import streamlit as st
import os
import re
import html
import base64
import pickle
import pandas as pd
import ollama

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="SmartMail AI",
    page_icon="📧",
    layout="wide"
)


# =========================================================
# GMAIL SCOPES
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
]


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "📊 Dashboard"

if "selected_email" not in st.session_state:
    st.session_state.selected_email = None

if "spam_results" not in st.session_state:
    st.session_state.spam_results = {}

if "manual_spam_results" not in st.session_state:
    st.session_state.manual_spam_results = {}


# =========================================================
# LOAD SPAM MODEL
# =========================================================

MODEL_FILE = "spam_model.pkl"

vectorizer = None
spam_model = None

try:
    with open(MODEL_FILE, "rb") as f:
        vectorizer, spam_model = pickle.load(f)
except Exception as e:
    vectorizer = None
    spam_model = None


# =========================================================
# GMAIL CONNECTION
# =========================================================

@st.cache_resource
def get_gmail_service():

    creds = None

    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file(
                "token.json",
                SCOPES
            )
        except Exception:
            creds = None

    # Refresh expired token
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        except Exception:
            creds = None

    # Login if credentials are missing
    if not creds or not creds.valid:

        if not os.path.exists("credentials.json"):
            st.error(
                "credentials.json not found. "
                "Place your Google OAuth credentials file in the project folder."
            )
            return None

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent"
            )

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        except Exception as e:
            st.error(f"Gmail authentication failed: {e}")
            return None

    try:
        service = build(
            "gmail",
            "v1",
            credentials=creds
        )

        return service

    except Exception as e:
        st.error(f"Could not connect to Gmail: {e}")
        return None


# =========================================================
# GMAIL EMAIL HELPERS
# =========================================================

def get_header(headers, name):

    for header in headers:

        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")

    return ""


def decode_base64(data):

    if not data:
        return ""

    try:
        return base64.urlsafe_b64decode(
            data.encode("UTF-8")
        ).decode(
            "UTF-8",
            errors="ignore"
        )

    except Exception:
        return ""


def get_email_body(payload):

    """
    Extract plain text email body recursively.
    """

    body = ""

    if not payload:
        return body

    mime_type = payload.get("mimeType", "")

    body_data = payload.get("body", {}).get("data")

    if body_data:

        decoded = decode_base64(body_data)

        if mime_type == "text/plain":
            return decoded

        if mime_type == "text/html":
            clean = re.sub(
                r"<[^>]+>",
                " ",
                decoded
            )

            return html.unescape(clean)

    for part in payload.get("parts", []):

        result = get_email_body(part)

        if result:
            body += "\n" + result

    return body.strip()


def get_email_html(payload):

    """
    Extract original HTML email content.
    """

    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")

    body_data = payload.get("body", {}).get("data")

    if mime_type == "text/html" and body_data:

        return decode_base64(body_data)

    for part in payload.get("parts", []):

        result = get_email_html(part)

        if result:
            return result

    return ""


# =========================================================
# CLEAN EMAIL HTML
# =========================================================

