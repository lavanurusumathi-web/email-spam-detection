import os
import re
import html
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd
import streamlit as st

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SmartMail AI",
    page_icon="📧",
    layout="wide"
)

# ============================================================
# CONSTANTS
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
]

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
MODEL_FILE = "spam_model.pkl"

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.block-container {
    padding-top: 1.5rem;
}

.smartmail-title {
    font-size: 34px;
    font-weight: 700;
    margin-bottom: 0;
}

.smartmail-subtitle {
    color: #667085;
    font-size: 16px;
}

.email-card {
    padding: 18px;
    border-radius: 14px;
    background: white;
    border: 1px solid #e5e7eb;
    margin-bottom: 10px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #e5e7eb;
    text-align: center;
}

.small-text {
    color: #667085;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Dashboard",
    "selected_email": None,
    "gmail": None,
    "spam_results": {},
    "email_cache": {},
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# GMAIL CONNECTION
# ============================================================

def get_gmail_service():

    try:

        creds = None

        if os.path.exists(TOKEN_FILE):

            creds = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )

        # Refresh token
        if creds and creds.expired and creds.refresh_token:

            try:

                creds.refresh(Request())

                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())

            except Exception:

                creds = None

        # New authentication
        if not creds or not creds.valid:

            if not os.path.exists(CREDENTIALS_FILE):

                st.error(
                    "credentials.json was not found in the project folder."
                )

                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent"
            )

            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        # IMPORTANT:
        # cache_discovery=False avoids unnecessary discovery-cache
        # problems and keeps the Gmail API connection clean.

        gmail = build(
            "gmail",
            "v1",
            credentials=creds,
            cache_discovery=False
        )

        # Verify connection
        gmail.users().getProfile(
            userId="me"
        ).execute()

        return gmail

    except Exception as e:

        st.error(
            f"Could not connect to Gmail: {e}"
        )

        return None


# ============================================================
# GET MESSAGES
# ============================================================

def get_messages(gmail, query="", max_results=20):

    try:

        response = gmail.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        return response.get("messages", [])

    except Exception as e:

        st.error(
            f"Could not retrieve emails: {e}"
        )

        return []


# ============================================================
# GET EMAIL
# ============================================================

def get_message(gmail, message_id):

    if message_id in st.session_state.email_cache:

        return st.session_state.email_cache[message_id]

    try:

        message = gmail.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        st.session_state.email_cache[message_id] = message

        return message

    except Exception as e:

        st.error(
            f"Could not open email: {e}"
        )

        return None


# ============================================================
# HEADER EXTRACTION
# ============================================================

def get_header(message, name):

    headers = (
        message
        .get("payload", {})
        .get("headers", [])
    )

    for header in headers:

        if header.get("name", "").lower() == name.lower():

            return header.get("value", "")

    return ""


# ============================================================
# EMAIL BODY
# ============================================================

def decode_body(data):

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

    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")

    body_data = (
        payload
        .get("body", {})
        .get("data")
    )

    if body_data:

        decoded = decode_body(body_data)

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
            return result

    return ""


def get_html_body(payload):

    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")

    body_data = (
        payload
        .get("body", {})
        .get("data")
    )

    if body_data and mime_type == "text/html":

        return decode_body(body_data)

    for part in payload.get("parts", []):

        result = get_html_body(part)

        if result:
            return result

    return ""


# ============================================================
# SPAM MODEL
# ============================================================

@st.cache_resource
def load_spam_model():

    if not os.path.exists(MODEL_FILE):

        return None, None

    try:

        with open(MODEL_FILE, "rb") as file:

            vectorizer, model = pickle.load(file)

        return vectorizer, model

    except Exception as e:

        st.error(
            f"Could not load spam model: {e}"
        )

        return None, None


def detect_spam(subject, sender, body):

    vectorizer, model = load_spam_model()

    if vectorizer is None or model is None:

        return "unknown", 0.0

    text = f"{subject} {sender} {body}"

    try:

        transformed = vectorizer.transform([text])

        prediction = model.predict(transformed)[0]

        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(
                transformed
            )[0]

            confidence = max(probabilities) * 100

        else:

            confidence = 100.0

        if int(prediction) == 1:

            return "spam", confidence

        return "safe", confidence

    except Exception:

        return "unknown", 0.0


# ============================================================
# EMAIL SPAM CHECK
# ============================================================

