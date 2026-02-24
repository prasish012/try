# from django import forms

# class LocalizationForm(forms.Form):
#     upload_po_file = forms.FileField(label='Upload .po File:', required=False)
#     upload_zip_file = forms.FileField(label='Upload .zip File (optional):', required=False)
#     upload_glossary_file = forms.FileField(label='Upload Glossary .csv File (optional):', required=False)

#     LANGUAGES = [
#         ('en', 'English'),
#         ('es', 'Spanish'),
#         ('de', 'German'),
#         ('fr', 'French'),
#         ('pt', 'Portuguese'),
#         ('hi', 'Hindi'),
#         ('ne', 'Nepali'),
#         ('ar', 'Arabic'),
#         ('it', 'Italian'),
#         ('ja', 'Japanese'),
#         ('pl', 'Polish'),
#         ('ru', 'Russian'),
#         ('nl', 'Dutch'),
#     ]

#     target_languages = forms.MultipleChoiceField(
#         choices=LANGUAGES,
#         widget=forms.CheckboxSelectMultiple,
#         required=True
#     )

# localizationtool/forms.py

# localizationtool/forms.py
# from django import forms
# from django.conf import settings

# class LocalizationForm(forms.Form):
#     upload_po_file = forms.FileField(
#         label='Upload .pot File:',
#         required=False,
#         widget=forms.FileInput(attrs={'accept': '.po,.pot'})
#     )
#     upload_zip_file = forms.FileField(
#         label='Upload .zip File (optional):',
#         required=False,
#         widget=forms.FileInput(attrs={'accept': '.zip'})
#     )
#     upload_glossary_file = forms.FileField(
#         label='Upload Glossary .csv File (optional):',
#         required=False,
#         widget=forms.FileInput(attrs={'accept': '.csv'})
#     )

#     # DYNAMIC: Pulls from settings.py
#     target_languages = forms.MultipleChoiceField(
#         choices=[(code, name) for code, name in settings.LANGUAGES],
#         widget=forms.CheckboxSelectMultiple,
#         required=True,
#         label="Target languages:",
#         help_text="Select one or more languages to translate into."
#     )




# localizationtool/forms.py

from django import forms
from django.conf import settings

class LocalizationForm(forms.Form):
    upload_po_file = forms.FileField(
        label="Upload .pot or .po Template",
        widget=forms.FileInput(attrs={'accept': '.pot,.po'})
    )
    upload_zip_file = forms.FileField(
        label="Upload Existing Translations ZIP (with folders like Dutch/, Arabic/ — optional)",
        required=False,
        widget=forms.FileInput(attrs={'accept': '.zip'})
    )
    upload_glossary_file = forms.FileField(
        label="Upload Glossary (CSV or ZIP with lang CSV files — optional)",
        required=False,
        widget=forms.FileInput(attrs={'accept': '.csv,.zip'})
    )
    target_languages = forms.MultipleChoiceField(
        choices=[(code, name) for code, name in settings.LANGUAGES],
        widget=forms.CheckboxSelectMultiple,
        label="Select Target Languages",
        required=True
    )