def prepare_email_html(email_html):

    if not email_html:
        return ""

    # Remove dangerous tags
    email_html = re.sub(
        r"<script.*?>.*?</script>",
        "",
        email_html,
        flags=re.IGNORECASE | re.DOTALL
    )

    email_html = re.sub(
        r"<iframe.*?>.*?</iframe>",
        "",
        email_html,
        flags=re.IGNORECASE | re.DOTALL
    )

    email_html = re.sub(
        r"<form.*?>.*?</form>",
        "",
        email_html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Remove inline JavaScript events
    email_html = re.sub(
        r"\son\w+\s*=\s*(['\"]).*?\1",
        "",
        email_html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Add basic styling
    full_html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <style>

            body {{
                font-family:
                    Arial,
                    Helvetica,
                    sans-serif;

                font-size: 16px;

                line-height: 1.6;

                padding: 25px;

                margin: 0;

                background: white;

                color: #222;

                word-wrap: break-word;

                overflow-wrap: break-word;
            }}

            img {{
                max-width: 100%;
                height: auto;
            }}

            table {{
                max-width: 100%;
                border-collapse: collapse;
            }}

            a {{
                word-break: break-word;
            }}

        </style>

    </head>

    <body>

        {email_html}

    </body>

    </html>
    """

    return full_html


def display_html_email(email_html):

    if not email_html:
        return False

    full_html = prepare_email_html(email_html)

    if not full_html:
        return False

    # NEW Streamlit API
    st.iframe(
        full_html,
        height=1200
    )

    return True


# =========================================================
# GET EMAIL
# =========================================================

def get_full_email(gmail, message_id):

    try:

        message = gmail.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        return message

    except Exception as e:

        st.error(f"Could not load email: {e}")

        return None


# =========================================================
# SEND EMAIL
# =========================================================

def send_email(
    gmail,
    recipient,
    subject,
    message,
    thread_id=None,
    extra_headers=None
):

    try:

        mime_message = MIMEText(
            message,
            "plain",
            "utf-8"
        )

        mime_message["to"] = recipient
        mime_message["subject"] = subject

        if extra_headers:

            for key, value in extra_headers.items():

                mime_message[key] = value

        raw_message = base64.urlsafe_b64encode(
            mime_message.as_bytes()
        ).decode()

        body = {
            "raw": raw_message
        }

        if thread_id:
            body["threadId"] = thread_id

        gmail.users().messages().send(
            userId="me",
            body=body
        ).execute()

        return True

    except Exception as e:

        st.error(f"Email sending failed: {e}")

        return False


# =========================================================
# SPAM DETECTION
# =========================================================

def detect_spam(subject, sender, body):

    if vectorizer is None or spam_model is None:

        return "unknown", 0.0

    text = (
        str(subject)
        + " "
        + str(sender)
        + " "
        + str(body)
    )

    try:

        transformed = vectorizer.transform([text])

        prediction = spam_model.predict(
            transformed
        )[0]

        result = "spam" if prediction == 1 else "safe"

        confidence = 0.0

        if hasattr(spam_model, "predict_proba"):

            probabilities = spam_model.predict_proba(
                transformed
            )[0]

            confidence = max(probabilities) * 100

        return result, confidence

    except Exception:

        return "unknown", 0.0


# =========================================================
# AUTOMATIC SPAM CHECK
# =========================================================

def automatic_spam_check(gmail, message_id):

    if message_id in st.session_state.spam_results:

        return st.session_state.spam_results[
            message_id
        ]

    message = get_full_email(
        gmail,
        message_id
    )

    if not message:

        return "unknown", 0.0

    payload = message.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    subject = get_header(
        headers,
        "Subject"
    )

    sender = get_header(
        headers,
        "From"
    )

    body = get_email_body(
        payload
    )

    result, confidence = detect_spam(
        subject,
        sender,
        body
    )

    st.session_state.spam_results[
        message_id
    ] = (
        result,
        confidence
    )

    return result, confidence


# =========================================================
# SPAM RESULT
# =========================================================

def show_full_width_spam_result(
    result,
    confidence,
    title="AI Spam Analysis"
):

    st.markdown("---")

    if result == "spam":

        st.error(
            f"🚨 **{title}: SPAM EMAIL**\n\n"
            f"AI confidence: **{confidence:.1f}%**"
        )

    elif result == "safe":

        st.success(
            f"✅ **{title}: LOOKS SAFE**\n\n"
            f"AI confidence: **{confidence:.1f}%**"
        )

    else:

        st.warning(
            f"⚠️ **{title}: Unable to analyze email**"
        )

    st.markdown("---")


# =========================================================
# STAR / UNSTAR
# =========================================================

def toggle_star(gmail, message_id, starred):

    try:

        if starred:

            gmail.users().messages().modify(
                userId="me",
                id=message_id,
                body={
                    "removeLabelIds": ["STARRED"]
                }
            ).execute()

        else:

            gmail.users().messages().modify(
                userId="me",
                id=message_id,
                body={
                    "addLabelIds": ["STARRED"]
                }
            ).execute()

        st.rerun()

    except Exception as e:

        st.error(f"Star action failed: {e}")


# =========================================================
# TRASH EMAIL
# =========================================================

def trash_email(gmail, message_id):

    try:

        gmail.users().messages().trash(
            userId="me",
            id=message_id
        ).execute()

        st.success("Email moved to Trash.")

        st.rerun()

    except Exception as e:

        st.error(f"Could not move email to Trash: {e}")


# =========================================================
# GET EMAIL LIST
# =========================================================

def get_messages(
    gmail,
    query="",
    max_results=20
):

    try:

        response = gmail.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        return response.get(
            "messages",
            []
        )

    except Exception as e:

        st.error(
            f"Could not retrieve emails: {e}"
        )

        return []


# =========================================================
# EMAIL DISPLAY
# =========================================================

def display_emails(
    gmail,
    messages,
    folder_name
):

    if not messages:

        st.info(
            f"No emails found in {folder_name}."
        )

        return

    for msg in messages:

        message_id = msg["id"]

        message = get_full_email(
            gmail,
            message_id
        )

        if not message:
            continue

        payload = message.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        subject = get_header(
            headers,
            "Subject"
        )

        sender = get_header(
            headers,
            "From"
        )

        recipient = get_header(
            headers,
            "To"
        )

        date = get_header(
            headers,
            "Date"
        )

        snippet = message.get(
            "snippet",
            ""
        )

        label_ids = message.get(
            "labelIds",
            []
        )

        starred = "STARRED" in label_ids

        if not subject:
            subject = "(No Subject)"

        # =================================================
        # EMAIL CARD
        # =================================================

        with st.expander(
            f"📧 {subject}"
        ):

            st.write(
                f"**From:** {sender}"
            )

            st.write(
                f"**To:** {recipient}"
            )

            st.write(
                f"**Date:** {date}"
            )

            if snippet:

                st.caption(
                    snippet
                )

            # Automatic spam check for Inbox
            if folder_name == "Inbox":

                result, confidence = automatic_spam_check(
                    gmail,
                    message_id
                )

                show_full_width_spam_result(
                    result,
                    confidence,
                    "SmartMail AI"
                )

            # =============================================
            # BUTTONS
            # =============================================

            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:

                if st.button(
                    "📖 Read",
                    key=f"read_{message_id}"
                ):

                    st.session_state.selected_email = (
                        message_id
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "↩️ Reply",
                    key=f"reply_{message_id}"
                ):

                    st.session_state.reply_to = (
                        message_id
                    )

                    st.rerun()

            with col3:

                if st.button(
                    "↪️ Forward",
                    key=f"forward_{message_id}"
                ):

                    st.session_state.forward_email = (
                        message_id
                    )

                    st.rerun()

            with col4:

                star_text = (
                    "☆ Star"
                    if not starred
                    else
                    "⭐ Unstar"
                )

                if st.button(
                    star_text,
                    key=f"star_{message_id}"
                ):

                    toggle_star(
                        gmail,
                        message_id,
                        starred
                    )

            with col5:

                if st.button(
                    "🧠 Check Spam",
                    key=f"check_{message_id}"
                ):

                    result, confidence = automatic_spam_check(
                        gmail,
                        message_id
                    )

                    st.session_state.manual_spam_results[
                        message_id
                    ] = (
                        result,
                        confidence
                    )

                    st.rerun()

            with col6:

                if st.button(
                    "🗑️ Trash",
                    key=f"trash_{message_id}"
                ):

                    trash_email(
                        gmail,
                        message_id
                    )

            # =============================================
            # MANUAL SPAM RESULT
            # =============================================

            if message_id in st.session_state.manual_spam_results:

                result, confidence = (
                    st.session_state.manual_spam_results[
                        message_id
                    ]
                )

                show_full_width_spam_result(
                    result,
                    confidence,
                    "Manual Spam Check"
                )


# =========================================================
# FULL EMAIL READER
# =========================================================

def show_full_email(gmail, message_id):

    message = get_full_email(
        gmail,
        message_id
    )

    if not message:

        return

    payload = message.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    subject = get_header(
        headers,
        "Subject"
    )

    sender = get_header(
        headers,
        "From"
    )

    recipient = get_header(
        headers,
        "To"
    )

    date = get_header(
        headers,
        "Date"
    )

    thread_id = message.get(
        "threadId"
    )

    st.button(
        "⬅️ Back to Inbox",
        key="back_from_email",
        on_click=lambda: (
            st.session_state.update(
                selected_email=None
            )
        )
    )

    st.title(
        f"📧 {subject or '(No Subject)'}"
    )

    st.write(
        f"**From:** {sender}"
    )

    st.write(
        f"**To:** {recipient}"
    )

    st.write(
        f"**Date:** {date}"
    )

    # =============================================
    # SPAM ANALYSIS
    # =============================================

    result, confidence = automatic_spam_check(
        gmail,
        message_id
    )

    show_full_width_spam_result(
        result,
        confidence,
        "SmartMail AI"
    )

    # =============================================
    # ACTION BUTTONS
    # =============================================

    col1, col2, col3, col4 = st.columns(4)

    label_ids = message.get(
        "labelIds",
        []
    )

    starred = "STARRED" in label_ids

    with col1:

        if st.button(
            "↩️ Reply",
            key="full_reply"
        ):

            st.session_state.reply_to = (
                message_id
            )

            st.rerun()

    with col2:

        if st.button(
            "↪️ Forward",
            key="full_forward"
        ):

            st.session_state.forward_email = (
                message_id
            )

            st.rerun()

    with col3:

        if st.button(
            "⭐ Star" if not starred else "☆ Unstar",
            key="full_star"
        ):

            toggle_star(
                gmail,
                message_id,
                starred
            )

    with col4:

        if st.button(
            "🗑️ Trash",
            key="full_trash"
        ):

            trash_email(
                gmail,
                message_id
            )

    st.divider()

    # =============================================
    # EMAIL BODY
    # =============================================

    email_html = get_email_html(
        payload
    )

    if email_html:

        display_html_email(
            email_html
        )

    else:

        plain_text = get_email_body(
            payload
        )

        st.markdown(
            f"""
            <div style="
                padding:25px;
                border:1px solid #ddd;
                border-radius:10px;
                white-space:pre-wrap;
                font-size:16px;
            ">
            {html.escape(plain_text)}
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# REPLY EMAIL
# =========================================================

def show_reply_form(gmail, message_id):

    message = get_full_email(
        gmail,
        message_id
    )

    if not message:
        return

    payload = message.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    sender = get_header(
        headers,
        "From"
    )

    subject = get_header(
        headers,
        "Subject"
    )

    message_id_header = get_header(
        headers,
        "Message-ID"
    )

    references = get_header(
        headers,
        "References"
    )

    if not subject.lower().startswith("re:"):

        subject = "Re: " + subject

    st.subheader(
        "↩️ Reply to Email"
    )

    st.write(
        f"**To:** {sender}"
    )

    reply_text = st.text_area(
        "Message",
        height=250,
        key=f"reply_text_{message_id}"
    )

    if st.button(
        "📤 Send Reply",
        key=f"send_reply_{message_id}"
    ):

        extra_headers = {
            "In-Reply-To": message_id_header
        }

        if references:

            extra_headers["References"] = (
                references
                + " "
                + message_id_header
            )

        else:

            extra_headers["References"] = (
                message_id_header
            )

        if reply_text.strip():

            success = send_email(
                gmail,
                sender,
                subject,
                reply_text,
                thread_id=message.get("threadId"),
                extra_headers=extra_headers
            )

            if success:

                st.success(
                    "Reply sent successfully! ✅"
                )

                st.session_state.reply_to = None

                st.rerun()


# =========================================================
# FORWARD EMAIL
# =========================================================

def show_forward_form(gmail, message_id):

    message = get_full_email(
        gmail,
        message_id
    )

    if not message:
        return

    payload = message.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    subject = get_header(
        headers,
        "Subject"
    )

    sender = get_header(
        headers,
        "From"
    )

    date = get_header(
        headers,
        "Date"
    )

    body = get_email_body(
        payload
    )

    if not subject.lower().startswith("fwd:"):

        subject = "Fwd: " + subject

    st.subheader(
        "↪️ Forward Email"
    )

    recipient = st.text_input(
        "Forward to",
        key=f"forward_recipient_{message_id}"
    )

    message_text = st.text_area(
        "Message",
        height=200,
        key=f"forward_message_{message_id}"
    )

    forwarded_content = f"""

---------- Forwarded message ----------

From: {sender}
Date: {date}
Subject: {subject}

{body}

----------------------------------------
"""

    if st.button(
        "📤 Forward Email",
        key=f"send_forward_{message_id}"
    ):

        if not recipient.strip():

            st.warning(
                "Please enter recipient email."
            )

        else:

            final_message = (
                message_text
                + "\n"
                + forwarded_content
            )

            success = send_email(
                gmail,
                recipient,
                subject,
                final_message
            )

            if success:

                st.success(
                    "Email forwarded successfully! ✅"
                )

                st.session_state.forward_email = None

                st.rerun()


# =========================================================
# COMPOSE EMAIL
# =========================================================

def compose_email(gmail):

    st.title(
        "✉️ Compose Email"
    )

    recipient = st.text_input(
        "To"
    )

    subject = st.text_input(
        "Subject"
    )

    message = st.text_area(
        "Message",
        height=300
    )

    if st.button(
        "📤 Send Email",
        type="primary"
    ):

        if not recipient:

            st.warning(
                "Please enter recipient email."
            )

        elif not message:

            st.warning(
                "Please enter message."
            )

        else:

            success = send_email(
                gmail,
                recipient,
                subject,
                message
            )

            if success:

                st.success(
                    "Email sent successfully! 🎉"
                )


# =========================================================
# DASHBOARD
# =========================================================

def dashboard(gmail):

    st.title(
        "📊 SmartMail AI Dashboard"
    )

    st.write(
        "Welcome to your AI-powered Gmail assistant."
    )

    inbox = get_messages(
        gmail,
        "in:inbox",
        20
    )

    sent = get_messages(
        gmail,
        "in:sent",
        20
    )

    starred = get_messages(
        gmail,
        "is:starred",
        20
    )

    spam = get_messages(
        gmail,
        "in:spam",
        20
    )

    trash = get_messages(
        gmail,
        "in:trash",
        20
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "📥 Inbox",
            len(inbox)
        )

    with col2:

        st.metric(
            "📤 Sent",
            len(sent)
        )

    with col3:

        st.metric(
            "⭐ Starred",
            len(starred)
        )

    with col4:

        st.metric(
            "🚫 Spam",
            len(spam)
        )

    with col5:

        st.metric(
            "🗑️ Trash",
            len(trash)
        )

    st.divider()

    st.subheader(
        "🧠 SmartMail AI Analysis"
    )

    if st.button(
        "🧠 Analyze Latest Inbox"
    ):

        spam_count = 0
        safe_count = 0

        progress = st.progress(0)

        total = min(
            len(inbox),
            20
        )

        for index, msg in enumerate(inbox[:20]):

            result, confidence = automatic_spam_check(
                gmail,
                msg["id"]
            )

            if result == "spam":

                spam_count += 1

            elif result == "safe":

                safe_count += 1

            if total > 0:

                progress.progress(
                    (index + 1) / total
                )

        progress.empty()

        total_analyzed = (
            spam_count
            + safe_count
        )

        if total_analyzed:

            spam_percentage = (
                spam_count
                / total_analyzed
                * 100
            )

            st.metric(
                "🚨 Spam Percentage",
                f"{spam_percentage:.1f}%"
            )

            chart_data = pd.DataFrame(
                {
                    "Type": [
                        "Spam",
                        "Safe"
                    ],
                    "Emails": [
                        spam_count,
                        safe_count
                    ]
                }
            )

            st.bar_chart(
                chart_data.set_index("Type")
            )


# =========================================================
# SPAM DETECTOR PAGE
# =========================================================

def spam_detector():

    st.title(
        "🧠 SmartMail Spam Detector"
    )

    st.write(
        "Paste an email below and let the ML model check it."
    )

    subject = st.text_input(
        "Email Subject"
    )

    sender = st.text_input(
        "Sender Email"
    )

    body = st.text_area(
        "Email Content",
        height=300
    )

    if st.button(
        "🔍 Detect Spam",
        type="primary"
    ):

        if not body.strip():

            st.warning(
                "Please enter email content."
            )

        else:

            result, confidence = detect_spam(
                subject,
                sender,
                body
            )

            show_full_width_spam_result(
                result,
                confidence,
                "Spam Detector"
            )


# =========================================================
# AI CUSTOMER CARE
# =========================================================

def ai_customer_care():

    st.title(
        "🤖 SmartMail AI Customer Care"
    )

    st.write(
        "Ask me anything about SmartMail."
    )

    if "chat_messages" not in st.session_state:

        st.session_state.chat_messages = []

    for message in st.session_state.chat_messages:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    user_message = st.chat_input(
        "Type your question..."
    )

    if user_message:

        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        with st.chat_message("user"):

            st.write(
                user_message
            )

        try:

            response = ollama.chat(
                model="llama3.2:3b",
                messages=[
                    {
                        "role": "system",
                        "content": """
You are SmartMail AI Customer Care.

Help users with:
- Gmail
- SmartMail
- Spam detection
- Sending emails
- Reading emails
- Starred emails
- Trash
- AI features
- Basic troubleshooting

Give simple beginner-friendly answers.
"""
                    },
                    *st.session_state.chat_messages
                ]
            )

            assistant_message = (
                response["message"]["content"]
            )

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message
                }
            )

            with st.chat_message(
                "assistant"
            ):

                st.write(
                    assistant_message
                )

        except Exception as e:

            st.error(
                "Ollama could not respond.\n\n"
                f"Error: {e}"
            )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title(
        "📧 SmartMail AI"
    )

    st.caption(
        "AI-Powered Gmail Assistant"
    )

    st.divider()

    if st.button(
        "📊 Dashboard",
        use_container_width=True
    ):

        st.session_state.page = "📊 Dashboard"
        st.session_state.selected_email = None
        st.rerun()

    if st.button(
        "📧 Inbox",
        use_container_width=True
    ):

        st.session_state.page = "📧 Inbox"
        st.session_state.selected_email = None
        st.rerun()

    if st.button(
        "⭐ Starred",
        use_container_width=True
    ):

        st.session_state.page = "⭐ Starred"
        st.session_state.selected_email = None
        st.rerun()

    if st.button(
        "📤 Sent",
        use_container_width=True
    ):

        st.session_state.page = "📤 Sent"
        st.session_state.selected_email = None
        st.rerun()

    if st.button(
        "🚫 Spam",
        use_container_width=True
    ):

        st.session_state.page = "🚫 Spam"
        st.session_state.selected_email = None
        st.rerun()

    if st.button(
        "🗑️ Trash",
        use_container_width=True
    ):

        st.session_state.page = "🗑️ Trash"
        st.session_state.selected_email = None
        st.rerun()

    st.divider()

    if st.button(
        "✉️ Compose Email",
        use_container_width=True
    ):

        st.session_state.page = "✉️ Compose Email"
        st.session_state.selected_email = None
        st.rerun()

    if st.button(
        "🧠 Spam Detector",
        use_container_width=True
    ):

        st.session_state.page = "🧠 Spam Detector"
        st.session_state.selected_email = None
        st.rerun()

    if st.button(
        "🤖 AI Customer Care",
        use_container_width=True
    ):

        st.session_state.page = "🤖 AI Customer Care"
        st.session_state.selected_email = None
        st.rerun()

    st.divider()

    st.caption(
        "SmartMail AI • Gmail + Machine Learning + Ollama"
    )


