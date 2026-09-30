# utils/ai_engine.py
# ---------------------------------------------------------------
# Local AI / NLP engine for the Complaint Management System.
#
# It analyses the text of a complaint and returns:
#   category, sentiment, priority, confidence, summary, suggested response
#
# HOW IT WORKS (a simple "rule-based" approach):
#   Each result is decided by looking for keywords in the complaint text
#   and counting how many are found. This needs NO internet, NO API key
#   and NO training data, and every decision can be explained.
#
# HOW TO USE IT (later, from app.py):
#       from utils.ai_engine import analyze_complaint
#       result = analyze_complaint("The Wi-Fi in the library is down...")
#       print(result["category"], result["priority"])
#
# HOW TO TEST IT NOW (from the project folder):
#       python utils/ai_engine.py
#
# This file does not need any other file from the project.
# ---------------------------------------------------------------

import re  # "re" = regular expressions, used for matching whole words


# ===============================================================
# 1. KEYWORD LISTS  (edit these lists to tune the "AI")
# ===============================================================
# Every category has a list of words/phrases that suggest it.
# To improve accuracy later, just add more keywords to a list.
CATEGORY_KEYWORDS = {
    "Academic": [
        "exam", "grade", "mark", "lecturer", "lecture", "professor", "teacher",
        "course", "class", "assignment", "timetable", "syllabus", "result",
        "thesis", "supervisor", "tutor", "module", "semester", "attendance",
        "coursework", "curriculum", "academic", "tutorial", "coursework",
        "final year project",
    ],
    "IT / Network": [
        "wifi", "wi-fi", "internet", "network", "portal", "login", "password",
        "computer", "email", "server", "website", "software", "vpn", "moodle",
        "lms", "connection", "printer", "online", "account locked", "lab computer",
        "system down",
    ],
    "Library": [
        "library", "librarian", "book", "journal", "borrow", "reading room",
        "study room", "catalogue", "catalog", "e-book", "ebook", "research paper",
        "reference section",
    ],
    "Hostel": [
        "hostel", "dormitory", "dorm", "roommate", "room mate", "warden",
        "mess", "laundry", "accommodation", "hostel room", "hostel food",
        "bunk", "residence hall",
    ],
    "Facilities": [
        "toilet", "washroom", "restroom", "classroom", "air conditioning",
        "fan", "light", "electricity", "water", "cleaning", "broken", "chair",
        "desk", "parking", "canteen", "cafeteria", "playground", "gym", "lift",
        "elevator", "security", "leak", "projector", "maintenance", "drinking water",
        "power cut", "dirty",
    ],
    "Finance": [
        "fee", "tuition", "payment", "refund", "scholarship", "invoice", "bill",
        "financial aid", "bursar", "receipt", "loan", "overcharged", "charged",
        "late fee", "installment", "deposit", "account office",
    ],
    "Transportation": [
        "bus", "shuttle", "transport", "transportation", "driver", "route",
        "bus stop", "pickup", "pick-up", "vehicle", "commute", "bus schedule",
        "bus fare", "campus bus",
    ],
}

# Words that suggest the student is unhappy.
NEGATIVE_KEYWORDS = [
    "terrible", "awful", "horrible", "worst", "angry", "upset", "frustrated",
    "frustrating", "unacceptable", "disappointed", "disappointing", "disgusting",
    "useless", "unhappy", "unfair", "rude", "ignored", "poor", "bad", "broken",
    "late", "delay", "delayed", "slow", "dirty", "failed", "failure", "problem",
    "complain", "suffering", "waste", "overcharged", "fed up", "not working",
    "no response", "not good", "not helpful", "not happy", "not satisfied",
    "not great",
]

# Phrases that LOOK positive but actually mean the opposite (e.g. "not good").
# We remove them before counting positive words, so "not good" is not
# counted as the positive word "good".
NEGATED_POSITIVE_PHRASES = [
    "not good", "not helpful", "not happy", "not satisfied", "not great",
]

