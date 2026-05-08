"""
Student views for dashboard, chatbot, assessments, counselling, and wellness content.
"""
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib import error, request as urllib_request

from bson.objectid import ObjectId
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.risk_engine import update_user_risk
from .models import (
    Appointment,
    Assessment,
    BreathingExercise,
    CareTask,
    ChatLog,
    CounsellorMessage,
    CounsellorSessionNote,
    DailyPost,
    JournalEntry,
    MeditationGuide,
    MotivationalContent,
    StudentReply,
)
from .stress_detector import analyze_stress_message

logger = logging.getLogger(__name__)

AI_SYSTEM_PROMPT = (
    "You are Wellify, a calm and supportive mental wellness assistant for students. "
    "Respond in a warm, practical, non-judgmental tone. Keep answers concise, actionable, "
    "and supportive. Do not claim to be a human therapist, do not diagnose, and encourage "
    "professional or emergency help when there is mention of self-harm, suicide, or immediate danger. "
    "Offer short coping strategies, grounding steps, journaling prompts, breathing ideas, and help-seeking suggestions."
)

CRISIS_KEYWORDS = (
    "suicide",
    "kill myself",
    "want to die",
    "end my life",
    "self harm",
    "can't live anymore",
    "hopeless",
    "no reason to live",
)

MAX_CHAT_HISTORY_ITEMS = 12
LANGUAGE_CHOICES = {"en", "hi", "gu"}
LANGUAGE_LABELS = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}
ASSESSMENT_NUDGE_GAP = 4

CONTENT_TRANSLATIONS = {
    "hi": {
        "Support": "सपोर्ट",
        "Wellify Team": "वेलिफाई टीम",
        "Motivation": "प्रेरणा",
        "Self-Compassion": "स्वयं के प्रति करुणा",
        "Mindfulness for Overthinking": "ओवरथिंकिंग के लिए माइंडफुलनेस",
        "Guided Meditation for Deep Sleep": "गहरी नींद के लिए गाइडेड मेडिटेशन",
        "Breathing for Panic Relief": "पैनिक राहत के लिए ब्रीदिंग",
        "Coherent Breathing": "कोहेरेंट ब्रीदिंग",
        "Physiological Sigh": "फिजियोलॉजिकल साई",
        "You Deserve Support Before a Crisis": "संकट से पहले भी आप सहयोग के हकदार हैं",
        "One Small Step Still Counts": "एक छोटा कदम भी मायने रखता है",
        "A supportive meditation for students dealing with self-criticism, setbacks, or emotional exhaustion.": "आत्म-आलोचना, असफलताओं या भावनात्मक थकान से जूझ रहे छात्रों के लिए सहायक मेडिटेशन।",
        "Learn to observe thoughts without being pulled into them with a practical mindfulness session.": "व्यावहारिक माइंडफुलनेस सत्र के साथ विचारों को बिना उनमें फंसे देखना सीखें।",
        "Slow down racing thoughts and prepare your body for deep, restorative sleep.": "तेज़ दौड़ते विचारों को धीमा करें और शरीर को गहरी, आरामदायक नींद के लिए तैयार करें।",
        "A guided breathing practice designed to slow the body when panic sensations or overwhelm start rising.": "घबराहट या ओवरवेल्म बढ़ने पर शरीर को शांत करने के लिए गाइडेड ब्रीदिंग अभ्यास।",
        "A balanced breathing rhythm that supports calm focus, especially useful during study breaks.": "संतुलित ब्रीदिंग रिदम जो शांत फोकस बनाए रखती है, खासकर पढ़ाई के ब्रेक में उपयोगी।",
        "A fast-acting breathing reset that can quickly reduce stress and lower physical tension.": "तेज़ असर वाला ब्रीदिंग रीसेट जो तनाव और शारीरिक खिंचाव जल्दी कम कर सकता है।",
        "You do not have to wait until things fall apart to ask for help. Support is not only for emergencies. It is also for confusion, stress, loneliness, pressure, and those days when ...": "मदद मांगने के लिए हालात बिगड़ने का इंतज़ार जरूरी नहीं। सहयोग सिर्फ इमरजेंसी के लिए नहीं, बल्कि भ्रम, तनाव, अकेलापन और दबाव के दिनों के लिए भी है।",
        "When everything feels too much, shrink the goal. Open the document. Drink water. Sit by the window. Send one message. Tiny actions are often the doorway back into motion.": "जब सब कुछ बहुत भारी लगे, लक्ष्य छोटा करें। डॉक्युमेंट खोलें। पानी पिएं। खिड़की के पास बैठें। एक संदेश भेजें। छोटे कदम ही दोबारा गति की शुरुआत होते हैं।",
    },
    "gu": {
        "Support": "સપોર્ટ",
        "Wellify Team": "વેલિફાય ટીમ",
        "Motivation": "પ્રેરણા",
        "Self-Compassion": "સ્વ-કૃપા",
        "Mindfulness for Overthinking": "ઓવરથિંકિંગ માટે માઇન્ડફુલનેસ",
        "Guided Meditation for Deep Sleep": "ઊંડી ઊંઘ માટે માર્ગદર્શિત ધ્યાન",
        "Breathing for Panic Relief": "પેનિક રાહત માટે શ્વાસ અભ્યાસ",
        "Coherent Breathing": "સંતુલિત શ્વાસ",
        "Physiological Sigh": "ફિઝિયોલોજિકલ સાઈ",
        "You Deserve Support Before a Crisis": "સંકટ પહેલાં પણ તમે સહાયના હકદાર છો",
        "One Small Step Still Counts": "એક નાનું પગલું પણ મહત્વનું છે",
        "A supportive meditation for students dealing with self-criticism, setbacks, or emotional exhaustion.": "આત્મ-આલોચના, નિષ્ફળતા અથવા ભાવનાત્મક થાકનો સામનો કરતા વિદ્યાર્થીઓ માટે સહાયક ધ્યાન.",
        "Learn to observe thoughts without being pulled into them with a practical mindfulness session.": "વ્યવહારુ માઇન્ડફુલનેસ સેશન સાથે વિચારોને તેમાં ફસાય્યા વિના જોવું શીખો.",
        "Slow down racing thoughts and prepare your body for deep, restorative sleep.": "ઝડપથી દોડતા વિચારો ધીમા કરો અને શરીરને ઊંડી, પુનઃસ્થાપક ઊંઘ માટે તૈયાર કરો.",
        "A guided breathing practice designed to slow the body when panic sensations or overwhelm start rising.": "ઘબરામણ અથવા ઓવરવેલ્મ વધે ત્યારે શરીરને શાંત કરવા માટે રચાયેલ માર્ગદર્શિત શ્વાસ અભ્યાસ.",
        "A balanced breathing rhythm that supports calm focus, especially useful during study breaks.": "શાંત ફોકસ માટે મદદરૂપ સંતુલિત શ્વાસ લય, ખાસ કરીને અભ્યાસના વિરામ દરમિયાન ઉપયોગી.",
        "A fast-acting breathing reset that can quickly reduce stress and lower physical tension.": "ઝડપી અસર આપતું શ્વાસ રીસેટ જે તણાવ અને શારીરિક તાણ ઝડપથી ઘટાડે છે.",
        "You do not have to wait until things fall apart to ask for help. Support is not only for emergencies. It is also for confusion, stress, loneliness, pressure, and those days when ...": "મદદ માગવા માટે પરિસ્થિતિ બગડે ત્યાં સુધી રાહ જોવાની જરૂર નથી. સહાય માત્ર ઇમરજન્સી માટે નથી. ગૂંચવણ, તણાવ, એકલતા, દબાણ અને એવા દિવસો માટે પણ છે જ્યારે ...",
        "When everything feels too much, shrink the goal. Open the document. Drink water. Sit by the window. Send one message. Tiny actions are often the doorway back into motion.": "જ્યારે બધું વધારે લાગે, લક્ષ્ય નાનું કરો. દસ્તાવેજ ખોલો. પાણી પીવો. બારી પાસે બેસો. એક સંદેશ મોકલો. નાનાં પગલાં ઘણી વાર ફરી ગતિમાં આવવાનો દરવાજો બને છે.",
    },
}