# =========================================================
# CONNECT TO GMAIL
# =========================================================

gmail = get_gmail_service()

if gmail is None:

    st.stop()


# =========================================================
# FULL EMAIL READER
# =========================================================

if st.session_state.selected_email:

    show_full_email(
        gmail,
        st.session_state.selected_email
    )

    # Reply
    if st.session_state.get("reply_to"):

        st.divider()

        show_reply_form(
            gmail,
            st.session_state.reply_to
        )

    # Forward
    if st.session_state.get("forward_email"):

        st.divider()

        show_forward_form(
            gmail,
            st.session_state.forward_email
        )


# =========================================================
# NORMAL PAGES
# =========================================================

else:

    current_page = st.session_state.page

    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    if current_page == "📊 Dashboard":

        dashboard(gmail)

    # -----------------------------------------------------
    # INBOX
    # -----------------------------------------------------

    elif current_page == "📧 Inbox":

        st.title(
            "📧 Inbox"
        )

        search = st.text_input(
            "🔍 Search emails",
            placeholder="Search Gmail..."
        )

        col1, col2 = st.columns([6, 1])

        with col2:

            if st.button(
                "🔄 Refresh"
            ):

                st.session_state.spam_results = {}
                st.session_state.manual_spam_results = {}

                st.rerun()

        query = "in:inbox"

        if search.strip():

            query += f" {search}"

        messages = get_messages(
            gmail,
            query,
            20
        )

        display_emails(
            gmail,
            messages,
            "Inbox"
        )

    # -----------------------------------------------------
    # STARRED
    # -----------------------------------------------------

    elif current_page == "⭐ Starred":

        st.title(
            "⭐ Starred Emails"
        )

        messages = get_messages(
            gmail,
            "is:starred",
            20
        )

        display_emails(
            gmail,
            messages,
            "Starred"
        )

    # -----------------------------------------------------
    # SENT
    # -----------------------------------------------------

    elif current_page == "📤 Sent":

        st.title(
            "📤 Sent Emails"
        )

        messages = get_messages(
            gmail,
            "in:sent",
            20
        )

        display_emails(
            gmail,
            messages,
            "Sent"
        )

    # -----------------------------------------------------
    # SPAM
    # -----------------------------------------------------

    elif current_page == "🚫 Spam":

        st.title(
            "🚫 Gmail Spam"
        )

        messages = get_messages(
            gmail,
            "in:spam",
            20
        )

        display_emails(
            gmail,
            messages,
            "Spam"
        )

    # -----------------------------------------------------
    # TRASH
    # -----------------------------------------------------

    elif current_page == "🗑️ Trash":

        st.title(
            "🗑️ Trash"
        )

        messages = get_messages(
            gmail,
            "in:trash",
            20
        )

        display_emails(
            gmail,
            messages,
            "Trash"
        )

    # -----------------------------------------------------
    # COMPOSE
    # -----------------------------------------------------

    elif current_page == "✉️ Compose Email":

        compose_email(
            gmail
        )

    # -----------------------------------------------------
    # SPAM DETECTOR
    # -----------------------------------------------------

    elif current_page == "🧠 Spam Detector":

        spam_detector()

    # -----------------------------------------------------
    # AI CUSTOMER CARE
    # -----------------------------------------------------

    elif current_page == "🤖 AI Customer Care":

        ai_customer_care()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <br><br>
    <hr>

    <center>

    <small>
    📧 SmartMail AI |
    Gmail Integration |
    Machine Learning |
    Ollama AI
    </small>

    </center>
    """,
    unsafe_allow_html=True
)