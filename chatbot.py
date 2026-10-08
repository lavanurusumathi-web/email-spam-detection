from openai import OpenAI

client = OpenAI()

print("🤖 SmartMail AI Customer Care")
print("Type 'exit' to close the chatbot.\n")

while True:
    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("AI: Bye bro! 👋")
        break

    response = client.responses.create(
        model="gpt-5.6",
        input=[
            {
                "role": "developer",
                "content": (
                    "You are SmartMail AI Customer Care. "
                    "Help users understand and use the SmartMail website. "
                    "Explain Gmail connection, inbox, sending emails, "
                    "spam detection, searching emails, and SmartMail features. "
                    "Be friendly and simple."
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    print("AI:", response.output_text)
    print()