INTENT_LIBRARY = {
    "anxiety": {
        "keywords": ("anxious", "anxiety", "panic", "nervous", "overthinking", "worry", "worried"),
        "reflection": "Your message suggests anxiety or mental overload.",
        "coping": [
            "Try one round of box breathing: inhale 4, hold 4, exhale 4, hold 4.",
            "Name 5 things you can see, 4 you can feel, 3 you can hear, 2 you can smell, and 1 you can taste.",
        ],
        "follow_up": "If this keeps returning, complete the assessment and compare how often anxiety is affecting study, sleep, or concentration.",
    },
    "sadness": {
        "keywords": ("sad", "down", "depressed", "empty", "hopeless", "crying", "low"),
        "reflection": "Your message suggests low mood or emotional heaviness.",
        "coping": [
            "Reduce the next hour to one manageable task and one supportive action, such as food, water, sunlight, or a short walk.",
            "Write one sentence about what is hardest today instead of trying to solve everything at once.",
        ],
        "follow_up": "If this has been lasting for days or affecting daily functioning, use the assessment and consider booking a counselling session.",
    },
    "academic": {
        "keywords": ("exam", "assignment", "deadline", "study", "college", "marks", "result", "project"),
        "reflection": "This sounds tied to academic pressure.",
        "coping": [
            "Break the work into one 20-minute focus block and define the smallest visible output for that block.",
            "Stop planning the whole day and choose only the next concrete deliverable.",
        ],
        "follow_up": "If pressure is affecting sleep, appetite, or motivation, use Wellify support tools before the stress compounds.",
    },
    "sleep": {
        "keywords": ("sleep", "insomnia", "tired", "awake", "rest", "night"),
        "reflection": "Sleep seems to be part of the issue.",
        "coping": [
            "Avoid solving tomorrow tonight; write your pending thoughts down before bed.",
            "Use a low-stimulation reset for 10 minutes: dim light, slow breathing, no scrolling.",
        ],
        "follow_up": "If poor sleep continues, track it for a few days and bring it into a counselling conversation.",
    },
    "lonely": {
        "keywords": ("alone", "lonely", "isolated", "nobody", "ignored"),
        "reflection": "Your message suggests disconnection or loneliness.",
        "coping": [
            "Send one low-pressure message to a person you trust instead of waiting to feel ready.",
            "Move toward one real-world environment today, even briefly, rather than staying isolated the whole day.",
        ],
        "follow_up": "If isolation is becoming your default pattern, that is a strong reason to use counselling support.",
    },
}

ASSESSMENT_SESSION_KEY = "chatbot_assessment_state"
ASSESSMENT_ACCEPT_WORDS = {"yes", "haan", "start", "ok", "okay", "sure", "continue", "begin", "screening"}
ASSESSMENT_DECLINE_WORDS = {"no", "nahi", "later", "skip", "cancel", "stop"}
ASSESSMENT_DIRECT_START = {"start screening", "screening", "start assessment", "start phq", "start gad"}
ASSESSMENT_EXIT_WORDS = {
    "stop screening",
    "exit screening",
    "cancel screening",
    "stop assessment",
    "exit assessment",
    "chat normally",
    "normal chat",
}

PHQ_QUESTIONS = [
    "Over the last 2 weeks, how often have you had little interest or pleasure in doing things?",
    "Over the last 2 weeks, how often have you been feeling down, depressed, or hopeless?",
    "Over the last 2 weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
    "Over the last 2 weeks, how often have you been feeling tired or having little energy?",
    "Over the last 2 weeks, how often have you had poor appetite or been overeating?",
    "Over the last 2 weeks, how often have you felt bad about yourself, or that you are a failure, or that you have let yourself or your family down?",
    "Over the last 2 weeks, how often have you had trouble concentrating on things such as reading or studying?",
    "Over the last 2 weeks, how often have you been moving or speaking so slowly that other people could have noticed, or the opposite, being so fidgety or restless that you were moving around a lot more than usual?",
    "Over the last 2 weeks, how often have you had thoughts that you would be better off dead or of hurting yourself in some way?",
]

GAD_QUESTIONS = [
    "Over the last 2 weeks, how often have you been feeling nervous, anxious, or on edge?",
    "Over the last 2 weeks, how often have you not been able to stop or control worrying?",
    "Over the last 2 weeks, how often have you been worrying too much about different things?",
    "Over the last 2 weeks, how often have you had trouble relaxing?",
    "Over the last 2 weeks, how often have you been so restless that it was hard to sit still?",
    "Over the last 2 weeks, how often have you become easily annoyed or irritable?",
    "Over the last 2 weeks, how often have you felt afraid, as if something awful might happen?",
]

ASSESSMENT_OPTIONS_TEXT = "Reply with 0, 1, 2, or 3. 0 = Not at all, 1 = Several days, 2 = More than half the days, 3 = Nearly every day."