# Words that suggest the student is happy or thankful.
POSITIVE_KEYWORDS = [
    "thank", "grateful", "appreciate", "great", "good", "excellent", "helpful",
    "happy", "satisfied", "pleased", "wonderful", "well done", "improved",
    "fantastic",
]

# Words that suggest the problem is URGENT or a safety risk -> High priority.
HIGH_PRIORITY_KEYWORDS = [
    "urgent", "urgently", "emergency", "immediately", "asap", "danger",
    "dangerous", "unsafe", "safety", "harassment", "harassed", "threat",
    "threatened", "fire", "injury", "injured", "medical", "health", "theft",
    "stolen", "flood", "flooding", "electric shock", "deadline",
    "due tomorrow", "exam tomorrow", "cannot access", "can't access",
    "unable to access", "no water", "no electricity",
]

# Words that suggest a MINOR issue or a suggestion -> Low priority.
LOW_PRIORITY_KEYWORDS = [
    "suggest", "suggestion", "minor", "would be nice", "would be great",
    "feedback", "improve", "improvement", "request", "whenever possible",
    "no rush", "not urgent",
]

# Words that suggest the problem has lasted a long time or affects many people.
CONTEXT_KEYWORDS = [
    "days", "weeks", "months", "again", "still", "repeatedly", "every day",
    "many students", "everyone", "all students", "several times", "again and again",
]

# How long the university aims to take to reply, by priority.
# (Change these to match your institution's policy.)
RESPONSE_TIMEFRAME = {
    "High": "within 1 working day",
    "Medium": "within 3 working days",
    "Low": "within 5 working days",
}


# ===============================================================
# 2. SMALL HELPER FUNCTIONS
# ===============================================================
def clean_text(text):
    """Make text easy to search: lowercase, straight apostrophes, single spaces."""
    text = (text or "").lower().replace(
        "\u2019", "'")  # curly ' becomes straight '
    return " ".join(text.split())  # collapse extra spaces and new lines


def count_keyword_matches(text, keywords):
    """Count how many times the keywords appear in the text.

    - Whole words only: 'fan' must not match inside 'fantastic'.
    - Simple endings are allowed: 'book' also matches 'books' and 'booking'.
    - A multi-word phrase (e.g. 'not working') counts double, because it is
      stronger evidence than a single word."""
    total = 0
    for keyword in keywords:
        # \b means "word boundary". The (?:s|es|ed|ing)? part allows common endings.
        pattern = r"\b" + re.escape(keyword) + r"(?:s|es|ed|ing)?\b"
        matches = re.findall(pattern, text)
        weight = 2 if " " in keyword else 1
        total += weight * len(matches)
    return total


def remove_keyword_matches(text, keywords):
    """Return the text with all the given keywords/phrases blanked out."""
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword) + r"(?:s|es|ed|ing)?\b"
        text = re.sub(pattern, " ", text)
    return text


# ===============================================================
# 3. THE ANALYSIS STEPS
# ===============================================================
def classify_category(text):
    """Decide the complaint category. Returns (category, confidence 0-100).

    Method: score every category by counting its keywords in the text and
    pick the category with the highest score."""

    # Count keyword matches for each category, e.g. {"Library": 2, "IT / Network": 1, ...}
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = count_keyword_matches(text, keywords)

    # the category with the highest score
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    total_score = sum(scores.values())

    # No keyword matched at all -> we cannot tell, so use "Other" with low confidence.
    if best_score == 0:
        return "Other", 35.0

    # Confidence combines two ideas:
    #   share    = how much of ALL the matches belong to the winning category
    #              (1.0 means no other category matched at all)
    #   strength = how much evidence there is (3 or more matches = full strength)
    share = best_score / total_score
    strength = min(best_score, 3) / 3
    confidence = 100 * (0.3 + 0.7 * share * strength)
    confidence = min(confidence, 98.0)  # never claim 100% certainty

    return best_category, round(confidence, 1)


