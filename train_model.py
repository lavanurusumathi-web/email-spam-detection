import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report


print("Loading dataset...")


# 1. Read the SMS Spam Collection dataset
data = pd.read_csv(
    "SMSSpamCollection",
    sep="\t",
    header=None,
    names=["label", "message"]
)


# 2. Display dataset information
print("Dataset loaded successfully!")
print("Total messages:", len(data))


# 3. Convert labels into numbers
# ham = 0
# spam = 1

data["label"] = data["label"].map({
    "ham": 0,
    "spam": 1
})


# 4. Separate messages and labels

X = data["message"]
y = data["label"]


# 5. Split dataset into training and testing

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


print("Training messages:", len(X_train))
print("Testing messages:", len(X_test))


# 6. Convert text into numbers using TF-IDF

vectorizer = TfidfVectorizer()

X_train = vectorizer.fit_transform(X_train)

X_test = vectorizer.transform(X_test)


# 7. Create the Machine Learning model

model = MultinomialNB()


# 8. Train the model

print("Training model...")

model.fit(X_train, y_train)

print("Training completed!")


# 9. Test the model

y_pred = model.predict(X_test)


# 10. Calculate accuracy

accuracy = accuracy_score(
    y_test,
    y_pred
)


print()
print("==============================")
print("MODEL RESULTS")
print("==============================")

print("Accuracy:", accuracy)

print()
print("Classification Report:")

print(
    classification_report(
        y_test,
        y_pred
    )
)


# 11. Save the trained model

with open(
    "spam_model.pkl",
    "wb"
) as file:

    pickle.dump(
        (vectorizer, model),
        file
    )


print("==============================")
print("Model saved successfully!")
print("File: spam_model.pkl")
print("==============================")