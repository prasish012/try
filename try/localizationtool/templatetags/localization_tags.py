# # from django import template

# # register = template.Library()

# # @register.filter
# # def language_name(code):
# #     language_map = {
# #         'en': 'English',
# #         'es': 'Spanish',
# #         'de': 'German',
# #         'fr': 'French',
# #         'pt': 'Portuguese',
# #         'hi': 'Hindi',
# #         'ne': 'Nepali',
# #         'ar': 'Arabic',
# #         'it': 'Italian',
# #         'ja': 'Japanese',
# #         'pl': 'Polish',
# #         'ru': 'Russian',
# #         'nl': 'Dutch',
# #     }
# #     return language_map.get(code, code)


# # localizationtool/templatetags/localization_tags.py

# from django import template
# from django.conf import settings

# register = template.Library()


# @register.filter
# def language_name(code):
#     """
#     Convert language code (e.g. 'en-us') → human name from settings.LANGUAGES
#     Fallback: return code if not found
#     """
#     lang_dict = dict(settings.LANGUAGES)
#     return lang_dict.get(code, code)


# @register.filter
# def filter_by_language(queryset, lang_code):
#     """
#     Filter TranslationResult queryset by language code
#     Used in translation_selection.html
#     """
#     return queryset.filter(language=lang_code).first()





# localizationtool/templatetags/localization_tags.py
from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter
def language_name(code):
    from django.conf import settings
    return dict(settings.LANGUAGES).get(code, code)

@register.filter
def basename(path):
    import os
    return os.path.basename(path)