def analyze_sentiment(text):
    """Decide whether the complaint sounds Positive, Neutral or Negative."""

    negative_score = count_keyword_matches(text, NEGATIVE_KEYWORDS)

    # Remove phrases like "not good" first, so they are not counted as positive.
    text_for_positive = remove_keyword_matches(text, NEGATED_POSITIVE_PHRASES)
    positive_score = count_keyword_matches(
        text_for_positive, POSITIVE_KEYWORDS)

    if negative_score > positive_score:
        return "Negative"
    if positive_score > negative_score:
        return "Positive"
    return "Neutral"  # equal scores (including 0 and 0)


def recommend_priority(text, sentiment):
    """Recommend Low, Medium or High priority using simple rules."""

    high_hits = count_keyword_matches(text, HIGH_PRIORITY_KEYWORDS)
    low_hits = count_keyword_matches(text, LOW_PRIORITY_KEYWORDS)
    context_hits = count_keyword_matches(text, CONTEXT_KEYWORDS)
    negative_hits = count_keyword_matches(text, NEGATIVE_KEYWORDS)

    # Rule 1: any urgent / safety word means High priority.
    if high_hits >= 1:
        return "High"

    # Rule 2: very angry, or a long-running problem with a negative tone -> High.
    if sentiment == "Negative" and (negative_hits >= 3 or context_hits >= 2):
        return "High"

    # Rule 3: thankful messages and small suggestions are Low priority.
    if sentiment == "Positive":
        return "Low"
    if low_hits >= 1 and sentiment != "Negative" and context_hits == 0:
        return "Low"

    # Rule 4: everything else is Medium.
    return "Medium"


def generate_summary(title, description, category, sentiment, priority):
    """Create a short summary: a label plus the first sentence of the complaint."""

    text = " ".join((description or "").split())

    if not text:
        base = title.strip() if title else "No description provided."
    else:
        # Split into sentences after '.', '!' or '?'.
        sentences = re.split(r"(?<=[.!?])\s+", text)
        base = sentences[0]
        # If the first sentence is very short, add the second one for context.
        if len(base) < 60 and len(sentences) > 1:
            base = base + " " + sentences[1]

    # Keep the summary short: cut at ~140 characters on a word boundary.
    if len(base) > 140:
        base = base[:140].rsplit(" ", 1)[0] + "..."

    return f"{category} complaint ({sentiment.lower()} tone, {priority.lower()} priority): {base}"


def generate_suggested_response(category, sentiment, priority, student_name=None):
    """Write a professional reply that staff can review, edit and send.

    The reply is built from four parts:
      1. a greeting
      2. an opening sentence that matches the student's tone
      3. a paragraph that matches the category
      4. a sentence with the expected reply time (from the priority)"""

    # Part 1: greeting
    greeting = f"Dear {student_name}," if student_name else "Dear Student,"

    # Part 2: opening sentence, chosen by sentiment
    openings = {
        "Negative": "Thank you for contacting us. We are sorry for the inconvenience this has caused "
                    "and we understand your frustration.",
        "Neutral": "Thank you for bringing this matter to our attention.",
        "Positive": "Thank you for your kind message and for taking the time to share your feedback.",
    }
    opening = openings[sentiment]

    # Part 3: main paragraph, chosen by category
    bodies = {
        "Academic": "Your concern has been passed to the relevant academic department. "
                    "A member of the academic staff will review the matter and contact you with the next steps.",
        "IT / Network": "Our IT support team has been informed and will investigate the problem. "
                        "It would help if you could tell us your location and the device you were using.",
        "Library": "The library management team has been notified and will look into the matter. "
                   "We will update you once we have checked the resources or services involved.",
        "Hostel": "The hostel management office has been informed. The warden will review the "
                  "situation and follow up with you directly.",
        "Facilities": "The facilities and maintenance team has been notified and will inspect the "
                      "issue as soon as possible.",
        "Finance": "Your concern has been forwarded to the finance office. Please keep your payment "
                   "receipts and student ID number ready, as they may be needed to verify your account.",
        "Transportation": "The transport office has been informed and will review the route, schedule "
                          "or service you described.",
        "Other": "We have received your complaint and will direct it to the appropriate department "
                 "for review.",
    }
    body = bodies[category]

    # Part 4: expected reply time, chosen by priority
    timeframe = RESPONSE_TIMEFRAME[priority]
    if priority == "High":
        follow_up = f"Because this matter appears urgent, it has been marked as high priority and you can expect an update {timeframe}."
    else:
        follow_up = f"You can expect an update from us {timeframe}."

    closing = ("Please reply to this message if you have any additional information that could help us.\n\n"
               "Kind regards,\nUniversity Support Team")

    # Join the parts with blank lines between them.
    return "\n\n".join([greeting, f"{opening} {body}", follow_up, closing])


