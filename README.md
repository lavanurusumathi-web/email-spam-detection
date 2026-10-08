\# 📧 SmartMail — AI-Powered Email Management \& Spam Detection



> \*\*SmartMail\*\* is an AI-powered email management application that combines Gmail integration, Machine Learning-based spam detection, and an AI Customer Care assistant into a single, user-friendly platform.



\## 🌐 Application Links



\### 💻 Local Application



Run SmartMail locally using Streamlit:



```bash

streamlit run app.py

```



Then open:



\*\*http://localhost:8501\*\*



\### 🌍 Live Application



\*\*Live Demo:\*\* `YOUR\_GLOBAL\_LINK\_HERE`



> The live URL will be added after deployment.



\### 🐙 Source Code



\*\*GitHub:\*\*

https://github.com/lavanurusumathi-web/email-spam-detection



\---



\## 📌 Overview



SmartMail is designed to make email management smarter and more efficient.



The application connects to a user's Gmail account and provides common email management features while automatically analyzing messages using a Machine Learning model to identify potentially unwanted or spam emails.



It also includes an AI-powered Customer Care chatbot that can assist users directly inside the application.



\### Core Components



\* \*\*Gmail Integration\*\* — Read, send, reply to, forward, star, and manage emails.

\* \*\*Spam Detection\*\* — Automatically classify emails as spam or safe.

\* \*\*AI Customer Care\*\* — Conversational assistant powered by Ollama and Llama 3.2.

\* \*\*Dashboard\*\* — View email statistics and spam analysis.

\* \*\*Streamlit Interface\*\* — Simple and interactive web-based UI.



\---



\## ✨ Features



\### 📧 Gmail Email Management



\* View Inbox

\* View Sent emails

\* View Starred emails

\* View Gmail Spam

\* View Trash

\* Search emails

\* Read complete email content

\* Send emails

\* Reply to emails

\* Forward emails

\* Star / Unstar emails

\* Move emails to Trash



\### 🧠 Intelligent Spam Detection



SmartMail uses Machine Learning to analyze email content and classify messages as:



\* 🟢 \*\*Safe\*\*

\* 🔴 \*\*Spam\*\*



The application can automatically analyze incoming messages and display the prediction with a confidence score when available.



\### 🤖 AI Customer Care



SmartMail includes an AI Customer Care chatbot powered by:



\* \*\*Ollama\*\*

\* \*\*Llama 3.2\*\*



The chatbot provides an interactive conversational experience directly within the SmartMail application.



\### 📊 Dashboard \& Analytics



The dashboard provides useful information such as:



\* Total inbox emails

\* Sent emails

\* Starred emails

\* Gmail spam emails

\* Trash emails

\* AI-detected spam emails

\* Safe emails

\* Spam percentage



\---



\## 🧠 Machine Learning Pipeline



The spam detection system is trained using the \*\*SMS Spam Collection dataset\*\*.



The Machine Learning workflow is:



```text

Dataset

&#x20;  ↓

Data Preprocessing

&#x20;  ↓

Text Feature Extraction

&#x20;  ↓

TF-IDF Vectorization

&#x20;  ↓

Multinomial Naive Bayes

&#x20;  ↓

Spam / Safe Prediction

```



\### Model Components



\*\*Dataset:\*\* SMS Spam Collection



\*\*Feature Extraction:\*\* TF-IDF



\*\*Algorithm:\*\* Multinomial Naive Bayes



\*\*Output:\*\*



```text

Spam

Safe

```



The trained model and vectorizer are stored in:



```text

spam\_model.pkl

```



\---



\## 🏗️ Technology Stack



| Technology              | Purpose                   |

| ----------------------- | ------------------------- |

| Python                  | Application development   |

| Streamlit               | Web application interface |

| Pandas                  | Data processing           |

| Scikit-learn            | Machine Learning          |

| TF-IDF                  | Text feature extraction   |

| Multinomial Naive Bayes | Spam classification       |

| Gmail API               | Gmail integration         |

| Google OAuth 2.0        | Secure authentication     |

| Ollama                  | Local AI inference        |

| Llama 3.2               | AI Customer Care          |

| SQLite                  | Local application data    |



\---



\## 📂 Project Structure



```text

email-spam-detection/

│

├── app.py                 # Main Streamlit application

├── train\_model.py         # ML model training

├── spam\_model.pkl         # Trained spam detection model

├── chatbot.py             # AI chatbot

├── smartmail\_ai.py        # AI assistant functionality

├── database.py            # Database operations

├── gmail\_test.py          # Gmail API testing

├── SMSSpamCollection      # Training dataset

├── requirements.txt       # Python dependencies

├── .gitignore             # Ignored files

└── README.md              # Project documentation

```



\---



\## ⚙️ Installation \& Setup



\### 1. Clone the Repository



```bash

git clone https://github.com/lavanurusumathi-web/email-spam-detection.git

```



\### 2. Navigate to the Project



```bash

cd email-spam-detection

```



\### 3. Install Dependencies



```bash

pip install -r requirements.txt

```



\### 4. Configure Gmail API



To enable Gmail functionality:



1\. Create a project in Google Cloud.

2\. Enable the Gmail API.

3\. Configure Google OAuth.

4\. Create OAuth credentials.

5\. Place the required credentials file in the project directory.

6\. Run SmartMail and complete the Google authentication process.



> \*\*Security:\*\* Never commit `credentials.json`, `token.json`, API keys, passwords, or other sensitive credentials to GitHub.



\### 5. Configure Ollama



Install Ollama and download the required model:



```bash

ollama pull llama3.2:3b

```



\### 6. Start SmartMail



```bash

streamlit run app.py

```



Open:



```text

http://localhost:8501

```



\---



\## 🔐 Security



SmartMail uses Google OAuth for Gmail authentication.



Sensitive authentication files are excluded from version control using `.gitignore`.



Examples of files that should remain private:



```text

credentials.json

token.json

\*.db

\*.sqlite

.streamlit/secrets.toml

```



\*\*Never upload secrets, OAuth credentials, access tokens, API keys, or passwords to a public repository.\*\*



\---



\## 🎯 Project Objectives



The main objectives of SmartMail are to:



\* Integrate Gmail functionality into a custom web application.

\* Apply Machine Learning to email spam detection.

\* Provide an intuitive email management interface.

\* Integrate a local Large Language Model for AI assistance.

\* Demonstrate practical usage of Python, Machine Learning, APIs, OAuth, and AI technologies.



\---



\## 🚀 Future Enhancements



Planned improvements include:



\* 🌍 Cloud deployment

\* 📱 Improved mobile responsiveness

\* ⚡ Real-time email updates

\* 🔔 Email notifications

\* 📈 Advanced email analytics

\* 🧠 Improved spam classification

\* 👥 Multi-user Gmail authentication

\* ☁️ Cloud database integration

\* 🔎 Advanced email search and filtering

\* 📊 More detailed ML performance metrics



\---



\## 📸 Application



SmartMail provides a centralized interface for:



```text

Gmail

&#x20; +

Machine Learning

&#x20; +

Artificial Intelligence

&#x20; +

Analytics

&#x20; =

SmartMail

```



\---



\## 👨‍💻 Author



\### Lavan



\*\*GitHub:\*\*

https://github.com/lavanurusumathi-web



\*\*Project Repository:\*\*

https://github.com/lavanurusumathi-web/email-spam-detection



\---



\## ⭐ Support



If you find this project interesting or useful, consider giving the repository a ⭐ on GitHub.



\---



\### 📄 License



This project is intended for educational and portfolio purposes.