def _response_for_stress(level):
    if level == "Low":
        return "That's good to hear. Keep taking care of yourself. You're doing great!"
    if level == "Medium":
        return (
            "It's okay to feel this way. Try deep breathing, a short walk, or talking to "
            "someone you trust. You can also book a counselling session if you'd like extra support."
        )
    return (
        "We're concerned about your wellbeing. Please consider booking a counselling session "
        "as soon as you can. You're not alone - reach out to a counsellor or a trusted person."
    )


def _t(lang, en, hi, gu):
    language = _normalize_chat_language(lang)
    if language == "hi":
        return hi
    if language == "gu":
        return gu
    return en


def _build_local_support_response(message, stress, language="en"):
    lower = (message or "").strip().lower()
    if any(keyword in lower for keyword in CRISIS_KEYWORDS):
        return _t(
            language,
            "I'm really sorry you're carrying this right now. If you might hurt yourself or you feel unsafe, please contact local emergency services or a crisis helpline immediately, and reach out to a trusted person nearby right now. You can also book a counselling session in Wellify so support can follow up quickly.",
            "Mujhe bahut afsos hai ki aap itna heavy feel kar rahe ho. Agar aapko khud ko nuksan pahunchane ka risk lag raha hai, turant emergency service ya crisis helpline se contact karo aur kisi trusted person ko abhi batao. Wellify me counselling session bhi book kar sakte ho.",
            "તમે ઘણું ભાર અનુભવો છો એ બદલ મને ખેદ છે. જો તમને પોતાને નુકસાન પહોંચાડવાનો જોખમ લાગે તો તરત ઇમરજન્સી સેવા અથવા ક્રાઇસિસ હેલ્પલાઇનનો સંપર્ક કરો અને નજીકના વિશ્વાસુ વ્યક્તિને કહો. Wellify માં કાઉન્સેલિંગ સેશન પણ બુક કરી શકો છો.",
        )

    lang = _normalize_chat_language(language)
    if lang in {"hi", "gu"}:
        localized_plan = {
            "hi": {
                "Low": [
                    "Aaj ka routine stable rakho: paani, khana, short walk, aur sahi sleep time.",
                    "5 minute deep breathing ya journaling se mood track karo.",
                ],
                "Medium": [
                    "Abhi sirf next 20-minute ka ek kaam choose karo aur usi pe focus karo.",
                    "Overthinking break ke liye 4-4-4-4 breathing cycle try karo.",
                ],
                "High": [
                    "Abhi non-essential kaam rok do aur trusted person se baat karo.",
                    "Counsellor session jaldi book karo; delay mat karo.",
                ],
                "title": "Main samajh raha hoon:",
                "action": "Abhi kya karein:",
                "next_q": "Aapko abhi sabse zyada problem kis cheez me hai: sleep, thoughts, anxiety, ya studies?",
            },
            "gu": {
                "Low": [
                    "આજનો રૂટિન સ્થિર રાખો: પાણી, ભોજન, નાની વોક અને યોગ્ય ઊંઘ.",
                    "5 મિનિટ ડીપ બ્રેધિંગ અથવા જર્નલિંગથી મૂડ ટ્રેક કરો.",
                ],
                "Medium": [
                    "હમણાં ફક્ત આવતા 20 મિનિટનું એક કામ પસંદ કરો અને તે પર ફોકસ કરો.",
                    "ઓવરથિંકિંગ ઘટાડવા 4-4-4-4 બ્રેધિંગ સાયકલ અજમાવો.",
                ],
                "High": [
                    "હમણાં non-essential કામ રોકો અને વિશ્વાસુ વ્યક્તિ સાથે વાત કરો.",
                    "કાઉન્સેલર સેશન તાત્કાલિક બુક કરો; મોડું ન કરો.",
                ],
                "title": "હું સમજી રહ્યો છું:",
                "action": "હમણાં શું કરવું:",
                "next_q": "હમણાં તમને સૌથી વધુ મુશ્કેલી કઈ બાબતમાં છે: ઊંઘ, વિચારો, ચિંતા કે અભ્યાસ?",
            },
        }
        plan = localized_plan[lang]
        lines = [
            plan["title"],
            (message or "").strip()[:130],
            "",
            plan["action"],
            f"- {plan.get(stress, plan['Low'])[0]}",
            f"- {plan.get(stress, plan['Low'])[1]}",
            "",
            plan["next_q"],
        ]
        if stress == "High":
            lines.append(_t(lang, "", "Agar safety concern ho to emergency help turant lo.", "જો સુરક્ષા જોખમ લાગે તો તરત ઇમરજન્સી મદદ લો."))
        return "\n".join([line for line in lines if line])

    matched_intent = None
    for intent in INTENT_LIBRARY.values():
        if any(keyword in lower for keyword in intent["keywords"]):
            matched_intent = intent
            break

    general_support = {
        "Low": [
            "Protect your current balance with a short breathing break or a journal check-in.",
            "Use one small wellbeing action before stress builds up.",
        ],
        "Medium": [
            "Reduce the situation to one next action you can complete in the next 10 to 20 minutes.",
            "Pair that action with one grounding tool, such as breathing or stepping away from the screen.",
        ],
        "High": [
            "Stop non-essential tasks and focus on immediate support, grounding, and safety.",
            "Use the counsellor booking flow now rather than waiting for the feeling to pass by itself.",
        ],
    }

    option_pool = matched_intent["coping"] if matched_intent else general_support.get(stress, general_support["Low"])
    if not option_pool:
        option_pool = general_support["Low"]
    # Keep fallback responses varied for similar prompts.
    offset = int(hashlib.md5(lower.encode("utf-8")).hexdigest(), 16) % len(option_pool)
    rotated_coping = option_pool[offset:] + option_pool[:offset]

    short_reflection = (message or "").strip()
    if len(short_reflection) > 120:
        short_reflection = short_reflection[:117] + "..."

    lines = [
        _t(language, "What I hear:", "Main samajh pa raha hoon:", "હું જે સમજ્યો છું:"),
        matched_intent["reflection"] if matched_intent else "You seem to be dealing with a meaningful amount of pressure right now.",
        f'Your words: "{short_reflection}"' if short_reflection else "",
        "",
        _t(language, "What to do right now:", "Abhi turant kya karein:", "હમણાં શું કરવું:"),
    ]

    for item in rotated_coping[:2]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            _t(language, "Next step in Wellify:", "Wellify me next step:", "Wellify માં આગળનું પગલું:"),
            matched_intent["follow_up"] if matched_intent else "Use the assessment for a structured check-in, or open journaling if you need to clear your head.",
        ]
    )

    if stress == "High":
        lines.extend(
            [
                "",
                _t(language, "Safety note:", "Safety note:", "સેફ્ટી નોંધ:"),
                "If you feel at risk of harming yourself or you feel unsafe, contact emergency support or a crisis helpline immediately and tell a trusted person now.",
            ]
        )

    lines.extend(
        [
            "",
            _t(language, "Quick check-in question:", "Ek quick check-in:", "ઝડપી ચેક-ઇન:"),
            _t(language, "What feels hardest right now: thoughts, body symptoms, sleep, or studies?", "Abhi sabse mushkil kya lag raha hai: thoughts, body symptoms, sleep ya studies?", "હમણાં સૌથી મુશ્કેલ શું લાગે છે: વિચારો, શરીરના લક્ષણો, ઊંઘ કે અભ્યાસ?"),
        ]
    )
    return "\n".join(line for line in lines if line != "")