def analyze_email(gmail, message_id):

    message = get_message(
        gmail,
        message_id
    )

    if not message:

        return "unknown", 0

    subject = get_header(
        message,
        "Subject"
    )

    sender = get_header(
        message,
        "From"
    )

    body = get_email_body(
        message.get("payload", {})
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


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    gmail,
    recipient,
    subject,
    message,
    thread_id=None
):

    try:

        email_message = MIMEText(
            message,
            "plain"
        )

        email_message["to"] = recipient
        email_message["subject"] = subject

        raw = base64.urlsafe_b64encode(
            email_message.as_bytes()
        ).decode()

        body = {
            "raw": raw
        }

        if thread_id:
            body["threadId"] = thread_id

        gmail.users().messages().send(
            userId="me",
            body=body
        ).execute()

        return True

    except Exception as e:

        st.error(
            f"Could not send email: {e}"
        )

        return False


# ============================================================
# STAR / TRASH
# ============================================================

def star_email(gmail, message_id):

    try:

        gmail.users().messages().modify(
            userId="me",
            id=message_id,
            body={
                "addLabelIds": ["STARRED"]
            }
        ).execute()

        return True

    except Exception as e:

        st.error(str(e))

        return False


def unstar_email(gmail, message_id):

    try:

        gmail.users().messages().modify(
            userId="me",
            id=message_id,
            body={
                "removeLabelIds": ["STARRED"]
            }
        ).execute()

        return True

    except Exception as e:

        st.error(str(e))

        return False


def trash_email(gmail, message_id):

    try:

        gmail.users().messages().trash(
            userId="me",
            id=message_id
        ).execute()

        return True

    except Exception as e:

        st.error(str(e))

        return False


# ============================================================
# SPAM RESULT UI
# ============================================================

def show_spam_result(result, confidence):

    if result == "spam":

        st.error(
            f"🚨 SPAM EMAIL\n\n"
            f"AI Confidence: {confidence:.2f}%"
        )

    elif result == "safe":

        st.success(
            f"✅ SAFE EMAIL\n\n"
            f"AI Confidence: {confidence:.2f}%"
        )


# ============================================================
# EMAIL READER
# ============================================================

def show_email(gmail, message_id):

    message = get_message(
        gmail,
        message_id
    )

    if not message:
        return

    subject = get_header(
        message,
        "Subject"
    )

    sender = get_header(
        message,
        "From"
    )

    recipient = get_header(
        message,
        "To"
    )

    date = get_header(
        message,
        "Date"
    )

    st.button(
        "⬅️ Back to Inbox",
        on_click=lambda: st.session_state.update(
            {"selected_email": None}
        )
    )

    st.markdown(
        f"# {subject or '(No Subject)'}"
    )

    st.write(f"**From:** {sender}")
    st.write(f"**To:** {recipient}")
    st.write(f"**Date:** {date}")

    st.divider()

    # AI spam analysis
    if st.button(
        "🧠 Check Spam",
        key=f"reader_spam_{message_id}"
    ):

        result, confidence = analyze_email(
            gmail,
            message_id
        )

        show_spam_result(
            result,
            confidence
        )

    if message_id in st.session_state.spam_results:

        result, confidence = (
            st.session_state.spam_results[
                message_id
            ]
        )

        show_spam_result(
            result,
            confidence
        )

    # Buttons
    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "⭐ Star",
            key=f"reader_star_{message_id}"
        ):

            star_email(
                gmail,
                message_id
            )

            st.rerun()

    with col2:

        if st.button(
            "🗑️ Trash",
            key=f"reader_trash_{message_id}"
        ):

            trash_email(
                gmail,
                message_id
            )

            st.session_state.selected_email = None

            st.rerun()

    with col3:

        if st.button(
            "↩️ Reply",
            key=f"reader_reply_{message_id}"
        ):

            st.session_state.reply_email = message_id

    st.divider()

    # Display HTML email
    html_body = get_html_body(
        message.get("payload", {})
    )

    if html_body:

        safe_html = re.sub(
            r"<script.*?>.*?</script>",
            "",
            html_body,
            flags=re.DOTALL | re.IGNORECASE
        )

        safe_html = re.sub(
            r"<iframe.*?>.*?</iframe>",
            "",
            safe_html,
            flags=re.DOTALL | re.IGNORECASE
        )

        st.components.v1.html(
            safe_html,
            height=700,
            scrolling=True
        )

    else:

        body = get_email_body(
            message.get("payload", {})
        )

        st.text_area(
            "Email Content",
            body,
            height=500
        )


