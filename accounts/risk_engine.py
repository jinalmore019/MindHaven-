"""
Risk Engine – single place for all risk/stress level logic.
Used by chatbot, assessment, and counsellor views. Do not duplicate rules elsewhere.
"""

# Numeric mapping for risk_score (for ordering/display)
_LEVEL_SCORE = {'Low': 1, 'Medium': 2, 'High': 3}


def calculate_chat_risk(chat_level):
    """
    Map chat stress level to risk. Returns 'Low', 'Medium', or 'High'.
    """
    if not chat_level:
        return 'Low'
    cap = (chat_level or '').strip()
    if cap == 'High':
        return 'High'
    if cap == 'Medium':
        return 'Medium'
    return 'Low'


def calculate_assessment_risk(phq, gad):
    """
    Determine assessment-based level from PHQ and GAD scores.
    phq, gad can be None (treated as 0). Returns 'Low', 'Medium', or 'High'.
    """
    p = 0 if phq is None else int(phq)
    g = 0 if gad is None else int(gad)
    if p >= 15 or g >= 15:
        return 'High'
    if 10 <= p <= 14 or 10 <= g <= 14:
        return 'Medium'
    return 'Low'


def determine_final_level(chat_level=None, phq=None, gad=None):
    """
    Combine chat and assessment inputs into one final level.
    Rules:
    - HIGH if chat_level == 'High' OR phq >= 15 OR gad >= 15
    - MEDIUM if chat_level == 'Medium' OR 10 <= phq <= 14 OR 10 <= gad <= 14
    - LOW otherwise
    """
    chat_risk = calculate_chat_risk(chat_level)
    assess_risk = calculate_assessment_risk(phq, gad)
    if chat_risk == 'High' or assess_risk == 'High':
        return 'High'
    if chat_risk == 'Medium' or assess_risk == 'Medium':
        return 'Medium'
    return 'Low'


def update_user_risk(user, chat_level=None, phq=None, gad=None):
    """
    Update user's risk_score, current_stress_level, and is_flagged_high.
    Saves the user. Returns final_level ('Low', 'Medium', 'High').
    """
    final = determine_final_level(chat_level=chat_level, phq=phq, gad=gad)
    user.current_stress_level = final
    user.risk_score = _LEVEL_SCORE.get(final, 0)
    user.is_flagged_high = (final == 'High')
    user.save(update_fields=['risk_score', 'current_stress_level', 'is_flagged_high'])
    return final
