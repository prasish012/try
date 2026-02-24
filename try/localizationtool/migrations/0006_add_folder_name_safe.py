# localizationtool/migrations/0006_add_folder_name_safe.py
from django.db import migrations, models
import os


def populate_folder_name(apps, schema_editor):
    LocalizationUpload = apps.get_model('localizationtool', 'LocalizationUpload')
    seen = {}

    for upload in LocalizationUpload.objects.all().order_by('id'):
        if not upload.pot_file:
            upload.folder_name = f"upload-{upload.id}"
            upload.save(update_fields=['folder_name'])
            continue

        # Extract base name: reviewnews.pot → reviewnews
        base = os.path.splitext(os.path.basename(upload.pot_file.name))[0]
        base = base.replace('_', '-').strip().lower()
        original = base

        # Track how many times we've seen this base
        counter = seen.get(base, 0) + 1
        seen[base] = counter

        # Only add suffix if duplicate
        upload.folder_name = f"{original}-{counter}" if counter > 1 else original
        upload.save(update_fields=['folder_name'])


class Migration(migrations.Migration):

    dependencies = [
        ('localizationtool', '0005_alter_translationresult_mo_file_and_more'),
    ]

    operations = [
        # 1. Add the field (nullable first)
        migrations.AddField(
            model_name='localizationupload',
            name='folder_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        # 2. Backfill unique folder names
        migrations.RunPython(populate_folder_name, reverse_code=migrations.RunPython.noop),
        # 3. Enforce uniqueness
        migrations.AlterField(
            model_name='localizationupload',
            name='folder_name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