def _make_non_repetitive_response(user_id, response_text):
    last_log = ChatLog.objects.filter(user_id=user_id).order_by("-timestamp").first()
    if not last_log:
        return response_text
    if (last_log.response or "").strip() != (response_text or "").strip():
        return response_text

    variants = [
        "\n\nLet's take this one step at a time. Tell me what hit you most today.",
        "\n\nI am with you in this. Would you like a 2-minute quick calming reset right now?",
        "\n\nThanks for sharing honestly. Should we focus first on sleep, thoughts, or study pressure?",
    ]
    index = int(hashlib.md5((last_log.message or "").encode("utf-8")).hexdigest(), 16) % len(variants)
    return response_text + variants[index]


def _format_detection_reason(analysis):
    signals = analysis.get("signals") or []
    if signals:
        return ", ".join(signals)
    return "general emotional stress indicators"


def _pick_available_counsellor():
    counsellors = list(User.objects.filter(role="Counsellor"))
    if not counsellors:
        return None
    load_by_counsellor = {}
    for counsellor in counsellors:
        load_by_counsellor[counsellor.id] = Appointment.objects.filter(
            counsellor_id=counsellor.id, status__in=("Pending", "Approved")
        ).count()
    return min(counsellors, key=lambda item: load_by_counsellor.get(item.id, 0))


def _ensure_high_risk_followup(student):
    existing = Appointment.objects.filter(
        student_id=student.id, status__in=("Pending", "Approved")
    ).first()
    if existing:
        return False
    counsellor = _pick_available_counsellor()
    if not counsellor:
        return False
    Appointment(
        student_id=student.id,
        counsellor_id=counsellor.id,
        date=datetime.now().strftime("%Y-%m-%d"),
        status="Pending",
    ).save()
    return True


def _should_show_assessment_nudge(session, stress):
    if stress not in ("Medium", "High"):
        return False
    count = int(session.get("assessment_nudge_count", 0) or 0)
    # Show only first time and then every few messages.
    should_show = count == 0 or (count % ASSESSMENT_NUDGE_GAP == 0)
    session["assessment_nudge_count"] = count + 1
    return should_show


def _new_assessment_state():
    return {
        "stage": "offer",
        "phq_answers": [],
        "gad_answers": [],
    }


def _format_assessment_question(state):
    if state["stage"] == "phq":
        index = len(state["phq_answers"])
        total = len(PHQ_QUESTIONS)
        question = PHQ_QUESTIONS[index]
        label = f"PHQ-9 Question {index + 1} of {total}"
    else:
        index = len(state["gad_answers"])
        total = len(GAD_QUESTIONS)
        question = GAD_QUESTIONS[index]
        label = f"GAD-7 Question {index + 1} of {total}"
    return f"{label}\n{question}\n\n{ASSESSMENT_OPTIONS_TEXT}"


def _parse_assessment_answer(message):
    cleaned = (message or "").strip().lower()
    aliases = {
        "0": 0,
        "not at all": 0,
        "1": 1,
        "several days": 1,
        "2": 2,
        "more than half the days": 2,
        "3": 3,
        "nearly every day": 3,
    }
    if cleaned in aliases:
        return aliases[cleaned]
    return None


def _save_assessment_result(user, phq_score, gad_score):
    from accounts.risk_engine import determine_final_level, update_user_risk

    final_level = determine_final_level(phq=phq_score, gad=gad_score)
    total_legacy = phq_score + gad_score
    Assessment(
        user_id=user.id,
        total_score=total_legacy,
        stress_level=final_level,
        phq_score=phq_score,
        gad_score=gad_score,
        final_level=final_level,
    ).save()
    update_user_risk(user, phq=phq_score, gad=gad_score)
    return final_level


def _complete_chat_assessment(request, state):
    phq_score = sum(state["phq_answers"])
    gad_score = sum(state["gad_answers"])
    final_level = _save_assessment_result(request.user, phq_score, gad_score)
    request.session["assessment_result"] = {
        "phq_score": phq_score,
        "gad_score": gad_score,
        "final_level": final_level,
    }
    request.session.pop(ASSESSMENT_SESSION_KEY, None)
    lines = [
        "Quick screening complete.",
        f"PHQ-9 score: {phq_score}",
        f"GAD-7 score: {gad_score}",
        f"Current level: {final_level}",
        "",
    ]
    if final_level == "High":
        lines.append("This result suggests a high level of concern. Please book a counselling session as soon as possible.")
    elif final_level == "Medium":
        lines.append("This result suggests a moderate level of concern. Use the assessment result, breathing tools, and consider counselling support.")
    else:
        lines.append("This result suggests a lower current severity level. Continue using preventive support tools and monitor how you feel.")
    lines.append("You can also open the assessment results page for the structured summary.")
    return "\n".join(lines), final_level


