\# 📧 SmartMail – AI-Powered Spam Email Detection



SmartMail is an AI-powered email management application that detects spam emails, connects with Gmail, and provides an AI Customer Care chatbot.



The application is built using \*\*Python, Streamlit, Machine Learning, Gmail API, and Ollama\*\*.



\## 🚀 Features



\* 📧 Gmail inbox integration

\* 🧠 AI-based spam email detection

\* 📊 Dashboard with email statistics

\* ⭐ Star and unstar emails

\* 🗑️ Move emails to trash

\* 📤 Send emails

\* ↩️ Reply to emails

\* ↪️ Forward emails

\* 🚫 View Gmail spam folder

\* 🤖 AI Customer Care chatbot

\* 🔍 Search emails

\* 📈 Spam/Safe email analysis



\## 🛠️ Technologies Used



\* \*\*Python\*\*

\* \*\*Streamlit\*\*

\* \*\*Pandas\*\*

\* \*\*Scikit-learn\*\*

\* \*\*TF-IDF Vectorization\*\*

\* \*\*Multinomial Naive Bayes\*\*

\* \*\*Gmail API\*\*

\* \*\*Google OAuth 2.0\*\*

\* \*\*Ollama\*\*

\* \*\*Llama 3.2\*\*

\* \*\*SQLite\*\*



\## 🧠 Machine Learning



The spam detection model is trained using the \*\*SMS Spam Collection dataset\*\*.



\### Machine Learning Process



```text

SMS Spam Dataset

&#x20;      ↓

Data Preprocessing

&#x20;      ↓

TF-IDF Vectorization

&#x20;      ↓

Multinomial Naive Bayes

&#x20;      ↓

Spam / Safe Prediction

```



The model classifies messages into:



\* 🟢 \*\*Safe\*\*

\* 🔴 \*\*Spam\*\*



The trained model is saved as:



```text

spam\_model.pkl

```



\## 📂 Project Structure



```text

email-spam-detection/

│

├── app.py

├── chatbot.py

├── database.py

├── gmail\_test.py

├── smartmail\_ai.py

├── train\_model.py

├── spam\_model.pkl

├── SMSSpamCollection

├── requirements.txt

├── .gitignore

└── README.md

```



> `credentials.json`, `token.json`, database files, and other sensitive/local files are intentionally excluded from GitHub.



\## ⚙️ Installation



\### 1. Clone the repository



```bash

git clone https://github.com/lavanurusumathi-web/email-spam-detection.git

```



\### 2. Open the project



```bash

cd email-spam-detection

```



\### 3. Install required packages



```bash

pip install -r requirements.txt

```



\## ▶️ Run SmartMail



Start the Streamlit application:



```bash

streamlit run app.py

```



The application will open in your browser at:



```text

http://localhost:8501

```



\## 📧 Gmail Setup



To use Gmail features:



1\. Create a project in Google Cloud Console.

2\. Enable the Gmail API.

3\. Configure Google OAuth.

4\. Create OAuth credentials.

5\. Download the credentials file as:



```text

credentials.json

```



6\. Place it inside the project folder.

7\. Run the application.

8\. Sign in with your Gmail account and authorize SmartMail.



\*\*Important:\*\* Never upload `credentials.json` or `token.json` to GitHub.



\## 🤖 AI Customer Care



SmartMail includes an AI Customer Care chatbot powered by \*\*Ollama\*\* and \*\*Llama 3.2\*\*.



Install Ollama and make sure the model is available:



```bash

ollama pull llama3.2:3b

```



The chatbot can then be used from the SmartMail application.



\## 📊 Dashboard



The SmartMail dashboard provides information such as:



\* Total inbox emails

\* Sent emails

\* Starred emails

\* Gmail spam emails

\* Trash emails

\* AI-detected spam emails

\* Safe emails

\* Spam percentage



\## 🔐 Security



Sensitive files are excluded using `.gitignore`.



The following files should \*\*never\*\* be uploaded to GitHub:



```text

credentials.json

token.json

.streamlit/secrets.toml

\*.db

\*.sqlite

```



\## 🎯 Project Objective



The main objective of SmartMail is to combine \*\*Machine Learning and AI with email management\*\* to create a smarter and more user-friendly email application.



\## 👩‍💻 Author



\*\*Lavan\*\*



GitHub:

https://github.com/lavanurusumathi-web



\## 📌 Future Improvements



\* 🌐 Deploy SmartMail online

\* 📱 Improve mobile responsiveness

\* 🧠 Improve spam detection accuracy

\* 📬 Real-time Gmail email updates

\* 🔔 Email notifications

\* 📈 Advanced email analytics

\* 👥 Multi-user Gmail authentication

\* ☁️ Cloud database integration



\---



⭐ If you find this project useful, consider giving the repository a star!