# ===============================================================
# 4. THE MAIN FUNCTION  (this is the one app.py will call)
# ===============================================================
def analyze_complaint(description, title="", student_name=None):
    """Analyse a complaint and return a dictionary with these keys:

        category            one of: Academic, IT / Network, Library, Hostel,
                            Facilities, Finance, Transportation, Other
        sentiment           Positive, Neutral or Negative
        priority            Low, Medium or High
        confidence          0-100 (how sure the engine is about the category)
        summary             a short summary of the complaint
        suggested_response  a professional reply staff can send to the student

    description   -> the complaint text (required)
    title         -> the complaint title (optional, makes the category more accurate)
    student_name  -> used in the greeting of the suggested response (optional)

    The keys match the columns of the ai_analysis database table, so the
    result can be saved later with save_ai_analysis()."""

    title = title or ""
    description = description or ""

    # Nothing to analyse -> return safe default values.
    if not (title.strip() or description.strip()):
        return {
            "category": "Other",
            "sentiment": "Neutral",
            "priority": "Medium",
            "confidence": 0.0,
            "summary": "No complaint text was provided.",
            "suggested_response": generate_suggested_response("Other", "Neutral", "Medium", student_name),
        }

    # The title is repeated once so its words count a little extra for the
    # category (a title such as "Library Wi-Fi down" is very informative).
    category_text = clean_text(f"{title} {title} {description}")
    # For sentiment and priority the title and description are counted once.
    full_text = clean_text(f"{title} {description}")

    category, confidence = classify_category(category_text)
    sentiment = analyze_sentiment(full_text)
    priority = recommend_priority(full_text, sentiment)
    summary = generate_summary(
        title, description, category, sentiment, priority)
    suggested_response = generate_suggested_response(
        category, sentiment, priority, student_name)

    return {
        "category": category,
        "sentiment": sentiment,
        "priority": priority,
        "confidence": confidence,
        "summary": summary,
        "suggested_response": suggested_response,
    }


# ===============================================================
# 5. QUICK SELF-TEST
# ===============================================================
# This block only runs when you start THIS file directly
# (python utils/ai_engine.py). It does not run when app.py imports the module.
if __name__ == "__main__":
    sample_complaints = [
        ("Wi-Fi down in library",
         "The Wi-Fi in the library has not worked for three days. I cannot access the student portal "
         "and my assignment deadline is tomorrow. This is unacceptable!"),
        ("Late campus bus",
         "The morning bus to campus is always late and the driver skips the bus stop near my house."),
        ("Thank you",
         "Thank you to the librarian for helping me find the books I needed. Excellent service."),
        ("Double tuition charge",
         "I was charged my tuition fee twice this semester and I need a refund."),
        ("Canteen idea",
         "It would be nice if the canteen offered more vegetarian options. Just a suggestion."),
        ("Weather",
         "The weather has been sunny this week."),
    ]

    for number, (title, description) in enumerate(sample_complaints, start=1):
        result = analyze_complaint(
            description, title=title, student_name="Alex")
        print("=" * 70)
        print(f"Sample {number}: {title}")
        print(
            f"  Category   : {result['category']}  (confidence {result['confidence']}%)")
        print(f"  Sentiment  : {result['sentiment']}")
        print(f"  Priority   : {result['priority']}")
        print(f"  Summary    : {result['summary']}")
        if number == 1:
            # Print one full suggested response so you can read it.
            print("  Suggested response:")
            for line in result["suggested_response"].splitlines():
                print("    " + line)