def _handle_chat_assessment_flow(request, message):
    state = request.session.get(ASSESSMENT_SESSION_KEY)
    cleaned = (message or "").strip().lower()

    if not state:
        return None

    if state["stage"] == "offer":
        if cleaned in ASSESSMENT_ACCEPT_WORDS:
            state["stage"] = "phq"
            request.session[ASSESSMENT_SESSION_KEY] = state
            return _format_assessment_question(state), "Medium", False
        if cleaned in ASSESSMENT_DECLINE_WORDS:
            request.session.pop(ASSESSMENT_SESSION_KEY, None)
            return "No problem. You can keep chatting normally, or start the quick screening anytime by saying: start screening.", "Low", False
        return "If you want the quick screening, reply with 'yes' or 'start'. If not, reply 'no' or 'later'.", "Low", False

    if cleaned in ASSESSMENT_EXIT_WORDS:
        request.session.pop(ASSESSMENT_SESSION_KEY, None)
        return (
            "Screening paused. We are back to normal chat now.\n"
            "If you want, share what is bothering you in your own words and I will support you step by step.",
            "Low",
            False,
        )

    answer = _parse_assessment_answer(message)
    if answer is None:
        return (
            f"Please reply with 0, 1, 2, or 3.\n\n{ASSESSMENT_OPTIONS_TEXT}\n\n"
            "If you want to stop screening and return to normal chat, type: stop screening."
        ), "Low", False

    if state["stage"] == "phq":
        state["phq_answers"].append(answer)
        if len(state["phq_answers"]) < len(PHQ_QUESTIONS):
            request.session[ASSESSMENT_SESSION_KEY] = state
            return _format_assessment_question(state), "Medium", False
        state["stage"] = "gad"
        request.session[ASSESSMENT_SESSION_KEY] = state
        return (
            "PHQ-9 section complete.\n\nNow continuing with the GAD-7 anxiety screening.\n\n"
            + _format_assessment_question(state),
            "Medium",
            False,
        )

    state["gad_answers"].append(answer)
    if len(state["gad_answers"]) < len(GAD_QUESTIONS):
        request.session[ASSESSMENT_SESSION_KEY] = state
        return _format_assessment_question(state), "Medium", False

    response_text, final_level = _complete_chat_assessment(request, state)
    return response_text, final_level, final_level == "High"


def _looks_like_assessment_answer(text):
    cleaned = (text or "").strip().lower()
    if cleaned in {"0", "1", "2", "3", "not at all", "several days", "more than half the days", "nearly every day"}:
        return True
    return False


def _is_openai_enabled():
    return bool(os.environ.get("OPENAI_API_KEY"))


def _normalize_chat_language(language):
    lang = (language or "").strip().lower()
    return lang if lang in LANGUAGE_CHOICES else "en"


def _translate_content_text(text, language):
    lang = _normalize_chat_language(language)
    if not text:
        return text
    cleaned_text = str(text)
    # Repair common mojibake artifacts (utf-8 text decoded as latin-1/cp1252).
    if any(token in cleaned_text for token in ("Ã", "â", "Â")):
        try:
            repaired = cleaned_text.encode("latin-1").decode("utf-8")
            cleaned_text = repaired
        except Exception:
            pass
    if lang == "en":
        return cleaned_text
    lang_map = CONTENT_TRANSLATIONS.get(lang, {})
    translated = lang_map.get(cleaned_text)
    if translated:
        return translated
    stripped = cleaned_text.strip()
    translated = lang_map.get(stripped)
    if translated:
        return translated
    # Fuzzy normalize for punctuation/spacing variants from DB seeds.
    normalized = (
        stripped.replace("…", "...")
        .replace(" - ", " ")
        .replace("’", "'")
        .replace('"', "")
        .replace(",", "")
        .replace(".", "")
        .replace(":", "")
        .lower()
    )
    normalized = " ".join(normalized.split())
    for source, target in lang_map.items():
        source_normalized = (
            str(source).strip()
            .replace("…", "...")
            .replace(" - ", " ")
            .replace("’", "'")
            .replace('"', "")
            .replace(",", "")
            .replace(".", "")
            .replace(":", "")
            .lower()
        )
        source_normalized = " ".join(source_normalized.split())
        if normalized == source_normalized:
            return target
        # Handle long seeded texts with small copy edits/truncation.
        if len(source_normalized) > 40 and (
            normalized.startswith(source_normalized)
            or source_normalized.startswith(normalized)
        ):
            return target
    return cleaned_text


def _call_openai_chatbot(user_message, session, user, stress, language):
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1")
    if not api_key:
        return None

    recent_messages = list(ChatLog.objects.filter(user_id=user.id).order_by("-timestamp")[:8])
    recent_messages.reverse()
    history_lines = []
    for item in recent_messages:
        history_lines.append(f"User: {item.message}")
        history_lines.append(f"Assistant: {item.response[:380]}")
    history_text = "\n".join(history_lines).strip() or "No previous chat history."

    language_name = LANGUAGE_LABELS.get(_normalize_chat_language(language), "English")

    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"{AI_SYSTEM_PROMPT}\n"
                            f"Current stress estimate from classifier: {stress}.\n"
                            f"Preferred response language: {language_name}.\n"
                            "Use the recent context if relevant, avoid repetitive phrasing, and finish with one gentle follow-up question.\n"
                            "Keep response practical, 5 to 10 lines, and use short bullet points when giving steps.\n"
                            "If language is Hindi, use easy Hinglish style. If Gujarati, use simple Gujarati script."
                        ),
                    }
                ],
            },
            {
                "role": "system",
                "content": [{"type": "input_text", "text": f"Recent context:\n{history_text}"}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_message}],
            },
        ],
        "max_output_tokens": 420,
    }

    previous_response_id = session.get("chatbot_previous_response_id")
    if previous_response_id:
        payload["previous_response_id"] = previous_response_id

    req = urllib_request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        logger.warning("OpenAI chatbot HTTP error: %s", exc.read().decode("utf-8", errors="ignore"))
        return None
    except Exception as exc:
        logger.warning("OpenAI chatbot unavailable: %s", exc)
        return None

    output_text = (data.get("output_text") or "").strip()
    if not output_text:
        fragments = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    fragments.append(content.get("text", ""))
        output_text = "".join(fragments).strip()

    if output_text and data.get("id"):
        session["chatbot_previous_response_id"] = data["id"]

    return output_text or None


