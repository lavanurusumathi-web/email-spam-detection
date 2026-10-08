import ollama

print("🤖 SmartMail AI Customer Care")
print("Type 'exit' to close.\n")

while True:
    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("AI: Bye bro! 👋")
        break

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "system",
                "content": """
You are SmartMail AI Customer Care.

You help users use the SmartMail email website.

You can explain:
- How to use the Inbox
- How to send emails
- How to connect Gmail
- How spam detection works
- How to search emails
- SmartMail features

Be friendly and simple.
Give short, easy-to-understand answers.
Do not claim that you can access private emails.
"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    print("AI:", response["message"]["content"])
    print()