# ============================================================
# EMAIL LIST
# ============================================================

def display_emails(
    gmail,
    messages,
    folder_name="Inbox"
):

    if not messages:

        st.info(
            f"No emails found in {folder_name}."
        )

        return

    for item in messages:

        message_id = item["id"]

        message = get_message(
            gmail,
            message_id
        )

        if not message:
            continue

        subject = get_header(
            message,
            "Subject"
        )

        sender = get_header(
            message,
            "From"
        )

        date = get_header(
            message,
            "Date"
        )

        labels = message.get(
            "labelIds",
            []
        )

        st.markdown(
            '<div class="email-card">',
            unsafe_allow_html=True
        )

        st.markdown(
            f"### 📧 {subject or '(No Subject)'}"
        )

        st.write(
            f"**From:** {sender}"
        )

        st.caption(date)

        # Automatic spam detection in inbox
        if folder_name == "Inbox":

            if message_id not in st.session_state.spam_results:

                result, confidence = analyze_email(
                    gmail,
                    message_id
                )

            else:

                result, confidence = (
                    st.session_state.spam_results[
                        message_id
                    ]
                )

            if result == "spam":

                st.warning(
                    f"🚨 AI detected this email as SPAM "
                    f"({confidence:.1f}% confidence)"
                )

            elif result == "safe":

                st.success(
                    f"✅ AI: Safe email "
                    f"({confidence:.1f}% confidence)"
                )

        col1, col2, col3, col4, col5 = st.columns(5)

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

            if "STARRED" in labels:

                if st.button(
                    "☆ Unstar",
                    key=f"unstar_{message_id}"
                ):

                    unstar_email(
                        gmail,
                        message_id
                    )

                    st.rerun()

            else:

                if st.button(
                    "⭐ Star",
                    key=f"star_{message_id}"
                ):

                    star_email(
                        gmail,
                        message_id
                    )

                    st.rerun()

        with col3:

            if st.button(
                "🧠 Check",
                key=f"check_{message_id}"
            ):

                result, confidence = analyze_email(
                    gmail,
                    message_id
                )

                show_spam_result(
                    result,
                    confidence
                )

        with col4:

            if st.button(
                "🗑️ Trash",
                key=f"trash_{message_id}"
            ):

                trash_email(
                    gmail,
                    message_id
                )

                st.rerun()

        with col5:

            if st.button(
                "↩️ Reply",
                key=f"reply_{message_id}"
            ):

                st.session_state.reply_email = (
                    message_id
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "# 📧 SmartMail"
    )

    st.caption(
        "AI-Powered Gmail Assistant"
    )

    st.divider()

    pages = [
        "📊 Dashboard",
        "📧 Inbox",
        "⭐ Starred",
        "📤 Sent",
        "🚫 Spam",
        "🗑️ Trash",
        "✉️ Compose Email",
        "🧠 Spam Detector",
        "🤖 AI Customer Care"
    ]

    for page in pages:

        if st.button(
            page,
            use_container_width=True
        ):

            st.session_state.page = page
            st.session_state.selected_email = None
            st.rerun()

# ============================================================
# GMAIL INITIALIZATION
# ============================================================

if st.session_state.gmail is None:

    st.session_state.gmail = get_gmail_service()

gmail = st.session_state.gmail

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="smartmail-title">📊 SmartMail AI Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="smartmail-subtitle">'
    'Welcome to your AI-powered Gmail assistant.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

# ============================================================
# CONNECTION CHECK
# ============================================================

if gmail is None:

    st.error(
        "Gmail is not connected."
    )

    st.stop()

# ============================================================
# SELECTED EMAIL
# ============================================================

if st.session_state.selected_email:

    show_email(
        gmail,
        st.session_state.selected_email
    )

    st.stop()

# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "📊 Dashboard":

    st.subheader("📊 Dashboard")

    inbox = get_messages(
        gmail,
        "in:inbox",
        100
    )

    starred = get_messages(
        gmail,
        "is:starred",
        100
    )

    sent = get_messages(
        gmail,
        "in:sent",
        100
    )

    spam = get_messages(
        gmail,
        "in:spam",
        100
    )

    trash = get_messages(
        gmail,
        "in:trash",
        100
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "📧 Inbox",
            len(inbox)
        )

    with c2:
        st.metric(
            "⭐ Starred",
            len(starred)
        )

    with c3:
        st.metric(
            "📤 Sent",
            len(sent)
        )

    with c4:
        st.metric(
            "🚫 Spam",
            len(spam)
        )

    with c5:
        st.metric(
            "🗑️ Trash",
            len(trash)
        )

    st.divider()

    st.subheader(
        "🧠 AI Spam Analysis"
    )

    if st.button(
        "🔍 Analyze Latest Inbox"
    ):

        spam_count = 0
        safe_count = 0

        for item in inbox[:20]:

            message_id = item["id"]

            result, confidence = analyze_email(
                gmail,
                message_id
            )

            if result == "spam":
                spam_count += 1

            elif result == "safe":
                safe_count += 1

        total = spam_count + safe_count

        if total:

            percentage = (
                spam_count / total
            ) * 100

            a, b, c = st.columns(3)

            with a:
                st.metric(
                    "🚨 Spam",
                    spam_count
                )

            with b:
                st.metric(
                    "✅ Safe",
                    safe_count
                )

            with c:
                st.metric(
                    "Spam %",
                    f"{percentage:.1f}%"
                )

            chart = pd.DataFrame(
                {
                    "Category": [
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
                chart.set_index("Category")
            )

# ============================================================
# INBOX
# ============================================================

elif st.session_state.page == "📧 Inbox":

    st.subheader("📧 Inbox")

    search = st.text_input(
        "🔎 Search emails",
        placeholder="Search Gmail..."
    )

    if st.button("🔄 Refresh Inbox"):

        st.session_state.email_cache = {}
        st.session_state.spam_results = {}

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

# ============================================================
# STARRED
# ============================================================

elif st.session_state.page == "⭐ Starred":

    st.subheader("⭐ Starred Emails")

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

# ============================================================
# SENT
# ============================================================

elif st.session_state.page == "📤 Sent":

    st.subheader("📤 Sent Emails")

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

# ============================================================
# SPAM
# ============================================================

elif st.session_state.page == "🚫 Spam":

    st.subheader("🚫 Gmail Spam")

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

# ============================================================
# TRASH
# ============================================================

elif st.session_state.page == "🗑️ Trash":

    st.subheader("🗑️ Trash")

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

# ============================================================
# COMPOSE
# ============================================================

elif st.session_state.page == "✉️ Compose Email":

    st.subheader("✉️ Compose Email")

    recipient = st.text_input(
        "To"
    )

    subject = st.text_input(
        "Subject"
    )

    message = st.text_area(
        "Message",
        height=250
    )

    if st.button(
        "📤 Send Email"
    ):

        if not recipient:

            st.warning(
                "Please enter recipient email."
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
                    "✅ Email sent successfully!"
                )

# ============================================================
# SPAM DETECTOR
# ============================================================

elif st.session_state.page == "🧠 Spam Detector":

    st.subheader(
        "🧠 AI Spam Email Detector"
    )

    subject = st.text_input(
        "Email Subject"
    )

    sender = st.text_input(
        "Sender Email"
    )

    body = st.text_area(
        "Email Content",
        height=250
    )

    if st.button(
        "🔍 Detect Spam"
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

            show_spam_result(
                result,
                confidence
            )

# ============================================================
# AI CUSTOMER CARE
# ============================================================

elif st.session_state.page == "🤖 AI Customer Care":

    st.subheader(
        "🤖 SmartMail AI Customer Care"
    )

    st.write(
        "Ask questions about SmartMail, spam detection, "
        "Gmail features, or email security."
    )

    prompt = st.text_area(
        "💬 Ask SmartMail AI",
        height=150,
        placeholder="Type your question..."
    )

    if st.button(
        "🤖 Ask AI"
    ):

        if not prompt.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            try:

                import ollama

                response = ollama.chat(
                    model="llama3.2:3b",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are SmartMail AI Customer Care. "
                                "Answer clearly and simply. "
                                "Help users understand Gmail, "
                                "SmartMail and spam detection."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                st.success(
                    "🤖 SmartMail AI"
                )

                st.write(
                    response["message"]["content"]
                )

            except Exception as e:

                st.error(
                    f"AI error: {e}"
                )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "📧 SmartMail AI • Gmail + Machine Learning + Ollama"
)