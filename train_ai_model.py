import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


# ============================================================
# TRAINING DATA
# 20 examples per category = 140 examples
# ============================================================

data = [

    # --------------------------------------------------------
    # ACADEMIC
    # --------------------------------------------------------
    ("I cannot register for my required course", "Academic"),
    ("My course registration is not working", "Academic"),
    ("I have a problem with my class schedule", "Academic"),
    ("The timetable for my course is incorrect", "Academic"),
    ("I need help changing my course enrollment", "Academic"),
    ("My examination schedule has not been published", "Academic"),
    ("There is an error in my exam timetable", "Academic"),
    ("I cannot access my examination information", "Academic"),
    ("My lecturer has not uploaded the assignment", "Academic"),
    ("The assignment deadline is unclear", "Academic"),
    ("I have a problem with my academic transcript", "Academic"),
    ("My grades have not been updated", "Academic"),
    ("My exam result is missing from the portal", "Academic"),
    ("I need help with my course result", "Academic"),
    ("The lecturer has changed the class time without notice", "Academic"),
    ("I cannot find my course materials", "Academic"),
    ("There is an issue with my attendance record", "Academic"),
    ("My attendance has been recorded incorrectly", "Academic"),
    ("I need information about my academic program", "Academic"),
    ("The university has not provided my class schedule", "Academic"),

    # --------------------------------------------------------
    # IT / NETWORK
    # --------------------------------------------------------
    ("The WiFi is not working in the computer lab", "IT / Network"),
    ("The internet connection keeps disconnecting", "IT / Network"),
    ("Campus WiFi is extremely slow", "IT / Network"),
    ("I cannot connect to the university WiFi", "IT / Network"),
    ("The network is unavailable in the library", "IT / Network"),
    ("The computer lab internet stopped working", "IT / Network"),
    ("My student portal is not loading", "IT / Network"),
    ("I cannot log into the student portal", "IT / Network"),
    ("The university website is down", "IT / Network"),
    ("The online portal keeps showing an error", "IT / Network"),
    ("My university email is not working", "IT / Network"),
    ("I cannot access my student email account", "IT / Network"),
    ("The classroom computer is not working", "IT / Network"),
    ("The printer connected to the lab computer is not working", "IT / Network"),
    ("The computer keeps restarting in the laboratory", "IT / Network"),
    ("The network connection is unstable", "IT / Network"),
    ("The internet is unavailable on campus", "IT / Network"),
    ("I cannot access the online learning system", "IT / Network"),
    ("The campus server is unavailable", "IT / Network"),
    ("The login system keeps rejecting my password", "IT / Network"),

    # --------------------------------------------------------
    # LIBRARY
    # --------------------------------------------------------
    ("I cannot find the book I need in the library", "Library"),
    ("The library does not have the required textbook", "Library"),
    ("I need help finding a book", "Library"),
    ("The library search system is not working", "Library"),
    ("I cannot renew my library books", "Library"),
    ("My library account is not working", "Library"),
    ("I was charged a library fine incorrectly", "Library"),
    ("The library fine on my account is incorrect", "Library"),
    ("I returned my book but it still shows as borrowed", "Library"),
    ("The library opening hours are inconvenient", "Library"),
    ("The library closes too early", "Library"),
    ("There are not enough study spaces in the library", "Library"),
    ("The library computers are unavailable", "Library"),
    ("I cannot access an online library journal", "Library"),
    ("A book I reserved has not arrived", "Library"),
    ("I have been waiting for my reserved book", "Library"),
    ("The library catalogue shows the wrong availability", "Library"),
    ("I need assistance with borrowing a book", "Library"),
    ("The library study room booking system has a problem", "Library"),
    ("The librarian helped me find the books I needed", "Library"),

    # --------------------------------------------------------
    # HOSTEL
    # --------------------------------------------------------
    ("There is a problem with my hostel room", "Hostel"),
    ("The hostel room is not clean", "Hostel"),
    ("The water supply in the hostel is not working", "Hostel"),
    ("There is no hot water in my hostel", "Hostel"),
    ("The hostel bathroom needs repair", "Hostel"),
    ("My hostel room has a broken fan", "Hostel"),
    ("The hostel electricity keeps going off", "Hostel"),
    ("There is a power problem in my hostel room", "Hostel"),
    ("The hostel room is too noisy", "Hostel"),
    ("Students are making too much noise in the hostel", "Hostel"),
    ("My hostel room has a leaking ceiling", "Hostel"),
    ("There is water leaking into my hostel room", "Hostel"),
    ("The hostel internet is not working", "Hostel"),
    ("I have not received my hostel room allocation", "Hostel"),
    ("There is an issue with hostel accommodation", "Hostel"),
    ("The hostel food is not satisfactory", "Hostel"),
    ("The hostel dining area is dirty", "Hostel"),
    ("The hostel security is a concern", "Hostel"),
    ("My hostel key is not working", "Hostel"),
    ("I need maintenance in my hostel room", "Hostel"),

    # --------------------------------------------------------
    # FACILITIES
    # --------------------------------------------------------
    ("The classroom projector is broken", "Facilities"),
    ("The classroom is too hot", "Facilities"),
    ("The classroom air conditioner is not working", "Facilities"),
    ("The classroom lights are not working", "Facilities"),
    ("The university building needs maintenance", "Facilities"),
    ("There is a broken chair in the classroom", "Facilities"),
    ("The classroom desks are damaged", "Facilities"),
    ("The canteen is too crowded", "Facilities"),
    ("The canteen does not have enough vegetarian options", "Facilities"),
    ("The canteen seating area is dirty", "Facilities"),
    ("The drinking water facility is not working", "Facilities"),
    ("The washroom needs cleaning", "Facilities"),
    ("The campus toilets are not clean", "Facilities"),
    ("There is a broken door in the classroom", "Facilities"),
    ("The elevator is not working", "Facilities"),
    ("The campus parking area needs improvement", "Facilities"),
    ("There is not enough lighting around campus", "Facilities"),
    ("The classroom windows are broken", "Facilities"),
    ("The campus facilities need improvement", "Facilities"),
    ("The rubbish bins around campus are overflowing", "Facilities"),

    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------
    ("I was charged my tuition fee twice", "Finance"),
    ("My tuition payment has been recorded incorrectly", "Finance"),
    ("I need a refund for my tuition payment", "Finance"),
    ("The university charged me the wrong amount", "Finance"),
    ("My fee payment is not showing in the system", "Finance"),
    ("I cannot see my tuition payment", "Finance"),
    ("There is an error in my student fee account", "Finance"),
    ("I was charged an incorrect amount for my semester fee", "Finance"),
    ("I need help with my university fee", "Finance"),
    ("My scholarship payment has not been received", "Finance"),
    ("There is a problem with my scholarship", "Finance"),
    ("My financial aid has not been processed", "Finance"),
    ("I was charged a late payment fee incorrectly", "Finance"),
    ("The invoice for my university fees is incorrect", "Finance"),
    ("I need a copy of my fee receipt", "Finance"),
    ("My payment receipt is missing", "Finance"),
    ("I paid my fees but the balance is still showing", "Finance"),
    ("The university has not processed my refund", "Finance"),
    ("There is a billing error on my account", "Finance"),
    ("I have a problem with my tuition bill", "Finance"),

    # --------------------------------------------------------
    # TRANSPORTATION
    # --------------------------------------------------------
    ("The morning campus bus is always late", "Transportation"),
    ("The university bus did not arrive", "Transportation"),
    ("The campus shuttle is frequently delayed", "Transportation"),
    ("The bus driver skipped my bus stop", "Transportation"),
    ("The university bus left before the scheduled time", "Transportation"),
    ("There are not enough campus buses", "Transportation"),
    ("The bus is too crowded in the morning", "Transportation"),
    ("The campus shuttle schedule is incorrect", "Transportation"),
    ("I cannot find the university bus timetable", "Transportation"),
    ("The bus route does not include my area", "Transportation"),
    ("The university shuttle route needs improvement", "Transportation"),
    ("The campus bus is unreliable", "Transportation"),
    ("The driver was late picking up students", "Transportation"),
    ("The bus did not stop at the designated stop", "Transportation"),
    ("The university transportation service is poor", "Transportation"),
    ("The evening bus is always delayed", "Transportation"),
    ("The campus shuttle broke down", "Transportation"),
    ("There is no bus available after class", "Transportation"),
    ("The bus timetable should be updated", "Transportation"),
    ("I have a complaint about the campus transport service", "Transportation"),
]


