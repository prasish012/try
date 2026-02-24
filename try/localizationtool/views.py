# localizationtool/views.py
# FINAL STRONG VERSION — JavaScript Escape + HTML Entity Handling (Feb 23, 2026)

import os
import shutil
import zipfile
import tempfile
import re
import html
from collections import defaultdict
import polib   

from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .forms import LocalizationForm
from .models import LocalizationUpload, TranslationResult
from .localization_logic import ColabLocalizationTool


# ====================== LANGUAGE FOLDER MAP ======================
LANG_FOLDER_MAP = {
    "arabic": "ar", "dutch": "nl", "french": "fr", "german": "de",
    "hindi": "hi", "italian": "it", "japanese": "ja", "nepali": "ne",
    "polish": "pl", "portuguese": "pt", "russian": "ru", "spanish": "es",
}


# ====================== MAIN TOOL VIEW ======================
def localize_tool_view(request):
    if request.method == 'POST':
        form = LocalizationForm(request.POST, request.FILES)
        if form.is_valid():
            pot_file = request.FILES['upload_po_file']
            zip_file = request.FILES.get('upload_zip_file')
            glossary_input = request.FILES.get('upload_glossary_file')
            target_languages = form.cleaned_data['target_languages']

            folder_name = os.path.splitext(pot_file.name)[0]

            existing = LocalizationUpload.objects.filter(folder_name=folder_name).first()
            if existing:
                existing.delete()

            upload = LocalizationUpload(pot_file=pot_file)
            upload.save()

            project_dir = os.path.join(settings.MEDIA_ROOT, 'translations', upload.folder_name)
            os.makedirs(project_dir, exist_ok=True)

            pot_path = os.path.join(project_dir, pot_file.name)
            with open(pot_path, 'wb') as f:
                for chunk in pot_file.chunks():
                    f.write(chunk)

            zip_paths_by_lang = {}
            if zip_file:
                extract_dir = os.path.join(project_dir, "existing_translations")
                os.makedirs(extract_dir, exist_ok=True)

                zip_path = os.path.join(project_dir, "existing.zip")
                with open(zip_path, 'wb') as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(extract_dir)

                for item in os.listdir(extract_dir):
                    item_path = os.path.join(extract_dir, item)
                    if os.path.isdir(item_path):
                        folder_lower = item.lower()
                        lang_code = LANG_FOLDER_MAP.get(folder_lower)
                        if lang_code and lang_code in target_languages:
                            zip_paths_by_lang[lang_code] = item_path

                if not zip_paths_by_lang:
                    for lang in target_languages:
                        zip_paths_by_lang[lang] = extract_dir

            glossary_by_lang = {}
            if glossary_input:
                gloss_dir = os.path.join(project_dir, "glossaries")
                os.makedirs(gloss_dir, exist_ok=True)
                csv_path = os.path.join(gloss_dir, glossary_input.name)
                with open(csv_path, 'wb') as f:
                    for chunk in glossary_input.chunks():
                        f.write(chunk)
                for lang in target_languages:
                    glossary_by_lang[lang] = csv_path

            tool = ColabLocalizationTool()
            success = tool.run(
                pot_path=pot_path,
                zip_paths_by_lang=zip_paths_by_lang,
                glossary_by_lang=glossary_by_lang,
                target_langs=target_languages,
                output_dir=project_dir,
                use_wporg=True
            )

            if success:
                messages.success(request, f"Translation completed: {folder_name}")
            else:
                messages.error(request, "Translation failed — check console logs")

            return redirect('localize_tool_view')
    else:
        form = LocalizationForm()

    folders = []
    translations_root = os.path.join(settings.MEDIA_ROOT, 'translations')
    if os.path.exists(translations_root):
        for d in sorted(os.listdir(translations_root), reverse=True):
            full_path = os.path.join(translations_root, d)
            if os.path.isdir(full_path):
                upload = LocalizationUpload.objects.filter(folder_name=d).first()
                folders.append({'name': d, 'upload': upload})

    return render(request, 'localizationtool/combined_view.html', {
        'form': form,
        'folders': folders
    })


