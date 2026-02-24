# # mylocalizationproject/localizationtool/models.py
# from django.db import models
# from django.conf import settings
# from django.core.files.storage import FileSystemStorage
# import os  # Added this import

# # Use default storage based on MEDIA_ROOT instead of /tmp/
# fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))  # Move to media/uploads/

# class LocalizationUpload(models.Model):
#     pot_file = models.FileField(upload_to='pots/')  # Relative to MEDIA_ROOT
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Upload {self.id} - {self.pot_file.name}"

# class TranslationResult(models.Model):
#     upload = models.ForeignKey(LocalizationUpload, on_delete=models.CASCADE)
#     language = models.CharField(max_length=10, choices=settings.LANGUAGES)  # Use Django LANGUAGES
#     po_file = models.FileField(upload_to='translations/po/')  # Relative to MEDIA_ROOT
#     mo_file = models.FileField(upload_to='translations/mo/')  # Relative to MEDIA_ROOT
#     translated_at = models.DateTimeField(auto_now_add=True)
#     edited_content = models.TextField(null=True, blank=True)  # Store edited .po content

#     def __str__(self):
#         return f"{self.get_language_display()} - {self.upload.pot_file.name}"

#     def get_language_display(self):
#         # Fallback if choices aren't applied correctly
#         for lang_code, lang_name in settings.LANGUAGES:
#             if lang_code == self.language:
#                 return lang_name
#         return self.language.title()  # Default to capitalized code if not found


# localization FRStool/models.py
from django.db import models
import os

class LocalizationUpload(models.Model):
    pot_file = models.FileField(upload_to='uploads/', max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    folder_name = models.CharField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.folder_name and self.pot_file:
            base = os.path.splitext(os.path.basename(self.pot_file.name))[0]
            base = base.replace('_', '-').strip().lower()
            self.folder_name = base

            # Ensure uniqueness
            original = self.folder_name
            counter = 1
            while LocalizationUpload.objects.filter(folder_name=self.folder_name).exclude(pk=self.pk).exists():
                self.folder_name = f"{original}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.folder_name or "Unnamed Upload"


class TranslationResult(models.Model):
    upload = models.ForeignKey(LocalizationUpload, on_delete=models.CASCADE)
    language = models.CharField(max_length=10)
    po_file = models.CharField(max_length=500)
    mo_file = models.CharField(max_length=500)
    edited_content = models.TextField(blank=True, null=True)
    translated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('upload', 'language')