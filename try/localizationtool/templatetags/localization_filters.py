# mylocalizationproject/localizationtool/templatetags/localization_filters.py
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def language_name(language_code):
    """
    Convert a language code to its human-readable name using settings.LANGUAGES.
    """
    for code, name in settings.LANGUAGES:
        if code == language_code:
            return name
    return language_code  # Fallback to code if not found