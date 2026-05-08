LOW_STRESS_KEYWORDS = [
    "okay", "fine", "good", "happy", "relaxed", "calm", "normal", "better", "stable", "manageable"
]

MEDIUM_STRESS_KEYWORDS = [
    "stressed", "anxious", "worried", "tired", "pressure",
    "overthinking", "panic", "confused", "nervous",
    "not feeling good", "sad", "demotivated", "burnout", "burned out",
    "can't focus", "cant focus", "sleep issue", "insomnia", "restless"
]

HIGH_STRESS_KEYWORDS = [
    "depressed", "hopeless", "worthless", "crying",
    "suicide", "kill myself", "want to die",
    "life is meaningless", "no reason to live",
    "self harm", "end my life", "can't live anymore", "cant live anymore",
    "hurt myself", "i give up", "i am done", "nobody cares"
]


def analyze_stress_message(message):
    text = (message or "").lower()
    high_hits = [word for word in HIGH_STRESS_KEYWORDS if word in text]
    medium_hits = [word for word in MEDIUM_STRESS_KEYWORDS if word in text]
    low_hits = [word for word in LOW_STRESS_KEYWORDS if word in text]

    weighted_score = (len(high_hits) * 3) + (len(medium_hits) * 2) - len(low_hits)

    if high_hits or weighted_score >= 4:
        level = "High"
    elif medium_hits or weighted_score >= 2:
        level = "Medium"
    else:
        level = "Low"

    matched = high_hits or medium_hits or low_hits
    return {
        "level": level,
        "score": weighted_score,
        "signals": matched[:4],
    }


def detect_stress_level(message):
    return analyze_stress_message(message)["level"]