@login_required
def student_dashboard(request):
    if getattr(request.user, "role", None) != "Student":
        messages.warning(request, "Access denied.")
        return redirect("accounts:login")

    recent_assessments = list(Assessment.objects.filter(user_id=request.user.id).order_by("-created_at")[:30])
    today = datetime.now().date()
    trend_days = [today - timedelta(days=day_offset) for day_offset in range(6, -1, -1)]
    trend_labels = [day.strftime("%d %b") for day in trend_days]
    trend_points = {day: 0 for day in trend_days}
    for item in recent_assessments:
        created_at = getattr(item, "created_at", None) or getattr(item, "date", None)
        if not created_at:
            continue
        day = created_at.date()
        if day in trend_points:
            trend_points[day] = max(trend_points[day], int(getattr(item, "phq_score", 0) or 0) + int(getattr(item, "gad_score", 0) or 0))

    all_posts = list(DailyPost.objects.order_by("-created_at")[:8])
    student_map = {u.id: u for u in User.objects.filter(role="Student")}
    global_post_feed = []
    for post in all_posts:
        author = student_map.get(post.user_id)
        global_post_feed.append(
            {
                "post": post,
                "author_name": author.name if author else f"Student #{post.user_id}",
            }
        )

    stress = getattr(request.user, "current_stress_level", "Low") or "Low"
    lang = _normalize_chat_language(request.session.get("django_language", "en"))
    localized_meditations = []
    for item in list(MeditationGuide.objects.order_by("-created_at")[:3]):
        localized_meditations.append(
            {
                "id": item.id,
                "duration": item.duration,
                "title": _translate_content_text(item.title, lang),
                "description": _translate_content_text(item.description, lang),
            }
        )
    localized_breathing = []
    for item in list(BreathingExercise.objects.order_by("-created_at")[:3]):
        localized_breathing.append(
            {
                "id": item.id,
                "duration": item.duration,
                "title": _translate_content_text(item.title, lang),
                "description": _translate_content_text(item.description, lang),
            }
        )
    localized_motivation = []
    for item in list(MotivationalContent.objects.order_by("-created_at")[:2]):
        localized_motivation.append(
            {
                "id": item.id,
                "category": _translate_content_text(item.category, lang),
                "author": _translate_content_text(item.author, lang),
                "title": _translate_content_text(item.title, lang),
                "content": _translate_content_text(item.content, lang),
            }
        )

    context = {
        "user": request.user,
        "stress": stress,
        "meditation_count": MeditationGuide.objects.count(),
        "breathing_count": BreathingExercise.objects.count(),
        "motivation_count": MotivationalContent.objects.count(),
        "recent_meditations": localized_meditations,
        "recent_breathing": localized_breathing,
        "recent_motivation": localized_motivation,
        "trend_labels_json": json.dumps(trend_labels),
        "trend_values_json": json.dumps([trend_points[day] for day in trend_days]),
        "recent_daily_posts": list(DailyPost.objects.filter(user_id=request.user.id).order_by("-created_at")[:5]),
        "global_post_feed": global_post_feed,
        "default_image_post_text": _t(lang, "(Image-only post)", "(केवल इमेज पोस्ट)", "(ફક્ત ઇમેજ પોસ્ટ)"),
        "default_inspiration_text": _t(lang, "Inspiration", "प्रेरणा", "પ્રેરણા"),
        "counsellor_messages": list(
            CounsellorMessage.objects.filter(student_id=request.user.id).order_by("-created_at")[:5]
        ),
        "student_replies": list(
            StudentReply.objects.filter(student_id=request.user.id).order_by("-created_at")[:5]
        ),
        "care_tasks": list(CareTask.objects.filter(student_id=request.user.id).order_by("-created_at")[:6]),
        "latest_session_note": None,
    }
    latest_note = CounsellorSessionNote.objects.filter(student_id=request.user.id).order_by("-created_at").first()
    context["latest_session_note"] = latest_note
    return render(request, "student/student_dashboard.html", context)


@login_required
@require_POST
def chatbot_send(request):
    """Handle chatbot message, save chat, and update risk state."""
    if getattr(request.user, "role", None) != "Student":
        return JsonResponse({"error": "Forbidden"}, status=403)

    msg = (request.POST.get("message") or "").strip()
    if not msg:
        return JsonResponse(
            {
                "response": "Please type a message.",
                "stress_level": "Low",
                "risk_level": getattr(request.user, "current_stress_level", "Low") or "Low",
            }
        )

    try:
        chat_language = _normalize_chat_language(request.POST.get("language") or request.session.get("chatbot_language", "en"))
        request.session["chatbot_language"] = chat_language
        cleaned_msg = msg.lower()
        if request.session.get(ASSESSMENT_SESSION_KEY):
            # If user sends normal sentence during screening, auto-exit screening.
            if (not _looks_like_assessment_answer(msg)) and cleaned_msg not in ASSESSMENT_EXIT_WORDS:
                if any(ch.isalpha() for ch in msg) and len(msg.strip()) > 4:
                    request.session.pop(ASSESSMENT_SESSION_KEY, None)

        if cleaned_msg in ASSESSMENT_DIRECT_START:
            request.session[ASSESSMENT_SESSION_KEY] = {"stage": "phq", "phq_answers": [], "gad_answers": []}
            request.session["assessment_nudge_count"] = 0
            response_text = _format_assessment_question(request.session[ASSESSMENT_SESSION_KEY])
            final_level = update_user_risk(request.user, chat_level="Medium")
            ChatLog(
                user_id=request.user.id,
                message=msg,
                response=response_text,
                stress_level="Medium",
            ).save()
            return JsonResponse(
                {
                    "response": response_text,
                    "stress_level": "Medium",
                    "risk_level": final_level,
                    "show_alert": False,
                    "assessment_mode": True,
                }
            )

        assessment_result = _handle_chat_assessment_flow(request, msg)
        if assessment_result is not None:
            response_text, stress, show_alert = assessment_result
            if "Quick screening complete." in response_text:
                request.session["assessment_nudge_count"] = 0
            final_level = update_user_risk(request.user, chat_level=stress)
            ChatLog(
                user_id=request.user.id,
                message=msg,
                response=response_text,
                stress_level=stress,
            ).save()
            return JsonResponse(
                {
                    "response": response_text,
                    "stress_level": stress,
                    "risk_level": final_level,
                    "show_alert": show_alert,
                    "assessment_mode": True,
                }
            )

        stress_analysis = analyze_stress_message(msg)
        stress = stress_analysis["level"]
        response_text = _call_openai_chatbot(msg, request.session, request.user, stress, chat_language)
        if not response_text:
            response_text = _build_local_support_response(msg, stress, chat_language)
            if not _is_openai_enabled():
                response_text += (
                    "\n\nNote: AI key not configured. Add OPENAI_API_KEY to enable full ChatGPT-like responses."
                )

        response_text = _make_non_repetitive_response(request.user.id, response_text)

        if stress == "High" and not any(
            keyword in response_text.lower()
            for keyword in ("emergency", "crisis", "trusted person", "helpline")
        ):
            response_text += (
                " If you feel unsafe or at risk, please contact emergency support or a crisis helpline immediately "
                "and tell a trusted person."
            )

        ChatLog(
            user_id=request.user.id,
            message=msg,
            response=response_text,
            stress_level=stress,
        ).save()

        final_level = update_user_risk(request.user, chat_level=stress)
        reason = _format_detection_reason(stress_analysis)
        response_text += (
            f"\n\nLive chat stress: {stress} (signals: {reason})"
            f"\nCurrent risk level: {final_level}"
        )

        if (
            not request.session.get(ASSESSMENT_SESSION_KEY)
            and _should_show_assessment_nudge(request.session, stress)
        ):
            response_text += (
                "\n\nIf you want, I can also run a quick PHQ-9 + GAD-7 screening."
                "\nType 'start screening' anytime."
            )
        if final_level == "High":
            auto_created = _ensure_high_risk_followup(request.user)
            response_text += " A counsellor has been notified and will reach out. You are not alone."
            if auto_created:
                response_text += " A priority counselling session request has been created automatically."
            logger.warning("High-risk user detected: %s - %s", request.user.id, request.user.email)
            return JsonResponse(
                {
                    "response": response_text,
                    "stress_level": stress,
                    "risk_level": final_level,
                    "show_alert": True,
                    "counsellor_notified": True,
                    "auto_session_created": auto_created,
                }
            )

        return JsonResponse(
            {
                "response": response_text,
                "stress_level": stress,
                "risk_level": final_level,
                "chat_language": chat_language,
                "show_alert": stress == "High",
            }
        )
    except Exception as exc:
        logger.error("Error in chatbot_send: %s", exc)
        return JsonResponse(
            {
                "response": "Sorry, something went wrong. Please try again.",
                "stress_level": "Low",
                "risk_level": getattr(request.user, "current_stress_level", "Low") or "Low",
                "error": True,
            },
            status=500,
        )


