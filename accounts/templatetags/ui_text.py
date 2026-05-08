from django import template
from django.utils.translation import get_language

register = template.Library()


_TEXTS = {
    "brand_subtitle": {
        "en": "Mental wellness platform for students",
        "hi": "Students ke liye mental wellness platform",
        "gu": "વિદ્યાર્થીઓ માટે માનસિક સ્વાસ્થ્ય પ્લેટફોર્મ",
    },
    "dashboard": {"en": "Dashboard", "hi": "Dashboard", "gu": "ડેશબોર્ડ"},
    "my_profile": {"en": "My Profile", "hi": "Meri Profile", "gu": "મારી પ્રોફાઇલ"},
    "logout": {"en": "Logout", "hi": "Logout", "gu": "લોગઆઉટ"},
    "login": {"en": "Login", "hi": "Login", "gu": "લૉગિન"},
    "create_account": {"en": "Create account", "hi": "Account banao", "gu": "એકાઉન્ટ બનાવો"},
    "language": {"en": "Language", "hi": "Bhasha", "gu": "ભાષા"},
}


@register.simple_tag
def ui_text(key):
    lang = (get_language() or "en")[:2]
    values = _TEXTS.get(key, {})
    return values.get(lang) or values.get("en") or key