# ============================================================
# SEPARATE TEXT AND LABELS
# ============================================================

texts = [item[0] for item in data]
labels = [item[1] for item in data]


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    texts,
    labels,
    test_size=0.25,
    random_state=42,
    stratify=labels
)


# ============================================================
# MACHINE LEARNING PIPELINE
# ============================================================

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=2000,
            random_state=42
        )
    )
])


# ============================================================
# TRAIN MODEL
# ============================================================

print("=" * 70)
print("AI COMPLAINT CLASSIFICATION MODEL")
print("=" * 70)

print()
print("Total dataset samples :", len(data))
print("Training samples      :", len(X_train))
print("Testing samples       :", len(X_test))
print()

model.fit(X_train, y_train)


# ============================================================
# EVALUATION
# ============================================================

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("=" * 70)
print("MODEL EVALUATION")
print("=" * 70)

print()
print(f"Accuracy : {accuracy * 100:.2f}%")
print()

print("Classification Report:")
print()

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

model_directory = "models"

os.makedirs(model_directory, exist_ok=True)

model_path = os.path.join(
    model_directory,
    "complaint_classifier.joblib"
)

joblib.dump(model, model_path)


print("=" * 70)
print(f"Model saved to: {model_path}")
print("=" * 70)


# ============================================================
# SAMPLE PREDICTIONS
# ============================================================

sample_complaints = [
    "The WiFi in the computer lab keeps disconnecting",
    "The morning bus to campus is always late",
    "The librarian helped me find the books I needed",
    "I was charged my tuition fee twice",
    "The classroom projector is broken",
    "There is no hot water in my hostel",
    "I cannot register for my required course",
    "The weather has been sunny this week"
]


print()
print("=" * 70)
print("SAMPLE PREDICTIONS")
print("=" * 70)

for complaint in sample_complaints:

    prediction = model.predict([complaint])[0]

    probabilities = model.predict_proba([complaint])[0]

    confidence = max(probabilities) * 100

    print()
    print("Complaint :", complaint)
    print("Category  :", prediction)
    print(f"Confidence: {confidence:.2f}%")

print()
print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)