# ====================== VIEW PROJECT ======================
def view_and_edit_translations(request, folder_name):
    project_dir = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
    if not os.path.isdir(project_dir):
        raise Http404("Project not found")

    upload = get_object_or_404(LocalizationUpload, folder_name=folder_name)

    lang_versions = defaultdict(list)
    for file_name in os.listdir(project_dir):
        if file_name.endswith('.po'):
            parts = file_name.rsplit('-', 1)
            if len(parts) == 2:
                lang_code = parts[0]
                try:
                    version = int(parts[1].replace('.po', ''))
                    po_path = os.path.join(project_dir, file_name)
                    lang_versions[lang_code].append({
                        'version': version,
                        'file_name': file_name,
                        'po_path': po_path,
                    })
                except:
                    continue

    for lang in lang_versions:
        lang_versions[lang].sort(key=lambda x: x['version'], reverse=True)

    return render(request, 'localizationtool/edit_translations.html', {
        'folder_name': folder_name,
        'upload': upload,
        'lang_versions': dict(lang_versions),
    })


# ====================== EDIT VERSION ======================
def edit_language_version(request, folder_name, lang_code, version):
    po_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name, f"{lang_code}-{version}.po")
    if not os.path.exists(po_path):
        raise Http404("PO file not found")

    po = polib.pofile(po_path)

    entries = []
    for entry in po:
        if entry.msgid:
            safe_key = f"trans_{re.sub(r'[^a-zA-Z0-9_]', '_', entry.msgid)[:100]}"
            entries.append({
                'msgid': entry.msgid,
                'msgstr': entry.msgstr,
                'safe_key': safe_key,
                'fuzzy': 'fuzzy' in entry.flags,
            })

    lang_name = dict(settings.LANGUAGES).get(lang_code, lang_code.upper())

    return render(request, 'localizationtool/edit_language_version.html', {
        'folder_name': folder_name,
        'lang_code': lang_code,
        'lang_name': lang_name,
        'version': version,
        'entries': entries,
        'po_path': po_path,
    })


# ====================== SAVE SINGLE TRANSLATION (STRONGEST DECODING) ======================
@csrf_exempt
def save_translation(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    po_path = request.POST.get('po_path')
    raw_msgid = request.POST.get('msgid', '')
    msgstr = request.POST.get('msgstr', '')

    if not po_path or not os.path.exists(po_path) or not raw_msgid:
        return JsonResponse({'status': 'error', 'message': 'Missing required data'}, status=400)

    try:
        po = polib.pofile(po_path)
        updated = False

        # STRONG DECODER: Convert JavaScript escape + HTML entities
        def normalize_string(s):
            if not s:
                return ''
            # Decode JavaScript \u0026, \u201C, etc.
            s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
            # Decode HTML entities (&ldquo;, &copy;, etc.)
            s = html.unescape(s)
            # Normalize spaces
            s = re.sub(r'\s+', ' ', s.strip())
            return s

        normalized_input = normalize_string(raw_msgid)

        for entry in po:
            normalized_entry = normalize_string(entry.msgid)

            if normalized_entry == normalized_input or normalized_entry.lower() == normalized_input.lower():
                entry.msgstr = msgstr
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
                updated = True
                break

        if updated:
            po.save(po_path)
            po.save_as_mofile(po_path.replace('.po', '.mo'))
            return JsonResponse({
                'status': 'success',
                'message': '✅ Translation saved successfully!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'String not found: "{raw_msgid[:100]}"'
            })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)


# ====================== CHECK VALIDATION ======================
@csrf_exempt
def check_po_validation(request):
    if request.method == 'POST':
        po_path = request.POST.get('po_path')
        if not po_path or not os.path.exists(po_path):
            return JsonResponse({'status': 'error', 'message': 'PO file not found'})

        tool = ColabLocalizationTool()
        warnings = tool._validate_po_file(po_path)

        if not warnings:
            return JsonResponse({'status': 'success', 'message': '✅ All correct! No format errors found.'})
        else:
            return JsonResponse({
                'status': 'warning',
                'message': f'⚠ Found {len(warnings)} issue(s):',
                'warnings': warnings
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# ====================== OTHER FUNCTIONS ======================
def download_folder(request, folder_name):
    folder_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
    if not os.path.isdir(folder_path):
        raise Http404("Folder not found")

    zip_path = shutil.make_archive(folder_path, 'zip', folder_path)

    response = FileResponse(open(zip_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{folder_name}_translations.zip"'
    return response


def delete_folder(request, folder_name):
    if request.method == 'POST':
        folder_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)

            upload = LocalizationUpload.objects.filter(folder_name=folder_name).first()
            if upload:
                TranslationResult.objects.filter(upload=upload).delete()
                upload.delete()

            messages.success(request, f'Project "{folder_name}" deleted successfully.')

    return redirect('localize_tool_view')