def _get_phq_gad_from_request(request):
    """Parse PHQ-9 (q1..q9) and GAD-7 (g1..g7) from POST."""
    phq = 0
    for i in range(1, 10):
        try:
            phq += int(request.POST.get(f"q{i}", 0))
        except ValueError:
            pass

    gad = 0
    for i in range(1, 8):
        try:
            gad += int(request.POST.get(f"g{i}", 0))
        except ValueError:
            pass
    return phq, gad


@login_required
def assessment_view(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")

    if request.method == "POST":
        phq_score, gad_score = _get_phq_gad_from_request(request)
        final_level = _save_assessment_result(request.user, phq_score, gad_score)
        request.session["assessment_result"] = {
            "phq_score": phq_score,
            "gad_score": gad_score,
            "final_level": final_level,
        }
        return redirect("student:assessment_result")

    return render(request, "student/assessment.html")


@login_required
def chatbot_view(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    return render(
        request,
        "student/chatbot.html",
        {
            "chatbot_is_ai_powered": _is_openai_enabled(),
            "chatbot_model_name": os.environ.get("OPENAI_MODEL", "gpt-4.1"),
            "current_risk_level": getattr(request.user, "current_stress_level", "Low") or "Low",
            "chat_language": _normalize_chat_language(request.session.get("chatbot_language", "en")),
        },
    )


@login_required
def chatbot_history(request):
    if getattr(request.user, "role", None) != "Student":
        return JsonResponse({"error": "Forbidden"}, status=403)

    items = list(ChatLog.objects.filter(user_id=request.user.id).order_by("-timestamp")[:MAX_CHAT_HISTORY_ITEMS])
    items.reverse()
    data = []
    for item in items:
        ts = item.timestamp.strftime("%d %b %I:%M %p") if item.timestamp else ""
        data.append(
            {
                "user_message": item.message,
                "bot_response": item.response,
                "stress_level": item.stress_level,
                "timestamp": ts,
            }
        )
    return JsonResponse({"history": data})


@login_required
def chatbot_export_pdf(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")

    logs = list(ChatLog.objects.filter(user_id=request.user.id).order_by("-timestamp")[:40])
    logs.reverse()

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except Exception:
        messages.error(request, "PDF export dependency missing. Please install reportlab: pip install reportlab")
        return redirect("student:chatbot")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="wellify_chat_export.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 0.8 * inch

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(0.8 * inch, y, "Wellify Chat Export")
    y -= 0.28 * inch

    pdf.setFont("Helvetica", 10)
    pdf.drawString(0.8 * inch, y, f"Student: {request.user.name} ({request.user.email})")
    y -= 0.24 * inch
    pdf.drawString(0.8 * inch, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 0.4 * inch

    if not logs:
        pdf.drawString(0.8 * inch, y, "No chat history available.")
    else:
        def safe_pdf_text(text):
            return (text or "").encode("latin-1", errors="replace").decode("latin-1")

        for item in logs:
            ts = item.timestamp.strftime("%d %b %Y %I:%M %p") if item.timestamp else "-"
            lines = [
                safe_pdf_text(f"[{ts}] You: {item.message}"),
                safe_pdf_text(f"Wellify ({item.stress_level}): {item.response}"),
                "",
            ]
            for line in lines:
                chunks = [line[i:i + 105] for i in range(0, len(line), 105)] or [""]
                for chunk in chunks:
                    if y < 0.9 * inch:
                        pdf.showPage()
                        y = height - 0.8 * inch
                        pdf.setFont("Helvetica", 10)
                    pdf.drawString(0.8 * inch, y, chunk)
                    y -= 0.19 * inch

    pdf.save()
    return response


@login_required
def community_posts_view(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")

    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        language = _normalize_chat_language(request.POST.get("language"))
        image_file = request.FILES.get("image")
        image_url = ""
        if not content and not image_file:
            messages.error(request, "Please write something or upload an image before posting.")
            return redirect("student:community_posts")
        if image_file:
            suffix = Path(image_file.name).suffix.lower()
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                messages.error(request, "Only JPG, PNG, or WEBP images are allowed.")
                return redirect("student:community_posts")
            filename = default_storage.save(f"daily_posts/{request.user.id}_{int(datetime.now().timestamp())}{suffix}", ContentFile(image_file.read()))
            image_url = default_storage.url(filename)
        analysis = analyze_stress_message(content) if content else {"level": "Low"}
        DailyPost(
            user_id=request.user.id,
            content=content,
            image_url=image_url,
            language=language,
            stress_level=analysis["level"],
        ).save()
        if analysis["level"] == "High":
            if _ensure_high_risk_followup(request.user):
                messages.warning(request, "High-risk signal detected. A priority counselling session request was created.")
        messages.success(request, f"Post shared. Current signal level: {analysis['level']}.")
        return redirect("student:community_posts")

    all_posts = list(DailyPost.objects.order_by("-created_at")[:40])
    user_map = {u.id: u for u in User.objects.filter(role="Student")}
    feed = []
    for post in all_posts:
        author = user_map.get(post.user_id)
        feed.append(
            {
                "post": post,
                "author_name": (author.name if author else f"Student #{post.user_id}"),
            }
        )

    return render(
        request,
        "student/community_posts.html",
        {
            "feed": feed,
            "selected_language": _normalize_chat_language(request.session.get("chatbot_language", "en")),
        },
    )


@login_required
@require_POST
def delete_daily_post_view(request, post_id):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    try:
        post = DailyPost.objects.get(id=ObjectId(post_id))
    except Exception:
        messages.error(request, "Post not found.")
        return redirect("student:community_posts")

    if post.user_id != request.user.id:
        messages.error(request, "You can delete only your own posts.")
        return redirect("student:community_posts")

    try:
        post.delete()
        messages.success(request, "Post deleted successfully.")
    except Exception:
        messages.error(request, "Unable to delete post right now. Please try again.")
    return redirect(request.POST.get("next") or "student:community_posts")


@login_required
@require_POST
def complete_care_task_view(request, task_id):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    try:
        task = CareTask.objects.get(id=ObjectId(task_id), student_id=request.user.id)
    except Exception:
        messages.error(request, "Task not found.")
        return redirect("student:student_dashboard")
    if task.status != "Completed":
        task.status = "Completed"
        task.completed_at = datetime.utcnow()
        task.save()
        messages.success(request, "Care task marked as completed.")
    return redirect(request.POST.get("next") or "student:student_dashboard")


@login_required
def assessment_result_view(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    data = request.session.pop("assessment_result", None)
    if not data:
        return redirect("student:assessment")
    return render(request, "student/assessment_result.html", data)


@login_required
def book_session_view(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")

    if request.method == "POST":
        date = (request.POST.get("date") or "").strip()
        time_slot = (request.POST.get("time_slot") or "").strip()
        if not date:
            messages.error(request, "Please select a date.")
            return render(request, "student/book_session.html")

        from datetime import datetime

        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            if date_obj.date() < datetime.now().date():
                messages.error(request, "Please select a future date.")
                return render(request, "student/book_session.html")
        except ValueError:
            messages.error(request, "Invalid date format.")
            return render(request, "student/book_session.html")

        counsellor = User.objects.filter(role="Counsellor").first()
        if not counsellor:
            messages.error(request, "No counsellor available. Please try later.")
            return render(request, "student/book_session.html")

        try:
            Appointment(
                student_id=request.user.id,
                counsellor_id=counsellor.id,
                date=date,
                time_slot=time_slot,
                status="Pending",
            ).save()
            slot_display = f" at {time_slot}" if time_slot else ""
            messages.success(request, f"Appointment requested for {date}{slot_display}. Counsellor will confirm.")
        except Exception as exc:
            logger.error("Error booking appointment: %s", exc)
            messages.error(request, "Failed to book appointment. Please try again.")
        return redirect("student:student_dashboard")

    return render(request, "student/book_session.html")


@login_required
def meditation_list(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    meditations = list(MeditationGuide.objects.order_by("-created_at"))
    return render(request, "student/meditation_list.html", {"meditations": meditations})


@login_required
def meditation_detail(request, meditation_id):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    try:
        meditation = MeditationGuide.objects.get(id=ObjectId(meditation_id))
    except (MeditationGuide.DoesNotExist, Exception) as exc:
        logger.error("Error fetching meditation: %s", exc)
        messages.error(request, "Meditation not found.")
        return redirect("student:meditation_list")
    return render(request, "student/meditation_detail.html", {"meditation": meditation})


@login_required
def breathing_list(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    exercises = list(BreathingExercise.objects.order_by("-created_at"))
    return render(request, "student/breathing_list.html", {"exercises": exercises})


@login_required
def breathing_detail(request, breathing_id):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    try:
        exercise = BreathingExercise.objects.get(id=ObjectId(breathing_id))
    except (BreathingExercise.DoesNotExist, Exception) as exc:
        logger.error("Error fetching breathing exercise: %s", exc)
        messages.error(request, "Exercise not found.")
        return redirect("student:breathing_list")
    return render(request, "student/breathing_detail.html", {"exercise": exercise})


@login_required
def journal_list(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    entries = list(JournalEntry.objects.filter(user_id=request.user.id).order_by("-created_at"))
    return render(request, "student/journal_list.html", {"entries": entries})


@login_required
def journal_create(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        mood = (request.POST.get("mood") or "").strip()
        stress = getattr(request.user, "current_stress_level", "Low") or "Low"
        if not content:
            messages.error(request, "Please write something in your journal.")
            return redirect("student:journal_create")
        JournalEntry(
            user_id=request.user.id,
            content=content,
            mood=mood,
            stress_level=stress,
        ).save()
        messages.success(request, "Journal entry saved!")
        return redirect("student:journal_list")
    return render(request, "student/journal_create.html")


@login_required
def journal_detail(request, journal_id):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    try:
        entry = JournalEntry.objects.get(id=ObjectId(journal_id), user_id=request.user.id)
    except (JournalEntry.DoesNotExist, Exception) as exc:
        logger.error("Error fetching journal entry: %s", exc)
        messages.error(request, "Entry not found.")
        return redirect("student:journal_list")
    return render(request, "student/journal_detail.html", {"entry": entry})


@login_required
def journal_delete(request, journal_id):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    if request.method != "POST":
        return redirect("student:journal_list")
    try:
        entry = JournalEntry.objects.get(id=ObjectId(journal_id), user_id=request.user.id)
        entry.delete()
        messages.success(request, "Journal entry deleted.")
    except (JournalEntry.DoesNotExist, Exception) as exc:
        logger.error("Error deleting journal entry: %s", exc)
        messages.error(request, "Entry not found.")
    return redirect("student:journal_list")


@login_required
@require_POST
def reply_counsellor(request):
    if getattr(request.user, 'role', None) != 'Student':
        return redirect('accounts:login')
    msg = (request.POST.get('message') or '').strip()
    counsellor_id = request.POST.get('counsellor_id')
    if not msg or not counsellor_id:
        messages.error(request, 'Message cannot be empty.')
        return redirect('student:student_dashboard')
    try:
        StudentReply(
            student_id=request.user.id,
            counsellor_id=int(counsellor_id),
            message=msg,
        ).save()
        messages.success(request, 'Message sent to counsellor.')
    except Exception as exc:
        logger.error('Error sending student reply: %s', exc)
        messages.error(request, 'Failed to send message.')
    return redirect('student:student_dashboard')


@login_required
def motivation_list(request):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    content = list(MotivationalContent.objects.order_by("-created_at"))
    return render(request, "student/motivation_list.html", {"content": content})


@login_required
def motivation_detail(request, motivation_id):
    if getattr(request.user, "role", None) != "Student":
        return redirect("accounts:login")
    try:
        item = MotivationalContent.objects.get(id=ObjectId(motivation_id))
    except (MotivationalContent.DoesNotExist, Exception) as exc:
        logger.error("Error fetching motivational content: %s", exc)
        messages.error(request, "Content not found.")
        return redirect("student:motivation_list")
    return render(request, "student/motivation_detail.html", {"item": item})
