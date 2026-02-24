# # double % and  placeholder on wrong place
# # localizationtool/localization_logic.py
# # ULTIMATE FINAL VERSION — DUPLICATE PLACEHOLDERS FIXED + STRONG FORCING (Jan 29, 2026)

# import polib
# import csv
# import os
# import re
# import json
# import requests
# import time
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings
# from charset_normalizer import from_path
# from deep_translator import GoogleTranslator as _GoogleTranslator


# class GoogleTranslatorEngine:
#     _BLOCK_KEYWORDS = [
#         "error 500", "504", "that’s an error", "please try again later",
#         "that’s all we know", "1500", "1504", "unusual traffic",
#         "server error", "blocked", "captcha", "<html", "<!doctype"
#     ]

#     def translate_single(self, text: str, target_lang: str) -> str:
#         original = text
#         for attempt in range(5):
#             try:
#                 translator = _GoogleTranslator(source='auto', target=target_lang)
#                 trans = translator.translate(text)
#                 time.sleep(4.0)
                
#                 trans_str = str(trans).strip()
#                 if any(kw.lower() in trans_str.lower() for kw in self._BLOCK_KEYWORDS):
#                     print(f"   ⚠ Google error page detected → fallback to original")
#                     return original
#                 return trans_str
#             except Exception as e:
#                 print(f"   ✗ Attempt {attempt+1} failed: {e}")
#                 time.sleep(6)
#         print(f"   ⚠ All attempts failed → using original")
#         return original


# class ColabLocalizationTool:
#     def __init__(self):
#         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
#         os.makedirs(self.json_dir, exist_ok=True)

#         self.CACHE_DIR = "/tmp/popular_po_cache"
#         os.makedirs(self.CACHE_DIR, exist_ok=True)
#         self.CACHE_DAYS = 7

#         self.PROTECTED_ENTITIES = {
#             "&copy;", "&COPY;",
#             "&reg;", "&REG;",
#             "&trade;", "&TRADE;",
#             "&euro;", "&nbsp;",
#             "&lt;", "&gt;", "&amp;"
#         }

#         self.PROTECTED_STRINGS = {
#             "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews", "Magnitude",
#             "CoverNews", "EnterNews", "Elegant Magazine", "DarkNews", "Newsium", "NewsCrunch",
#             "AF themes", "Get Started", "Upgrade to Pro", "Upgrade Now", "Starter Sites",
#             "Header Builder", "Footer Builder", "Dashboard", "Customize"
#         }

#         self._BAD_TRANSLATION_PATTERNS = [
#             r"error\s*5\d{2}",
#             r"that’s an error",
#             r"please try again later",
#             r"that’s all we know",
#             r"\!\!150[0-9]",
#             r"unusual traffic",
#             r"server error",
#             r"<html",
#             r"<!doctype",
#             r"&copy\b(?![;])", r"&reg\b(?![;])", r"&trade\b(?![;])",
#             r"&copia", r"&कॉपी", r"&कोपी", r"et copie;", r"&cópia;"
#         ]

#         # More aggressive placeholder regex — captures more format specifiers including %1$s, %u, %x, %e, etc.
#         self.placeholder_regex = re.compile(r"(%(?:\d+\$)?[sdifuxXeEgGcCr])|\{[^}]*\}")

#         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")

#         self._counts = {
#             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
#             "reused_zip": 0, "reused_json": 0, "translated_google": 0, "protected": 0,
#             "skipped_bad": 0, "saved_edits": 0, "skipped_protected": 0,
#             "placeholder_preserved": 0, "placeholder_fixed": 0  # tracks duplicate/junk fixes
#         }
#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);",
#             "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);",
#             "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
#             "ar": "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);",
#             "nl": "nplurals=2; plural=(n != 1);",
#             "it": "nplurals=2; plural=(n != 1);",
#             "ja": "nplurals=1; plural=0;",
#             "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);",
#         }

#         self.LANGUAGE_PRIORITY = [
#             "en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"
#         ]

#         self.POPULAR_THEMES_FALLBACK = [
#             "astra", "neve", "generatepress", "oceanwp", "kadence",
#             "blocksy", "hello-elementor", "sydney", "hestia", "zakra",
#         ]

#     def _display_status(self, message):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message):
#         print(f"\n--- ERROR: {message} ---")

#     def _is_bad_translation(self, text: str) -> bool:
#         if not text:
#             return False
#         text_lower = text.lower()
#         return any(re.search(pat, text_lower) for pat in self._BAD_TRANSLATION_PATTERNS)

#     def _is_broken_entity(self, text: str) -> bool:
#         text_lower = text.lower()
#         broken_patterns = [
#             r"&copy\b(?![;])", r"&reg\b(?![;])", r"&trade\b(?![;])",
#             r"&copia", r"&कॉपी", r"&कोपी", r"et copie;", r"&cópia;"
#         ]
#         return any(re.search(pat, text_lower) for pat in broken_patterns)

#     def _should_skip_translation(self, original: str, translated: str = None) -> bool:
#         if any(entity in original for entity in self.PROTECTED_ENTITIES):
#             return True
#         if translated and self._is_broken_entity(translated):
#             return True
#         return False

#     def _is_likely_untranslated(self, original_text: str, translated_text: str) -> bool:
#         raw_orig = re.sub(r'PH_\d+_TOKEN', '', original_text).strip().lower()
#         raw_trans = re.sub(r'PH_\d+_TOKEN', '', translated_text).strip().lower()
#         return raw_orig == raw_trans

#     def _clean_translated_text(self, text: str) -> str:
#         if not text:
#             return ""
#         text = text.strip()
#         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
#         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
#         text = re.sub(r'\s+', ' ', text)
#         text = self._sanitize_for_php(text)
#         return text

#     def _sanitize_for_php(self, text: str) -> str:
#         if not text:
#             return text

#         # Remove known junk
#         text = text.replace('�', '')
#         text = text.replace('\u200B', '')
#         text = text.replace('\u200C', '')
#         text = text.replace('\u200D', '')
#         text = text.replace('\uFEFF', '')
#         text = text.replace('\x00', '')

#         text = ''.join(c for c in text if c.isprintable() or c in '\n\t\r')

#         # AGGRESSIVE FIXES — MULTI-PASS

#         # Pass 1: Collapse duplicated $s on any % placeholder
#         text = re.sub(r'(\%s)\$s+', r'\1', text)  # %s$s$s → %s, %1$s$s$s → %1$s

#         # Pass 2: Fix any % followed by non-standard chars (including Hindi)
#         text = re.sub(r'%[^sdf%1-9$]', '%s', text)  # any % followed by non-standard char → %s

#         # Pass 3: Force uppercase specifiers to lowercase ( %D → %d, %S → %s )
#         text = re.sub(r'%([DSF])', lambda m: '%' + m.group(1).lower(), text, flags=re.IGNORECASE)

#         # Pass 4: Collapse any repeated %s pattern
#         text = re.sub(r'(%s)+', '%s', text)

#         # Pass 5: Specific for Hindi/Nepali Devanagari corruption
#         text = re.sub(r'%[डफल्टमानविजेटक्षेत्रसथ]', '%s', text)

#         try:
#             text.encode('utf-8', errors='strict')
#         except UnicodeEncodeError:
#             text = text.encode('ascii', errors='ignore').decode('ascii')

#         return text.strip()

#     def _preserve_placeholders(self, original: str, translated: str) -> str:
#         orig_placeholders = self.placeholder_regex.findall(original)
#         if not orig_placeholders:
#             return self._sanitize_for_php(translated)

#         # Remove ALL placeholders from translated
#         trans_clean = self.placeholder_regex.sub('__PH__', translated)

#         # Re-insert EXACT original placeholders (in order)
#         for ph in orig_placeholders:
#             trans_clean = trans_clean.replace('__PH__', ph, 1)

#         # Run sanitizer **multiple times** for maximum cleanup
#         cleaned = self._sanitize_for_php(trans_clean)
#         cleaned = self._sanitize_for_php(cleaned)  # second pass
#         cleaned = self._sanitize_for_php(cleaned)  # third pass if needed

#         if cleaned != translated:
#             self._counts["placeholder_fixed"] += 1

#         return cleaned

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         orig_ph = self.placeholder_regex.findall(original)
#         trans_ph = self.placeholder_regex.findall(translated)
#         return orig_ph == trans_ph

#     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
#         key = (text, target_language)
#         if key in self._cache:
#             cached = self._cache[key]
#             if self._is_bad_translation(cached) or self._is_broken_entity(cached):
#                 self._counts["skipped_bad"] += 1
#                 return text
#             return cached
        
#         trans = self.translator_engine.translate_single(text, target_language)
#         result = self._sanitize_for_php(trans)
        
#         if self._is_bad_translation(result) or self._is_broken_entity(result):
#             self._counts["skipped_bad"] += 1
#             return text
        
#         self._cache[key] = result
#         memory[text] = result
#         return result

#     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
#         glossary_lookup = {}
#         short_terms = {}
#         if not csv_file_path or not os.path.exists(csv_file_path):
#             return glossary_lookup, short_terms

#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         if orig and trans:
#                             if self._should_skip_translation(orig, trans):
#                                 continue
#                             trans = self._preserve_placeholders(orig, trans)
#                             glossary_lookup[(orig, ctx)] = trans
#                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
#                                 short_terms[orig] = trans
#                 return glossary_lookup, short_terms
#             except:
#                 continue
#         return glossary_lookup, short_terms

#     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
#         lookup = {}
#         if not folder_path or not os.path.exists(folder_path):
#             return lookup

#         lang_pattern = f"-{lang_code}."
#         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

#         skipped = 0
#         for root, _, files in os.walk(folder_path):
#             for file in files:
#                 if file.startswith('._') or file.startswith('__MACOSX'):
#                     continue
#                 if file.lower().endswith('.po') and lang_pattern in file.lower():
#                     file_path = os.path.join(root, file)
#                     try:
#                         detection = from_path(file_path).best()
#                         encoding = detection.encoding if detection else 'utf-8'
#                         po = polib.pofile(file_path, encoding=encoding)
#                         for entry in po:
#                             if entry.msgstr.strip():
#                                 cleaned = self._clean_translated_text(entry.msgstr.strip())
#                                 cleaned = self._preserve_placeholders(entry.msgid, cleaned)
#                                 if self._should_skip_translation(entry.msgid, cleaned):
#                                     skipped += 1
#                                     continue
#                                 if self._placeholders_are_valid(entry.msgid, cleaned):
#                                     key = (entry.msgid, entry.msgctxt or '')
#                                     lookup[key] = cleaned
#                         print(f"   ✓ Loaded: {file} ({len(lookup)} good, skipped {skipped} bad/broken)")
#                     except Exception as e:
#                         print(f"   ✗ Failed: {file} ({e})")
#         if skipped > 0:
#             print(f"   ⚠ Skipped {skipped} bad/broken translations from ZIP")
#         return lookup

#     def _download_wporg_po(self, theme_slug: str, lang_code: str, use_cache: bool = True) -> Dict[Tuple[str, str], str]:
#         cache_path = os.path.join(self.CACHE_DIR, f"{theme_slug}-{lang_code}.po")
        
#         if use_cache and os.path.exists(cache_path):
#             age_days = (time.time() - os.path.getmtime(cache_path)) / (24 * 3600)
#             if age_days < self.CACHE_DAYS:
#                 print(f"   ✓ Using weekly cached .po for {theme_slug}/{lang_code}")
#                 return self._load_single_po(cache_path)
        
#         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
#             'Accept': 'text/plain,*/*;q=0.9',
#             'Referer': 'https://translate.wordpress.org/',
#         }
#         try:
#             response = requests.get(url, timeout=30, headers=headers)
#             if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
#                 if use_cache:
#                     with open(cache_path, 'w', encoding='utf-8') as f:
#                         f.write(response.text)
#                     print(f"   ✓ Downloaded & cached {theme_slug}/{lang_code}")
                
#                 temp_path = os.path.join("/tmp", f"temp-{theme_slug}-{lang_code}.po")
#                 with open(temp_path, 'w', encoding='utf-8') as f:
#                     f.write(response.text)
#                 lookup = self._load_single_po(temp_path)
#                 os.remove(temp_path)
#                 return lookup
#             else:
#                 print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
#         except Exception as e:
#             print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
#         return {}

#     def _load_single_po(self, file_path: str) -> Dict[Tuple[str, str], str]:
#         lookup = {}
#         if not os.path.exists(file_path):
#             return lookup
#         try:
#             detection = from_path(file_path).best()
#             encoding = detection.encoding if detection else 'utf-8'
#             po = polib.pofile(file_path, encoding=encoding)
#             for entry in po:
#                 if entry.msgstr.strip():
#                     cleaned = self._clean_translated_text(entry.msgstr.strip())
#                     cleaned = self._preserve_placeholders(entry.msgid, cleaned)
#                     if self._should_skip_translation(entry.msgid, cleaned):
#                         continue
#                     if self._placeholders_are_valid(entry.msgid, cleaned):
#                         lookup[(entry.msgid, entry.msgctxt or '')] = cleaned
#             print(f"   ✓ Loaded cached/single PO ({len(lookup)} strings)")
#         except Exception as e:
#             print(f"   ✗ Failed to load PO: {e}")
#         return lookup

#     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
#                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str, user_override: str = None):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''
#         key = (msgid, msgctxt)
#         full_key = f"{msgctxt}||{msgid}"

#         self._counts["total"] += 1

#         if self.placeholder_regex.search(msgid):
#             self._counts["placeholder_preserved"] += 1

#             if user_override is not None and user_override.strip():
#                 clean = self._preserve_placeholders(msgid, user_override)
#                 self._counts["saved_edits"] += 1
#                 return clean, "User Edited (placeholders preserved)"

#             if key in wporg_lookup:
#                 trans = self._preserve_placeholders(msgid, wporg_lookup[key])
#                 self._counts["reused_wporg"] += 1
#                 return trans, "WP.org (placeholders preserved)"

#             if gloss := glossary_lookup.get(key):
#                 trans = self._preserve_placeholders(msgid, gloss)
#                 self._counts["reused_glossary"] += 1
#                 return trans, "Glossary (placeholders preserved)"

#             if existing := existing_po_lookup.get(key):
#                 trans = self._preserve_placeholders(msgid, existing)
#                 self._counts["reused_zip"] += 1
#                 return trans, "Existing PO (placeholders preserved)"

#             if full_key in memory and isinstance((val := memory[full_key]), list) and val:
#                 text = val[0]
#                 if text.startswith(("★", "○")):
#                     cleaned = self._preserve_placeholders(msgid, text[2:].strip())
#                     self._counts["reused_json"] += 1
#                     return cleaned, "Global JSON (placeholders preserved)"

#             fb = self._fallback_translate(memory, msgid, target_language)
#             fb = self._preserve_placeholders(msgid, fb)
#             self._counts["translated_google"] += 1
#             return fb, "Google (placeholders preserved)"

#         if user_override is not None and user_override.strip():
#             self._counts["saved_edits"] += 1
#             return user_override.strip(), "User Edited"

#         if msgid in self.PROTECTED_STRINGS:
#             self._counts["protected"] += 1
#             return msgid, "Protected String"

#         if key in wporg_lookup:
#             self._counts["reused_wporg"] += 1
#             return wporg_lookup[key], "WP.org Official"

#         if gloss := glossary_lookup.get(key):
#             self._counts["reused_glossary"] += 1
#             return gloss, "Glossary"

#         if existing := existing_po_lookup.get(key):
#             self._counts["reused_zip"] += 1
#             return existing, "Existing PO"

#         if full_key in memory and isinstance((val := memory[full_key]), list) and val:
#             text = val[0]
#             if text.startswith(("★", "○")):
#                 self._counts["reused_json"] += 1
#                 return text[2:].strip(), "Global JSON"

#         fb = self._fallback_translate(memory, msgid, target_language)
#         self._counts["translated_google"] += 1

#         if short_terms:
#             final = fb
#             for term, replacement in short_terms.items():
#                 pattern = rf'\b{re.escape(term)}\b'
#                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
#                 if new_text != final:
#                     final = new_text
#                     self._counts["reused_glossary"] += 1
#             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

#         return fb, "Google Translate"

#     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
#             use_wporg=False, user_edits=None):
#         self._display_status("Starting Localization Tool")

#         if zip_paths_by_lang is None:
#             zip_paths_by_lang = {}
#         if user_edits is None:
#             user_edits = {}

#         project_dir = output_dir or os.path.dirname(pot_path)
#         os.makedirs(project_dir, exist_ok=True)

#         valid_langs = [code for code, _ in settings.LANGUAGES]
#         selected_langs = [lang for lang in target_langs if lang in valid_langs]

#         if not selected_langs:
#             self._display_error("No valid languages")
#             return False

#         def priority_key(lang):
#             try:
#                 return self.LANGUAGE_PRIORITY.index(lang)
#             except ValueError:
#                 return len(self.LANGUAGE_PRIORITY)

#         target_languages = sorted(selected_langs, key=priority_key)

#         self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

#         pot_filename = os.path.basename(pot_path)
#         raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
#         raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
#         raw_name = raw_name.replace(' ', '-').strip('-').lower()

#         af_themes_mapping = {
#             "chromenews": "chromenews",
#             "reviewnews": "reviewnews",
#             "morenews": "morenews",
#             "newsever": "newsever",
#             "broadnews": "broadnews",
#             "magnitude": "magnitude",
#             "covernews": "covernews",
#             "enternews": "enternews",
#             "newsium": "newsium",
#             "darknews": "darknews",
#             "newscrunch": "newscrunch",
#             "elegantmagazine": "elegant-magazine",
#         }

#         theme_slug = af_themes_mapping.get(raw_name, raw_name)
#         if not theme_slug or len(theme_slug) < 3:
#             theme_slug = "unknown-theme"

#         self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

#         try:
#             pot_file = polib.pofile(pot_path)

#             existing_by_lang = {}
#             for lang in target_languages:
#                 folder = zip_paths_by_lang.get(lang)
#                 if folder:
#                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
#                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
#                 else:
#                     existing_by_lang[lang] = {}

#             wporg_by_lang = {}
#             if use_wporg:
#                 self._display_status("Downloading official + cached popular themes translations...")
#                 for lang in target_languages:
#                     primary = self._download_wporg_po(theme_slug, lang, use_cache=False)
                    
#                     fallback = {}
#                     self._display_status(f"   Loading popular themes (weekly cache) for {lang.upper()}")
#                     for popular in self.POPULAR_THEMES_FALLBACK:
#                         temp = self._download_wporg_po(popular, lang, use_cache=True)
#                         for k, v in temp.items():
#                             if k not in fallback:
#                                 fallback[k] = v
                    
#                     combined = primary.copy()
#                     combined.update(fallback)
#                     wporg_by_lang[lang] = combined
#                     print(f"   → Total strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular cached: {len(fallback)})")

#             changes_made = False

#             for target_language in target_languages:
#                 self._counts = {k: 0 for k in self._counts}

#                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
#                 translations_memory = {}
#                 if os.path.exists(jed_path):
#                     try:
#                         with open(jed_path, 'r', encoding='utf-8') as f:
#                             data = json.load(f)
#                             skipped = 0
#                             for k, v in data.items():
#                                 if k:
#                                     if isinstance(v, list) and v:
#                                         val = v[0]
#                                         if val.startswith(("★", "○")):
#                                             cleaned_val = val[2:].strip()
#                                             if self._should_skip_translation(k.split("||")[-1], cleaned_val):
#                                                 skipped += 1
#                                                 continue
#                                             translations_memory[k] = [f"{val[0]} {cleaned_val}"]
#                                         else:
#                                             translations_memory[k] = v
#                             if skipped > 0:
#                                 self._display_status(f"Skipped {skipped} bad/broken translations from old JSON")
#                     except Exception as e:
#                         self._display_error(f"Failed to load JSON: {e}")

#                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
#                 glossary = glossary_data[0]
#                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

#                 existing_lookup = existing_by_lang.get(target_language, {})
#                 wporg_lookup = wporg_by_lang.get(target_language, {})

#                 version = 1
#                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
#                     version += 1

#                 po = polib.POFile()
#                 po.metadata = {
#                     'Project-Id-Version': '1.0',
#                     'Language': target_language,
#                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
#                     'X-Generator': 'Advanced Localization Tool 2026',
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     user_override = user_edits.get(entry.msgid, None) if user_edits else None

#                     if entry.msgid_plural:
#                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
#                         clean_plurals = {i: self._preserve_placeholders(entry.msgid, v.strip()) for i, v in plurals.items()}
#                         po.append(polib.POEntry(
#                             msgid=entry.msgid,
#                             msgid_plural=entry.msgid_plural,
#                             msgstr_plural=clean_plurals,
#                             msgctxt=entry.msgctxt,
#                         ))
#                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
#                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
#                     else:
#                         translated, source = self._process_translation(
#                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language, user_override=user_override
#                         )
#                         clean = self._preserve_placeholders(entry.msgid, translated.strip())
#                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
#                         symbol = "★" if "Google" not in source else "○"
#                         prefixed = f"{symbol} {clean}"
#                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

#                         if user_override is not None and user_override.strip() != clean:
#                             changes_made = True

#                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 translations_memory[""] = {"lang": target_language}
#                 with open(jed_path, 'w', encoding='utf-8') as f:
#                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

#                 self._display_status(f"{target_language.upper()} v{version} complete")
#                 for k, v in self._counts.items():
#                     if v:
#                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")
#                 if self._counts["placeholder_fixed"] > 0:
#                     self._display_status(f"   ⚠ Fixed {self._counts['placeholder_fixed']} corrupted/duplicated placeholders!")

#             if changes_made:
#                 self._display_status("Changes saved successfully!")
#             else:
#                 self._display_status("No changes detected (check if you edited non-protected strings)")

#             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
#             return True

#         except Exception as e:
#             import traceback
#             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
#             return False

#     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
#         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
#         npl = 2
#         if "nplurals=1" in header:
#             npl = 1
#         elif "nplurals=3" in header:
#             npl = 3
#         elif "nplurals=6" in header:
#             npl = 6

#         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
#         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
#             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

#         results = {}
#         singular = self._fallback_translate(memory, entry.msgid, target_language)
#         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

#         results[0] = singular
#         for i in range(1, npl):
#             results[i] = plural

#         self._counts["translated_google"] += 2
#         return results






# # # # localizationtool/localization_logic.py
# # # # FINAL, COMPLETE, COPY‑PASTE VERSION — Safe, Stable, Ready to Test

# # # import polib
# # # import csv
# # # import os
# # # import re
# # # import json
# # # import requests
# # # import time
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings
# # # from charset_normalizer import from_path
# # # from deep_translator import GoogleTranslator as _GoogleTranslator


# # # class GoogleTranslatorEngine:
# # #     _BLOCK_KEYWORDS = [
# # #         "error 500", "504", "that’s an error", "please try again later",
# # #         "that’s all we know", "1500", "1504", "unusual traffic",
# # #         "server error", "blocked", "captcha", "<html", "<!doctype"
# # #     ]

# # #     def translate_single(self, text: str, target_lang: str) -> str:
# # #         original = text
# # #         for attempt in range(5):
# # #             try:
# # #                 translator = _GoogleTranslator(source="auto", target=target_lang)
# # #                 trans = translator.translate(text)
# # #                 time.sleep(3.5)

# # #                 trans_str = str(trans).strip()
# # #                 if any(kw.lower() in trans_str.lower() for kw in self._BLOCK_KEYWORDS):
# # #                     return original
# # #                 return trans_str
# # #             except Exception:
# # #                 time.sleep(6)
# # #         return original


# # # class ColabLocalizationTool:
# # #     def __init__(self):
# # #         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
# # #         os.makedirs(self.json_dir, exist_ok=True)

# # #         self.CACHE_DIR = "/tmp/popular_po_cache"
# # #         os.makedirs(self.CACHE_DIR, exist_ok=True)
# # #         self.CACHE_DAYS = 7

# # #         self.PROTECTED_ENTITIES = {
# # #             "&copy;", "&reg;", "&trade;", "&euro;", "&nbsp;",
# # #             "&lt;", "&gt;", "&amp;"
# # #         }

# # #         self.PROTECTED_STRINGS = {
# # #             "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews",
# # #             "Magnitude", "CoverNews", "EnterNews", "Elegant Magazine",
# # #             "DarkNews", "Newsium", "NewsCrunch", "AF themes"
# # #         }

# # #         self._BAD_TRANSLATION_PATTERNS = [
# # #             r"error\s*5\d{2}", r"that’s an error", r"please try again later",
# # #             r"that’s all we know", r"\!\!150[0-9]", r"unusual traffic",
# # #             r"server error", r"<html", r"<!doctype", 
# # #             r"&copy\b(?!;)", r"&reg\b(?!;)", r"&trade\b(?!;)"
# # #         ]

# # #         # Only real PHP‑style placeholders
# # #         self.placeholder_regex = re.compile(r"%(?:\d+\$)?[sdifuxXeEgGcCr]")

# # #         self._counts = {
# # #             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
# # #             "reused_zip": 0, "reused_json": 0, "translated_google": 0,
# # #             "protected": 0, "skipped_bad": 0, "saved_edits": 0,
# # #             "skipped_protected": 0, "placeholder_preserved": 0,
# # #             "placeholder_fixed": 0
# # #         }

# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine = GoogleTranslatorEngine()

# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# # #             "ar": "nplurals=6; plural=(n==0?0:n==1?1:n==2?2:n%100>=3&&n%100<=10?3:n%100>=11?4:5);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;"
# # #         }

# # #         self.LANGUAGE_PRIORITY = [
# # #             "en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"
# # #         ]

# # #         self.POPULAR_THEMES_FALLBACK = [
# # #             "astra", "neve", "generatepress", "oceanwp", "kadence",
# # #             "blocksy", "hello-elementor", "sydney", "hestia", "zakra"
# # #         ]

# # #     def _display_status(self, message: str):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message: str):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _is_bad_translation(self, text: str) -> bool:
# # #         if not text:
# # #             return False
# # #         text_lower = text.lower()
# # #         return any(re.search(pat, text_lower) for pat in self._BAD_TRANSLATION_PATTERNS)

# # #     def _should_skip_translation(self, original: str, translated: str = None) -> bool:
# # #         if any(ent in original for ent in self.PROTECTED_ENTITIES):
# # #             return True
# # #         if translated and self._is_bad_translation(translated):
# # #             return True
# # #         return False

# # #     def _sanitize_for_php(self, text: str) -> str:
# # #         if not text:
# # #             return text

# # #         # Remove junk
# # #         for junk in ['�', '\u200B', '\uFEFF', '\x00']:
# # #             text = text.replace(junk, '')

# # #         # Escape raw '%' not part of placeholders
# # #         text = re.sub(r'%(?!\d*\$?[sdifuxXeEgGcCr])', '%%', text)

# # #         # Normalize uppercase placeholders
# # #         text = re.sub(r'%([DSF])', lambda m: '%' + m.group(1).lower(), text)

# # #         # Fix double escapes
# # #         text = re.sub(r'%%+', '%%', text)

# # #         return text.strip()

# # #     def _preserve_placeholders(self, original: str, translated: str) -> str:
# # #         orig_ph = self.placeholder_regex.findall(original)
# # #         if not orig_ph:
# # #             return self._sanitize_for_php(translated)

# # #         temp = self.placeholder_regex.sub("<<PH>>", translated)
# # #         for ph in orig_ph:
# # #             temp = temp.replace("<<PH>>", ph, 1)

# # #         return self._sanitize_for_php(temp)

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         return sorted(self.placeholder_regex.findall(original)) == sorted(self.placeholder_regex.findall(translated))

# # #     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
# # #         key = (text, target_language)
# # #         if key in self._cache:
# # #             cached = self._cache[key]
# # #             if self._is_bad_translation(cached):
# # #                 self._counts["skipped_bad"] += 1
# # #                 return text
# # #             return cached

# # #         translated = self.translator_engine.translate_single(text, target_language)
# # #         safe_text = self._sanitize_for_php(translated)

# # #         if self._is_bad_translation(safe_text):
# # #             self._counts["skipped_bad"] += 1
# # #             return text

# # #         self._cache[key] = safe_text
# # #         memory[text] = safe_text
# # #         return safe_text

# # #     # ==== EXISTING METHODS BELOW (NO CHANGES NEEDED) ====
# # #     # _parse_glossary_csv, _load_pos_from_folder, _download_wporg_po,
# # #     # _load_single_po, _process_translation, _pluralize_entry,
# # #     # run ...

# # #     # (Due to length, they remain unchanged from your original;
# # #     # if you need the *rest* inserted here for a full one‑file copy,
# # #     # I can append them — just ask.)





# # #     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
# # #         glossary_lookup = {}
# # #         short_terms = {}
# # #         if not csv_file_path or not os.path.exists(csv_file_path):
# # #             return glossary_lookup, short_terms

# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         if orig and trans:
# # #                             if self._should_skip_translation(orig, trans):
# # #                                 continue
# # #                             trans = self._preserve_placeholders(orig, trans)
# # #                             glossary_lookup[(orig, ctx)] = trans
# # #                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
# # #                                 short_terms[orig] = trans
# # #                 return glossary_lookup, short_terms
# # #             except:
# # #                 continue
# # #         return glossary_lookup, short_terms

# # #     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
# # #         lookup = {}
# # #         if not folder_path or not os.path.exists(folder_path):
# # #             return lookup

# # #         lang_pattern = f"-{lang_code}."
# # #         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

# # #         skipped = 0
# # #         for root, _, files in os.walk(folder_path):
# # #             for file in files:
# # #                 if file.startswith('._') or file.startswith('__MACOSX'):
# # #                     continue
# # #                 if file.lower().endswith('.po') and lang_pattern in file.lower():
# # #                     file_path = os.path.join(root, file)
# # #                     try:
# # #                         detection = from_path(file_path).best()
# # #                         encoding = detection.encoding if detection else 'utf-8'
# # #                         po = polib.pofile(file_path, encoding=encoding)
# # #                         for entry in po:
# # #                             if entry.msgstr.strip():
# # #                                 cleaned = self._clean_translated_text(entry.msgstr.strip())
# # #                                 cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# # #                                 if self._should_skip_translation(entry.msgid, cleaned):
# # #                                     skipped += 1
# # #                                     continue
# # #                                 if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                                     key = (entry.msgid, entry.msgctxt or '')
# # #                                     lookup[key] = cleaned
# # #                         print(f"   ✓ Loaded: {file} ({len(lookup)} good, skipped {skipped} bad/broken)")
# # #                     except Exception as e:
# # #                         print(f"   ✗ Failed: {file} ({e})")
# # #         if skipped > 0:
# # #             print(f"   ⚠ Skipped {skipped} bad/broken translations from ZIP")
# # #         return lookup

# # #     def _download_wporg_po(self, theme_slug: str, lang_code: str, use_cache: bool = True) -> Dict[Tuple[str, str], str]:
# # #         cache_path = os.path.join(self.CACHE_DIR, f"{theme_slug}-{lang_code}.po")
        
# # #         if use_cache and os.path.exists(cache_path):
# # #             age_days = (time.time() - os.path.getmtime(cache_path)) / (24 * 3600)
# # #             if age_days < self.CACHE_DAYS:
# # #                 print(f"   ✓ Using weekly cached .po for {theme_slug}/{lang_code}")
# # #                 return self._load_single_po(cache_path)
        
# # #         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
# # #         headers = {
# # #             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
# # #             'Accept': 'text/plain,*/*;q=0.9',
# # #             'Referer': 'https://translate.wordpress.org/',
# # #         }
# # #         try:
# # #             response = requests.get(url, timeout=30, headers=headers)
# # #             if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
# # #                 if use_cache:
# # #                     with open(cache_path, 'w', encoding='utf-8') as f:
# # #                         f.write(response.text)
# # #                     print(f"   ✓ Downloaded & cached {theme_slug}/{lang_code}")
                
# # #                 temp_path = os.path.join("/tmp", f"temp-{theme_slug}-{lang_code}.po")
# # #                 with open(temp_path, 'w', encoding='utf-8') as f:
# # #                     f.write(response.text)
# # #                 lookup = self._load_single_po(temp_path)
# # #                 os.remove(temp_path)
# # #                 return lookup
# # #             else:
# # #                 print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
# # #         except Exception as e:
# # #             print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
# # #         return {}

# # #     def _load_single_po(self, file_path: str) -> Dict[Tuple[str, str], str]:
# # #         lookup = {}
# # #         if not os.path.exists(file_path):
# # #             return lookup
# # #         try:
# # #             detection = from_path(file_path).best()
# # #             encoding = detection.encoding if detection else 'utf-8'
# # #             po = polib.pofile(file_path, encoding=encoding)
# # #             for entry in po:
# # #                 if entry.msgstr.strip():
# # #                     cleaned = self._clean_translated_text(entry.msgstr.strip())
# # #                     cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# # #                     if self._should_skip_translation(entry.msgid, cleaned):
# # #                         continue
# # #                     if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                         lookup[(entry.msgid, entry.msgctxt or '')] = cleaned
# # #             print(f"   ✓ Loaded cached/single PO ({len(lookup)} strings)")
# # #         except Exception as e:
# # #             print(f"   ✗ Failed to load PO: {e}")
# # #         return lookup

# # #     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
# # #                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str, user_override: str = None):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key = (msgid, msgctxt)
# # #         full_key = f"{msgctxt}||{msgid}"

# # #         self._counts["total"] += 1

# # #         if self.placeholder_regex.search(msgid):
# # #             self._counts["placeholder_preserved"] += 1

# # #             if user_override is not None and user_override.strip():
# # #                 clean = self._preserve_placeholders(msgid, user_override)
# # #                 self._counts["saved_edits"] += 1
# # #                 return clean, "User Edited (placeholders preserved)"

# # #             if key in wporg_lookup:
# # #                 trans = self._preserve_placeholders(msgid, wporg_lookup[key])
# # #                 self._counts["reused_wporg"] += 1
# # #                 return trans, "WP.org (placeholders preserved)"

# # #             if gloss := glossary_lookup.get(key):
# # #                 trans = self._preserve_placeholders(msgid, gloss)
# # #                 self._counts["reused_glossary"] += 1
# # #                 return trans, "Glossary (placeholders preserved)"

# # #             if existing := existing_po_lookup.get(key):
# # #                 trans = self._preserve_placeholders(msgid, existing)
# # #                 self._counts["reused_zip"] += 1
# # #                 return trans, "Existing PO (placeholders preserved)"

# # #             if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# # #                 text = val[0]
# # #                 if text.startswith(("★", "○")):
# # #                     cleaned = self._preserve_placeholders(msgid, text[2:].strip())
# # #                     self._counts["reused_json"] += 1
# # #                     return cleaned, "Global JSON (placeholders preserved)"

# # #             fb = self._fallback_translate(memory, msgid, target_language)
# # #             fb = self._preserve_placeholders(msgid, fb)
# # #             self._counts["translated_google"] += 1
# # #             return fb, "Google (placeholders preserved)"

# # #         if user_override is not None and user_override.strip():
# # #             self._counts["saved_edits"] += 1
# # #             return user_override.strip(), "User Edited"

# # #         if msgid in self.PROTECTED_STRINGS:
# # #             self._counts["protected"] += 1
# # #             return msgid, "Protected String"

# # #         if key in wporg_lookup:
# # #             self._counts["reused_wporg"] += 1
# # #             return wporg_lookup[key], "WP.org Official"

# # #         if gloss := glossary_lookup.get(key):
# # #             self._counts["reused_glossary"] += 1
# # #             return gloss, "Glossary"

# # #         if existing := existing_po_lookup.get(key):
# # #             self._counts["reused_zip"] += 1
# # #             return existing, "Existing PO"

# # #         if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# # #             text = val[0]
# # #             if text.startswith(("★", "○")):
# # #                 self._counts["reused_json"] += 1
# # #                 return text[2:].strip(), "Global JSON"

# # #         fb = self._fallback_translate(memory, msgid, target_language)
# # #         self._counts["translated_google"] += 1

# # #         if short_terms:
# # #             final = fb
# # #             for term, replacement in short_terms.items():
# # #                 pattern = rf'\b{re.escape(term)}\b'
# # #                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
# # #                 if new_text != final:
# # #                     final = new_text
# # #                     self._counts["reused_glossary"] += 1
# # #             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

# # #         return fb, "Google Translate"

# # #     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
# # #             use_wporg=False, user_edits=None):
# # #         self._display_status("Starting Localization Tool")

# # #         if zip_paths_by_lang is None:
# # #             zip_paths_by_lang = {}
# # #         if user_edits is None:
# # #             user_edits = {}

# # #         project_dir = output_dir or os.path.dirname(pot_path)
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         valid_langs = [code for code, _ in settings.LANGUAGES]
# # #         selected_langs = [lang for lang in target_langs if lang in valid_langs]

# # #         if not selected_langs:
# # #             self._display_error("No valid languages")
# # #             return False

# # #         def priority_key(lang):
# # #             try:
# # #                 return self.LANGUAGE_PRIORITY.index(lang)
# # #             except ValueError:
# # #                 return len(self.LANGUAGE_PRIORITY)

# # #         target_languages = sorted(selected_langs, key=priority_key)

# # #         self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

# # #         pot_filename = os.path.basename(pot_path)
# # #         raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
# # #         raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
# # #         raw_name = raw_name.replace(' ', '-').strip('-').lower()

# # #         af_themes_mapping = {
# # #             "chromenews": "chromenews",
# # #             "reviewnews": "reviewnews",
# # #             "morenews": "morenews",
# # #             "newsever": "newsever",
# # #             "broadnews": "broadnews",
# # #             "magnitude": "magnitude",
# # #             "covernews": "covernews",
# # #             "enternews": "enternews",
# # #             "newsium": "newsium",
# # #             "darknews": "darknews",
# # #             "newscrunch": "newscrunch",
# # #             "elegantmagazine": "elegant-magazine",
# # #         }

# # #         theme_slug = af_themes_mapping.get(raw_name, raw_name)
# # #         if not theme_slug or len(theme_slug) < 3:
# # #             theme_slug = "unknown-theme"

# # #         self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

# # #         try:
# # #             pot_file = polib.pofile(pot_path)

# # #             existing_by_lang = {}
# # #             for lang in target_languages:
# # #                 folder = zip_paths_by_lang.get(lang)
# # #                 if folder:
# # #                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
# # #                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
# # #                 else:
# # #                     existing_by_lang[lang] = {}

# # #             wporg_by_lang = {}
# # #             if use_wporg:
# # #                 self._display_status("Downloading official + cached popular themes translations...")
# # #                 for lang in target_languages:
# # #                     primary = self._download_wporg_po(theme_slug, lang, use_cache=False)
                    
# # #                     fallback = {}
# # #                     self._display_status(f"   Loading popular themes (weekly cache) for {lang.upper()}")
# # #                     for popular in self.POPULAR_THEMES_FALLBACK:
# # #                         temp = self._download_wporg_po(popular, lang, use_cache=True)
# # #                         for k, v in temp.items():
# # #                             if k not in fallback:
# # #                                 fallback[k] = v
                    
# # #                     combined = primary.copy()
# # #                     combined.update(fallback)
# # #                     wporg_by_lang[lang] = combined
# # #                     print(f"   → Total strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular cached: {len(fallback)})")

# # #             changes_made = False

# # #             for target_language in target_languages:
# # #                 self._counts = {k: 0 for k in self._counts}

# # #                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
# # #                 translations_memory = {}
# # #                 if os.path.exists(jed_path):
# # #                     try:
# # #                         with open(jed_path, 'r', encoding='utf-8') as f:
# # #                             data = json.load(f)
# # #                             skipped = 0
# # #                             for k, v in data.items():
# # #                                 if k:
# # #                                     if isinstance(v, list) and v:
# # #                                         val = v[0]
# # #                                         if val.startswith(("★", "○")):
# # #                                             cleaned_val = val[2:].strip()
# # #                                             if self._should_skip_translation(k.split("||")[-1], cleaned_val):
# # #                                                 skipped += 1
# # #                                                 continue
# # #                                             translations_memory[k] = [f"{val[0]} {cleaned_val}"]
# # #                                         else:
# # #                                             translations_memory[k] = v
# # #                             if skipped > 0:
# # #                                 self._display_status(f"Skipped {skipped} bad/broken translations from old JSON")
# # #                     except Exception as e:
# # #                         self._display_error(f"Failed to load JSON: {e}")

# # #                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
# # #                 glossary = glossary_data[0]
# # #                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

# # #                 existing_lookup = existing_by_lang.get(target_language, {})
# # #                 wporg_lookup = wporg_by_lang.get(target_language, {})

# # #                 version = 1
# # #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# # #                     version += 1

# # #                 po = polib.POFile()
# # #                 po.metadata = {
# # #                     'Project-Id-Version': '1.0',
# # #                     'Language': target_language,
# # #                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
# # #                     'X-Generator': 'Advanced Localization Tool 2026',
# # #                 }

# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue

# # #                     user_override = user_edits.get(entry.msgid, None) if user_edits else None

# # #                     if entry.msgid_plural:
# # #                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
# # #                         clean_plurals = {i: self._preserve_placeholders(entry.msgid, v.strip()) for i, v in plurals.items()}
# # #                         po.append(polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgid_plural=entry.msgid_plural,
# # #                             msgstr_plural=clean_plurals,
# # #                             msgctxt=entry.msgctxt,
# # #                         ))
# # #                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
# # #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
# # #                     else:
# # #                         translated, source = self._process_translation(
# # #                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language, user_override=user_override
# # #                         )
# # #                         clean = self._preserve_placeholders(entry.msgid, translated.strip())
# # #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
# # #                         symbol = "★" if "Google" not in source else "○"
# # #                         prefixed = f"{symbol} {clean}"
# # #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

# # #                         if user_override is not None and user_override.strip() != clean:
# # #                             changes_made = True

# # #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# # #                 out_mo = out_po.replace('.po', '.mo')
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)

# # #                 translations_memory[""] = {"lang": target_language}
# # #                 with open(jed_path, 'w', encoding='utf-8') as f:
# # #                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

# # #                 self._display_status(f"{target_language.upper()} v{version} complete")
# # #                 for k, v in self._counts.items():
# # #                     if v:
# # #                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")
# # #                 if self._counts["placeholder_fixed"] > 0:
# # #                     self._display_status(f"   ⚠ Fixed {self._counts['placeholder_fixed']} corrupted/duplicated placeholders!")

# # #             if changes_made:
# # #                 self._display_status("Changes saved successfully!")
# # #             else:
# # #                 self._display_status("No changes detected (check if you edited non-protected strings)")

# # #             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
# # #             return True

# # #         except Exception as e:
# # #             import traceback
# # #             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
# # #             return False

# # #     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
# # #         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
# # #         npl = 2
# # #         if "nplurals=1" in header:
# # #             npl = 1
# # #         elif "nplurals=3" in header:
# # #             npl = 3
# # #         elif "nplurals=6" in header:
# # #             npl = 6

# # #         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
# # #         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
# # #             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

# # #         results = {}
# # #         singular = self._fallback_translate(memory, entry.msgid, target_language)
# # #         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

# # #         results[0] = singular
# # #         for i in range(1, npl):
# # #             results[i] = plural

# # #         self._counts["translated_google"] += 2
# # #         return results







# # # localizationtool/localization_logic.py thikc cha yo code tara eauta ma %% cha
# # # FINAL, COMPLETE, COPY‑PASTE VERSION — Safe, Stable, Ready to Test

# # # import polib
# # # import csv
# # # import os
# # # import re
# # # import json
# # # import requests
# # # import time
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings
# # # from charset_normalizer import from_path
# # # from deep_translator import GoogleTranslator as _GoogleTranslator


# # # class GoogleTranslatorEngine:
# # #     _BLOCK_KEYWORDS = [
# # #         "error 500", "504", "that’s an error", "please try again later",
# # #         "that’s all we know", "1500", "1504", "unusual traffic",
# # #         "server error", "blocked", "captcha", "<html", "<!doctype"
# # #     ]

# # #     def translate_single(self, text: str, target_lang: str) -> str:
# # #         original = text
# # #         for attempt in range(5):
# # #             try:
# # #                 translator = _GoogleTranslator(source="auto", target=target_lang)
# # #                 trans = translator.translate(text)
# # #                 time.sleep(3.5)

# # #                 trans_str = str(trans).strip()
# # #                 if any(kw.lower() in trans_str.lower() for kw in self._BLOCK_KEYWORDS):
# # #                     return original
# # #                 return trans_str
# # #             except Exception:
# # #                 time.sleep(6)
# # #         return original


# # # class ColabLocalizationTool:
# # #     def __init__(self):
# # #         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
# # #         os.makedirs(self.json_dir, exist_ok=True)

# # #         self.CACHE_DIR = "/tmp/popular_po_cache"
# # #         os.makedirs(self.CACHE_DIR, exist_ok=True)
# # #         self.CACHE_DAYS = 7

# # #         self.PROTECTED_ENTITIES = {
# # #             "&copy;", "&reg;", "&trade;", "&euro;", "&nbsp;",
# # #             "&lt;", "&gt;", "&amp;"
# # #         }

# # #         self.PROTECTED_STRINGS = {
# # #             "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews",
# # #             "Magnitude", "CoverNews", "EnterNews", "Elegant Magazine",
# # #             "DarkNews", "Newsium", "NewsCrunch", "AF themes"
# # #         }

# # #         self._BAD_TRANSLATION_PATTERNS = [
# # #             r"error\s*5\d{2}", r"that’s an error", r"please try again later",
# # #             r"that’s all we know", r"\!\!150[0-9]", r"unusual traffic",
# # #             r"server error", r"<html", r"<!doctype", 
# # #             r"&copy\b(?!;)", r"&reg\b(?!;)", r"&trade\b(?!;)"
# # #         ]

# # #         # Only real PHP‑style placeholders
# # #         self.placeholder_regex = re.compile(r"%(?:\d+\$)?[sdifuxXeEgGcCr]")

# # #         self._counts = {
# # #             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
# # #             "reused_zip": 0, "reused_json": 0, "translated_google": 0,
# # #             "protected": 0, "skipped_bad": 0, "saved_edits": 0,
# # #             "skipped_protected": 0, "placeholder_preserved": 0,
# # #             "placeholder_fixed": 0
# # #         }

# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine = GoogleTranslatorEngine()

# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# # #             "ar": "nplurals=6; plural=(n==0?0:n==1?1:n==2?2:n%100>=3&&n%100<=10?3:n%100>=11?4:5);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;"
# # #         }

# # #         self.LANGUAGE_PRIORITY = [
# # #             "en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"
# # #         ]

# # #         self.POPULAR_THEMES_FALLBACK = [
# # #             "astra", "neve", "generatepress", "oceanwp", "kadence",
# # #             "blocksy", "hello-elementor", "sydney", "hestia", "zakra"
# # #         ]

# # #     def _display_status(self, message: str):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message: str):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _is_bad_translation(self, text: str) -> bool:
# # #         if not text:
# # #             return False
# # #         text_lower = text.lower()
# # #         return any(re.search(pat, text_lower) for pat in self._BAD_TRANSLATION_PATTERNS)

# # #     def _should_skip_translation(self, original: str, translated: str = None) -> bool:
# # #         if any(ent in original for ent in self.PROTECTED_ENTITIES):
# # #             return True
# # #         if translated and self._is_bad_translation(translated):
# # #             return True
# # #         return False

# # #     def _sanitize_for_php(self, text: str) -> str:
# # #         if not text:
# # #             return text

# # #         # Remove junk
# # #         for junk in ['�', '\u200B', '\uFEFF', '\x00']:
# # #             text = text.replace(junk, '')

# # #         # Escape raw '%' not part of placeholders
# # #         text = re.sub(r'%(?!\d*\$?[sdifuxXeEgGcCr])', '%%', text)

# # #         # Normalize uppercase placeholders
# # #         text = re.sub(r'%([DSF])', lambda m: '%' + m.group(1).lower(), text)

# # #         # Fix double escapes
# # #         text = re.sub(r'%%+', '%%', text)

# # #         return text.strip()

# # #     def _preserve_placeholders(self, original: str, translated: str) -> str:
# # #         orig_ph = self.placeholder_regex.findall(original)
# # #         if not orig_ph:
# # #             return self._sanitize_for_php(translated)

# # #         temp = self.placeholder_regex.sub("<<PH>>", translated)
# # #         for ph in orig_ph:
# # #             temp = temp.replace("<<PH>>", ph, 1)

# # #         return self._sanitize_for_php(temp)

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         return sorted(self.placeholder_regex.findall(original)) == sorted(self.placeholder_regex.findall(translated))

# # #     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
# # #         key = (text, target_language)
# # #         if key in self._cache:
# # #             cached = self._cache[key]
# # #             if self._is_bad_translation(cached):
# # #                 self._counts["skipped_bad"] += 1
# # #                 return text
# # #             return cached

# # #         translated = self.translator_engine.translate_single(text, target_language)
# # #         safe_text = self._sanitize_for_php(translated)

# # #         if self._is_bad_translation(safe_text):
# # #             self._counts["skipped_bad"] += 1
# # #             return text

# # #         self._cache[key] = safe_text
# # #         memory[text] = safe_text
# # #         return safe_text

# # #     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
# # #         glossary_lookup = {}
# # #         short_terms = {}
# # #         if not csv_file_path or not os.path.exists(csv_file_path):
# # #             return glossary_lookup, short_terms

# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         if orig and trans:
# # #                             if self._should_skip_translation(orig, trans):
# # #                                 continue
# # #                             trans = self._preserve_placeholders(orig, trans)
# # #                             glossary_lookup[(orig, ctx)] = trans
# # #                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
# # #                                 short_terms[orig] = trans
# # #                 return glossary_lookup, short_terms
# # #             except:
# # #                 continue
# # #         return glossary_lookup, short_terms

# # #     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
# # #         lookup = {}
# # #         if not folder_path or not os.path.exists(folder_path):
# # #             return lookup

# # #         lang_pattern = f"-{lang_code}."
# # #         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

# # #         skipped = 0
# # #         for root, _, files in os.walk(folder_path):
# # #             for file in files:
# # #                 if file.startswith('._') or file.startswith('__MACOSX'):
# # #                     continue
# # #                 if file.lower().endswith('.po') and lang_pattern in file.lower():
# # #                     file_path = os.path.join(root, file)
# # #                     try:
# # #                         detection = from_path(file_path).best()
# # #                         encoding = detection.encoding if detection else 'utf-8'
# # #                         po = polib.pofile(file_path, encoding=encoding)
# # #                         for entry in po:
# # #                             if entry.msgstr.strip():
# # #                                 cleaned = self._sanitize_for_php(entry.msgstr.strip())
# # #                                 cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# # #                                 if self._should_skip_translation(entry.msgid, cleaned):
# # #                                     skipped += 1
# # #                                     continue
# # #                                 if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                                     key = (entry.msgid, entry.msgctxt or '')
# # #                                     lookup[key] = cleaned
# # #                         print(f"   ✓ Loaded: {file} ({len(lookup)} good, skipped {skipped} bad/broken)")
# # #                     except Exception as e:
# # #                         print(f"   ✗ Failed: {file} ({e})")
# # #         if skipped > 0:
# # #             print(f"   ⚠ Skipped {skipped} bad/broken translations from ZIP")
# # #         return lookup

# # #     def _download_wporg_po(self, theme_slug: str, lang_code: str, use_cache: bool = True) -> Dict[Tuple[str, str], str]:
# # #         cache_path = os.path.join(self.CACHE_DIR, f"{theme_slug}-{lang_code}.po")
        
# # #         if use_cache and os.path.exists(cache_path):
# # #             age_days = (time.time() - os.path.getmtime(cache_path)) / (24 * 3600)
# # #             if age_days < self.CACHE_DAYS:
# # #                 print(f"   ✓ Using weekly cached .po for {theme_slug}/{lang_code}")
# # #                 return self._load_single_po(cache_path)
        
# # #         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
# # #         headers = {
# # #             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
# # #             'Accept': 'text/plain,*/*;q=0.9',
# # #             'Referer': 'https://translate.wordpress.org/',
# # #         }
# # #         try:
# # #             response = requests.get(url, timeout=30, headers=headers)
# # #             if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
# # #                 if use_cache:
# # #                     with open(cache_path, 'w', encoding='utf-8') as f:
# # #                         f.write(response.text)
# # #                     print(f"   ✓ Downloaded & cached {theme_slug}/{lang_code}")
                
# # #                 temp_path = os.path.join("/tmp", f"temp-{theme_slug}-{lang_code}.po")
# # #                 with open(temp_path, 'w', encoding='utf-8') as f:
# # #                     f.write(response.text)
# # #                 lookup = self._load_single_po(temp_path)
# # #                 os.remove(temp_path)
# # #                 return lookup
# # #             else:
# # #                 print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
# # #         except Exception as e:
# # #             print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
# # #         return {}

# # #     def _load_single_po(self, file_path: str) -> Dict[Tuple[str, str], str]:
# # #         lookup = {}
# # #         if not os.path.exists(file_path):
# # #             return lookup
# # #         try:
# # #             detection = from_path(file_path).best()
# # #             encoding = detection.encoding if detection else 'utf-8'
# # #             po = polib.pofile(file_path, encoding=encoding)
# # #             for entry in po:
# # #                 if entry.msgstr.strip():
# # #                     cleaned = self._sanitize_for_php(entry.msgstr.strip())
# # #                     cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# # #                     if self._should_skip_translation(entry.msgid, cleaned):
# # #                         continue
# # #                     if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                         lookup[(entry.msgid, entry.msgctxt or '')] = cleaned
# # #             print(f"   ✓ Loaded cached/single PO ({len(lookup)} strings)")
# # #         except Exception as e:
# # #             print(f"   ✗ Failed to load PO: {e}")
# # #         return lookup

# # #     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
# # #                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str, user_override: str = None):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key = (msgid, msgctxt)
# # #         full_key = f"{msgctxt}||{msgid}"

# # #         self._counts["total"] += 1

# # #         if self.placeholder_regex.search(msgid):
# # #             self._counts["placeholder_preserved"] += 1

# # #             if user_override is not None and user_override.strip():
# # #                 clean = self._preserve_placeholders(msgid, user_override)
# # #                 self._counts["saved_edits"] += 1
# # #                 return clean, "User Edited (placeholders preserved)"

# # #             if key in wporg_lookup:
# # #                 trans = self._preserve_placeholders(msgid, wporg_lookup[key])
# # #                 self._counts["reused_wporg"] += 1
# # #                 return trans, "WP.org (placeholders preserved)"

# # #             if gloss := glossary_lookup.get(key):
# # #                 trans = self._preserve_placeholders(msgid, gloss)
# # #                 self._counts["reused_glossary"] += 1
# # #                 return trans, "Glossary (placeholders preserved)"

# # #             if existing := existing_po_lookup.get(key):
# # #                 trans = self._preserve_placeholders(msgid, existing)
# # #                 self._counts["reused_zip"] += 1
# # #                 return trans, "Existing PO (placeholders preserved)"

# # #             if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# # #                 text = val[0]
# # #                 if text.startswith(("★", "○")):
# # #                     cleaned = self._preserve_placeholders(msgid, text[2:].strip())
# # #                     self._counts["reused_json"] += 1
# # #                     return cleaned, "Global JSON (placeholders preserved)"

# # #             fb = self._fallback_translate(memory, msgid, target_language)
# # #             fb = self._preserve_placeholders(msgid, fb)
# # #             self._counts["translated_google"] += 1
# # #             return fb, "Google (placeholders preserved)"

# # #         if user_override is not None and user_override.strip():
# # #             self._counts["saved_edits"] += 1
# # #             return user_override.strip(), "User Edited"

# # #         if msgid in self.PROTECTED_STRINGS:
# # #             self._counts["protected"] += 1
# # #             return msgid, "Protected String"

# # #         if key in wporg_lookup:
# # #             self._counts["reused_wporg"] += 1
# # #             return wporg_lookup[key], "WP.org Official"

# # #         if gloss := glossary_lookup.get(key):
# # #             self._counts["reused_glossary"] += 1
# # #             return gloss, "Glossary"

# # #         if existing := existing_po_lookup.get(key):
# # #             self._counts["reused_zip"] += 1
# # #             return existing, "Existing PO"

# # #         if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# # #             text = val[0]
# # #             if text.startswith(("★", "○")):
# # #                 self._counts["reused_json"] += 1
# # #                 return text[2:].strip(), "Global JSON"

# # #         fb = self._fallback_translate(memory, msgid, target_language)
# # #         self._counts["translated_google"] += 1

# # #         if short_terms:
# # #             final = fb
# # #             for term, replacement in short_terms.items():
# # #                 pattern = rf'\b{re.escape(term)}\b'
# # #                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
# # #                 if new_text != final:
# # #                     final = new_text
# # #                     self._counts["reused_glossary"] += 1
# # #             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

# # #         return fb, "Google Translate"

# # #     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
# # #             use_wporg=False, user_edits=None):
# # #         self._display_status("Starting Localization Tool")

# # #         if zip_paths_by_lang is None:
# # #             zip_paths_by_lang = {}
# # #         if user_edits is None:
# # #             user_edits = {}

# # #         project_dir = output_dir or os.path.dirname(pot_path)
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         valid_langs = [code for code, _ in settings.LANGUAGES]
# # #         selected_langs = [lang for lang in target_langs if lang in valid_langs]

# # #         if not selected_langs:
# # #             self._display_error("No valid languages")
# # #             return False

# # #         def priority_key(lang):
# # #             try:
# # #                 return self.LANGUAGE_PRIORITY.index(lang)
# # #             except ValueError:
# # #                 return len(self.LANGUAGE_PRIORITY)

# # #         target_languages = sorted(selected_langs, key=priority_key)

# # #         self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

# # #         pot_filename = os.path.basename(pot_path)
# # #         raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
# # #         raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
# # #         raw_name = raw_name.replace(' ', '-').strip('-').lower()

# # #         af_themes_mapping = {
# # #             "chromenews": "chromenews",
# # #             "reviewnews": "reviewnews",
# # #             "morenews": "morenews",
# # #             "newsever": "newsever",
# # #             "broadnews": "broadnews",
# # #             "magnitude": "magnitude",
# # #             "covernews": "covernews",
# # #             "enternews": "enternews",
# # #             "newsium": "newsium",
# # #             "darknews": "darknews",
# # #             "newscrunch": "newscrunch",
# # #             "elegantmagazine": "elegant-magazine",
# # #         }

# # #         theme_slug = af_themes_mapping.get(raw_name, raw_name)
# # #         if not theme_slug or len(theme_slug) < 3:
# # #             theme_slug = "unknown-theme"

# # #         self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

# # #         try:
# # #             pot_file = polib.pofile(pot_path)

# # #             existing_by_lang = {}
# # #             for lang in target_languages:
# # #                 folder = zip_paths_by_lang.get(lang)
# # #                 if folder:
# # #                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
# # #                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
# # #                 else:
# # #                     existing_by_lang[lang] = {}

# # #             wporg_by_lang = {}
# # #             if use_wporg:
# # #                 self._display_status("Downloading official + cached popular themes translations...")
# # #                 for lang in target_languages:
# # #                     primary = self._download_wporg_po(theme_slug, lang, use_cache=False)
                    
# # #                     fallback = {}
# # #                     self._display_status(f"   Loading popular themes (weekly cache) for {lang.upper()}")
# # #                     for popular in self.POPULAR_THEMES_FALLBACK:
# # #                         temp = self._download_wporg_po(popular, lang, use_cache=True)
# # #                         for k, v in temp.items():
# # #                             if k not in fallback:
# # #                                 fallback[k] = v
                    
# # #                     combined = primary.copy()
# # #                     combined.update(fallback)
# # #                     wporg_by_lang[lang] = combined
# # #                     print(f"   → Total strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular cached: {len(fallback)})")

# # #             changes_made = False

# # #             for target_language in target_languages:
# # #                 self._counts = {k: 0 for k in self._counts}

# # #                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
# # #                 translations_memory = {}
# # #                 if os.path.exists(jed_path):
# # #                     try:
# # #                         with open(jed_path, 'r', encoding='utf-8') as f:
# # #                             data = json.load(f)
# # #                             skipped = 0
# # #                             for k, v in data.items():
# # #                                 if k:
# # #                                     if isinstance(v, list) and v:
# # #                                         val = v[0]
# # #                                         if val.startswith(("★", "○")):
# # #                                             cleaned_val = val[2:].strip()
# # #                                             if self._should_skip_translation(k.split("||")[-1], cleaned_val):
# # #                                                 skipped += 1
# # #                                                 continue
# # #                                             translations_memory[k] = [f"{val[0]} {cleaned_val}"]
# # #                                         else:
# # #                                             translations_memory[k] = v
# # #                             if skipped > 0:
# # #                                 self._display_status(f"Skipped {skipped} bad/broken translations from old JSON")
# # #                     except Exception as e:
# # #                         self._display_error(f"Failed to load JSON: {e}")

# # #                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
# # #                 glossary = glossary_data[0]
# # #                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

# # #                 existing_lookup = existing_by_lang.get(target_language, {})
# # #                 wporg_lookup = wporg_by_lang.get(target_language, {})

# # #                 version = 1
# # #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# # #                     version += 1

# # #                 po = polib.POFile()
# # #                 po.metadata = {
# # #                     'Project-Id-Version': '1.0',
# # #                     'Language': target_language,
# # #                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
# # #                     'X-Generator': 'Advanced Localization Tool 2026',
# # #                 }

# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue

# # #                     user_override = user_edits.get(entry.msgid, None) if user_edits else None

# # #                     if entry.msgid_plural:
# # #                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
# # #                         clean_plurals = {i: self._preserve_placeholders(entry.msgid, v.strip()) for i, v in plurals.items()}
# # #                         po.append(polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgid_plural=entry.msgid_plural,
# # #                             msgstr_plural=clean_plurals,
# # #                             msgctxt=entry.msgctxt,
# # #                         ))
# # #                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
# # #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
# # #                     else:
# # #                         translated, source = self._process_translation(
# # #                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language, user_override=user_override
# # #                         )
# # #                         clean = self._preserve_placeholders(entry.msgid, translated.strip())
# # #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
# # #                         symbol = "★" if "Google" not in source else "○"
# # #                         prefixed = f"{symbol} {clean}"
# # #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

# # #                         if user_override is not None and user_override.strip() != clean:
# # #                             changes_made = True

# # #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# # #                 out_mo = out_po.replace('.po', '.mo')
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)

# # #                 translations_memory[""] = {"lang": target_language}
# # #                 with open(jed_path, 'w', encoding='utf-8') as f:
# # #                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

# # #                 self._display_status(f"{target_language.upper()} v{version} complete")
# # #                 for k, v in self._counts.items():
# # #                     if v:
# # #                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")
# # #                 if self._counts["placeholder_fixed"] > 0:
# # #                     self._display_status(f"   ⚠ Fixed {self._counts['placeholder_fixed']} corrupted/duplicated placeholders!")

# # #             if changes_made:
# # #                 self._display_status("Changes saved successfully!")
# # #             else:
# # #                 self._display_status("No changes detected (check if you edited non-protected strings)")

# # #             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
# # #             return True

# # #         except Exception as e:
# # #             import traceback
# # #             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
# # #             return False

# # #     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
# # #         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
# # #         npl = 2
# # #         if "nplurals=1" in header:
# # #             npl = 1
# # #         elif "nplurals=3" in header:
# # #             npl = 3
# # #         elif "nplurals=6" in header:
# # #             npl = 6

# # #         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
# # #         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
# # #             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

# # #         results = {}
# # #         singular = self._fallback_translate(memory, entry.msgid, target_language)
# # #         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

# # #         results[0] = singular
# # #         for i in range(1, npl):
# # #             results[i] = plural

# # #         self._counts["translated_google"] += 2
# # #         return results






# # # # localizationtool/localization_logic.py &copy thik xaina
# # # # FINAL, COMPLETE, COPY‑PASTE VERSION — Safe, Stable, Ready to Test

# # # import polib
# # # import csv
# # # import os
# # # import re
# # # import json
# # # import requests
# # # import time
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings
# # # from charset_normalizer import from_path
# # # from deep_translator import GoogleTranslator as _GoogleTranslator


# # # class GoogleTranslatorEngine:
# # #     _BLOCK_KEYWORDS = [
# # #         "error 500", "504", "that’s an error", "please try again later",
# # #         "that’s all we know", "1500", "1504", "unusual traffic",
# # #         "server error", "blocked", "captcha", "<html", "<!doctype"
# # #     ]

# # #     def translate_single(self, text: str, target_lang: str) -> str:
# # #         original = text
# # #         for attempt in range(5):
# # #             try:
# # #                 translator = _GoogleTranslator(source="auto", target=target_lang)
# # #                 trans = translator.translate(text)
# # #                 time.sleep(3.5)

# # #                 trans_str = str(trans).strip()
# # #                 if any(kw.lower() in trans_str.lower() for kw in self._BLOCK_KEYWORDS):
# # #                     return original
# # #                 return trans_str
# # #             except Exception:
# # #                 time.sleep(6)
# # #         return original


# # # class ColabLocalizationTool:
# # #     def __init__(self):
# # #         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
# # #         os.makedirs(self.json_dir, exist_ok=True)

# # #         self.CACHE_DIR = "/tmp/popular_po_cache"
# # #         os.makedirs(self.CACHE_DIR, exist_ok=True)
# # #         self.CACHE_DAYS = 7

# # #         self.PROTECTED_ENTITIES = {
# # #             "&copy;", "&reg;", "&trade;", "&euro;", "&nbsp;",
# # #             "&lt;", "&gt;", "&amp;"
# # #         }

# # #         self.PROTECTED_STRINGS = {
# # #             "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews",
# # #             "Magnitude", "CoverNews", "EnterNews", "Elegant Magazine",
# # #             "DarkNews", "Newsium", "NewsCrunch", "AF themes"
# # #         }

# # #         self._BAD_TRANSLATION_PATTERNS = [
# # #             r"error\s*5\d{2}", r"that’s an error", r"please try again later",
# # #             r"that’s all we know", r"\!\!150[0-9]", r"unusual traffic",
# # #             r"server error", r"<html", r"<!doctype", 
# # #             r"&copy\b(?!;)", r"&reg\b(?!;)", r"&trade\b(?!;)"
# # #         ]

# # #         # Only real PHP‑style placeholders
# # #         self.placeholder_regex = re.compile(r"%(?:\d+\$)?[sdifuxXeEgGcCr]")

# # #         self._counts = {
# # #             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
# # #             "reused_zip": 0, "reused_json": 0, "translated_google": 0,
# # #             "protected": 0, "skipped_bad": 0, "saved_edits": 0,
# # #             "skipped_protected": 0, "placeholder_preserved": 0,
# # #             "placeholder_fixed": 0
# # #         }

# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine = GoogleTranslatorEngine()

# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# # #             "ar": "nplurals=6; plural=(n==0?0:n==1?1:n==2?2:n%100>=3&&n%100<=10?3:n%100>=11?4:5);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;"
# # #         }

# # #         self.LANGUAGE_PRIORITY = [
# # #             "en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"
# # #         ]

# # #         self.POPULAR_THEMES_FALLBACK = [
# # #             "astra", "neve", "generatepress", "oceanwp", "kadence",
# # #             "blocksy", "hello-elementor", "sydney", "hestia", "zakra"
# # #         ]

# # #     def _display_status(self, message: str):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message: str):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _is_bad_translation(self, text: str) -> bool:
# # #         if not text:
# # #             return False
# # #         text_lower = text.lower()
# # #         return any(re.search(pat, text_lower) for pat in self._BAD_TRANSLATION_PATTERNS)

# # #     def _should_skip_translation(self, original: str, translated: str = None) -> bool:
# # #         if any(ent in original for ent in self.PROTECTED_ENTITIES):
# # #             return True
# # #         if translated and self._is_bad_translation(translated):
# # #             return True
# # #         return False

# # #     def _sanitize_for_php(self, text: str) -> str:
# # #         if not text:
# # #             return text

# # #         # Remove junk
# # #         for junk in ['�', '\u200B', '\uFEFF', '\x00']:
# # #             text = text.replace(junk, '')

# # #         # Escape raw '%' not part of placeholders
# # #         text = re.sub(r'%(?!\d*\$?[sdifuxXeEgGcCr])', '%%', text)

# # #         # Normalize uppercase placeholders
# # #         text = re.sub(r'%([DSF])', lambda m: '%' + m.group(1).lower(), text)

# # #         # Fix double escapes
# # #         text = re.sub(r'%%+', '%%', text)

# # #         return text.strip()

# # #     def _preserve_placeholders(self, original: str, translated: str) -> str:
# # #         orig_ph = self.placeholder_regex.findall(original)
# # #         if not orig_ph:
# # #             return self._sanitize_for_php(translated)

# # #         temp = self.placeholder_regex.sub("<<PH>>", translated)
# # #         for ph in orig_ph:
# # #             temp = temp.replace("<<PH>>", ph, 1)

# # #         return self._sanitize_for_php(temp)

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         return sorted(self.placeholder_regex.findall(original)) == sorted(self.placeholder_regex.findall(translated))

# # #     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
# # #         key = (text, target_language)
# # #         if key in self._cache:
# # #             cached = self._cache[key]
# # #             if self._is_bad_translation(cached):
# # #                 self._counts["skipped_bad"] += 1
# # #                 return text
# # #             return cached

# # #         translated = self.translator_engine.translate_single(text, target_language)
# # #         safe_text = self._sanitize_for_php(translated)

# # #         if self._is_bad_translation(safe_text):
# # #             self._counts["skipped_bad"] += 1
# # #             return text

# # #         self._cache[key] = safe_text
# # #         memory[text] = safe_text
# # #         return safe_text

# # #     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
# # #         glossary_lookup = {}
# # #         short_terms = {}
# # #         if not csv_file_path or not os.path.exists(csv_file_path):
# # #             return glossary_lookup, short_terms

# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         if orig and trans:
# # #                             if self._should_skip_translation(orig, trans):
# # #                                 continue
# # #                             trans = self._preserve_placeholders(orig, trans)
# # #                             glossary_lookup[(orig, ctx)] = trans
# # #                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
# # #                                 short_terms[orig] = trans
# # #                 return glossary_lookup, short_terms
# # #             except:
# # #                 continue
# # #         return glossary_lookup, short_terms

# # #     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
# # #         lookup = {}
# # #         if not folder_path or not os.path.exists(folder_path):
# # #             return lookup

# # #         lang_pattern = f"-{lang_code}."
# # #         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

# # #         skipped = 0
# # #         for root, _, files in os.walk(folder_path):
# # #             for file in files:
# # #                 if file.startswith('._') or file.startswith('__MACOSX'):
# # #                     continue
# # #                 if file.lower().endswith('.po') and lang_pattern in file.lower():
# # #                     file_path = os.path.join(root, file)
# # #                     try:
# # #                         detection = from_path(file_path).best()
# # #                         encoding = detection.encoding if detection else 'utf-8'
# # #                         po = polib.pofile(file_path, encoding=encoding)
# # #                         for entry in po:
# # #                             if entry.msgstr.strip():
# # #                                 cleaned = self._sanitize_for_php(entry.msgstr.strip())
# # #                                 cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# # #                                 if self._should_skip_translation(entry.msgid, cleaned):
# # #                                     skipped += 1
# # #                                     continue
# # #                                 if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                                     key = (entry.msgid, entry.msgctxt or '')
# # #                                     lookup[key] = cleaned
# # #                         print(f"   ✓ Loaded: {file} ({len(lookup)} good, skipped {skipped} bad/broken)")
# # #                     except Exception as e:
# # #                         print(f"   ✗ Failed: {file} ({e})")
# # #         if skipped > 0:
# # #             print(f"   ⚠ Skipped {skipped} bad/broken translations from ZIP")
# # #         return lookup

# # #     def _download_wporg_po(self, theme_slug: str, lang_code: str, use_cache: bool = True) -> Dict[Tuple[str, str], str]:
# # #         cache_path = os.path.join(self.CACHE_DIR, f"{theme_slug}-{lang_code}.po")
        
# # #         if use_cache and os.path.exists(cache_path):
# # #             age_days = (time.time() - os.path.getmtime(cache_path)) / (24 * 3600)
# # #             if age_days < self.CACHE_DAYS:
# # #                 print(f"   ✓ Using weekly cached .po for {theme_slug}/{lang_code}")
# # #                 return self._load_single_po(cache_path)
        
# # #         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
# # #         headers = {
# # #             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
# # #             'Accept': 'text/plain,*/*;q=0.9',
# # #             'Referer': 'https://translate.wordpress.org/',
# # #         }
# # #         try:
# # #             response = requests.get(url, timeout=30, headers=headers)
# # #             if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
# # #                 if use_cache:
# # #                     with open(cache_path, 'w', encoding='utf-8') as f:
# # #                         f.write(response.text)
# # #                     print(f"   ✓ Downloaded & cached {theme_slug}/{lang_code}")
                
# # #                 temp_path = os.path.join("/tmp", f"temp-{theme_slug}-{lang_code}.po")
# # #                 with open(temp_path, 'w', encoding='utf-8') as f:
# # #                     f.write(response.text)
# # #                 lookup = self._load_single_po(temp_path)
# # #                 os.remove(temp_path)
# # #                 return lookup
# # #             else:
# # #                 print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
# # #         except Exception as e:
# # #             print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
# # #         return {}

# # #     def _load_single_po(self, file_path: str) -> Dict[Tuple[str, str], str]:
# # #         lookup = {}
# # #         if not os.path.exists(file_path):
# # #             return lookup
# # #         try:
# # #             detection = from_path(file_path).best()
# # #             encoding = detection.encoding if detection else 'utf-8'
# # #             po = polib.pofile(file_path, encoding=encoding)
# # #             for entry in po:
# # #                 if entry.msgstr.strip():
# # #                     cleaned = self._sanitize_for_php(entry.msgstr.strip())
# # #                     cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# # #                     if self._should_skip_translation(entry.msgid, cleaned):
# # #                         continue
# # #                     if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                         lookup[(entry.msgid, entry.msgctxt or '')] = cleaned
# # #             print(f"   ✓ Loaded cached/single PO ({len(lookup)} strings)")
# # #         except Exception as e:
# # #             print(f"   ✗ Failed to load PO: {e}")
# # #         return lookup

# # #     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
# # #                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str, user_override: str = None):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key = (msgid, msgctxt)
# # #         full_key = f"{msgctxt}||{msgid}"

# # #         self._counts["total"] += 1

# # #         if self.placeholder_regex.search(msgid):
# # #             self._counts["placeholder_preserved"] += 1

# # #             if user_override is not None and user_override.strip():
# # #                 clean = self._preserve_placeholders(msgid, user_override)
# # #                 self._counts["saved_edits"] += 1
# # #                 return clean, "User Edited (placeholders preserved)"

# # #             if key in wporg_lookup:
# # #                 trans = self._preserve_placeholders(msgid, wporg_lookup[key])
# # #                 self._counts["reused_wporg"] += 1
# # #                 return trans, "WP.org (placeholders preserved)"

# # #             if gloss := glossary_lookup.get(key):
# # #                 trans = self._preserve_placeholders(msgid, gloss)
# # #                 self._counts["reused_glossary"] += 1
# # #                 return trans, "Glossary (placeholders preserved)"

# # #             if existing := existing_po_lookup.get(key):
# # #                 trans = self._preserve_placeholders(msgid, existing)
# # #                 self._counts["reused_zip"] += 1
# # #                 return trans, "Existing PO (placeholders preserved)"

# # #             if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# # #                 text = val[0]
# # #                 if text.startswith(("★", "○")):
# # #                     cleaned = self._preserve_placeholders(msgid, text[2:].strip())
# # #                     self._counts["reused_json"] += 1
# # #                     return cleaned, "Global JSON (placeholders preserved)"

# # #             fb = self._fallback_translate(memory, msgid, target_language)
# # #             fb = self._preserve_placeholders(msgid, fb)
# # #             self._counts["translated_google"] += 1
# # #             return fb, "Google (placeholders preserved)"

# # #         if user_override is not None and user_override.strip():
# # #             self._counts["saved_edits"] += 1
# # #             return user_override.strip(), "User Edited"

# # #         if msgid in self.PROTECTED_STRINGS:
# # #             self._counts["protected"] += 1
# # #             return msgid, "Protected String"

# # #         if key in wporg_lookup:
# # #             self._counts["reused_wporg"] += 1
# # #             return wporg_lookup[key], "WP.org Official"

# # #         if gloss := glossary_lookup.get(key):
# # #             self._counts["reused_glossary"] += 1
# # #             return gloss, "Glossary"

# # #         if existing := existing_po_lookup.get(key):
# # #             self._counts["reused_zip"] += 1
# # #             return existing, "Existing PO"

# # #         if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# # #             text = val[0]
# # #             if text.startswith(("★", "○")):
# # #                 self._counts["reused_json"] += 1
# # #                 return text[2:].strip(), "Global JSON"

# # #         fb = self._fallback_translate(memory, msgid, target_language)
# # #         self._counts["translated_google"] += 1

# # #         if short_terms:
# # #             final = fb
# # #             for term, replacement in short_terms.items():
# # #                 pattern = rf'\b{re.escape(term)}\b'
# # #                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
# # #                 if new_text != final:
# # #                     final = new_text
# # #                     self._counts["reused_glossary"] += 1
# # #             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

# # #         return fb, "Google Translate"

# # #     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
# # #             use_wporg=False, user_edits=None):
# # #         self._display_status("Starting Localization Tool")

# # #         if zip_paths_by_lang is None:
# # #             zip_paths_by_lang = {}
# # #         if user_edits is None:
# # #             user_edits = {}

# # #         project_dir = output_dir or os.path.dirname(pot_path)
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         valid_langs = [code for code, _ in settings.LANGUAGES]
# # #         selected_langs = [lang for lang in target_langs if lang in valid_langs]

# # #         if not selected_langs:
# # #             self._display_error("No valid languages")
# # #             return False

# # #         def priority_key(lang):
# # #             try:
# # #                 return self.LANGUAGE_PRIORITY.index(lang)
# # #             except ValueError:
# # #                 return len(self.LANGUAGE_PRIORITY)

# # #         target_languages = sorted(selected_langs, key=priority_key)

# # #         self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

# # #         pot_filename = os.path.basename(pot_path)
# # #         raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
# # #         raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
# # #         raw_name = raw_name.replace(' ', '-').strip('-').lower()

# # #         af_themes_mapping = {
# # #             "chromenews": "chromenews",
# # #             "reviewnews": "reviewnews",
# # #             "morenews": "morenews",
# # #             "newsever": "newsever",
# # #             "broadnews": "broadnews",
# # #             "magnitude": "magnitude",
# # #             "covernews": "covernews",
# # #             "enternews": "enternews",
# # #             "newsium": "newsium",
# # #             "darknews": "darknews",
# # #             "newscrunch": "newscrunch",
# # #             "elegantmagazine": "elegant-magazine",
# # #         }

# # #         theme_slug = af_themes_mapping.get(raw_name, raw_name)
# # #         if not theme_slug or len(theme_slug) < 3:
# # #             theme_slug = "unknown-theme"

# # #         self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

# # #         try:
# # #             pot_file = polib.pofile(pot_path)

# # #             existing_by_lang = {}
# # #             for lang in target_languages:
# # #                 folder = zip_paths_by_lang.get(lang)
# # #                 if folder:
# # #                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
# # #                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
# # #                 else:
# # #                     existing_by_lang[lang] = {}

# # #             wporg_by_lang = {}
# # #             if use_wporg:
# # #                 self._display_status("Downloading official + cached popular themes translations...")
# # #                 for lang in target_languages:
# # #                     primary = self._download_wporg_po(theme_slug, lang, use_cache=False)
                    
# # #                     fallback = {}
# # #                     self._display_status(f"   Loading popular themes (weekly cache) for {lang.upper()}")
# # #                     for popular in self.POPULAR_THEMES_FALLBACK:
# # #                         temp = self._download_wporg_po(popular, lang, use_cache=True)
# # #                         for k, v in temp.items():
# # #                             if k not in fallback:
# # #                                 fallback[k] = v
                    
# # #                     combined = primary.copy()
# # #                     combined.update(fallback)
# # #                     wporg_by_lang[lang] = combined
# # #                     print(f"   → Total strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular cached: {len(fallback)})")

# # #             changes_made = False

# # #             for target_language in target_languages:
# # #                 self._counts = {k: 0 for k in self._counts}

# # #                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
# # #                 translations_memory = {}
# # #                 if os.path.exists(jed_path):
# # #                     try:
# # #                         with open(jed_path, 'r', encoding='utf-8') as f:
# # #                             data = json.load(f)
# # #                             skipped = 0
# # #                             for k, v in data.items():
# # #                                 if k:
# # #                                     if isinstance(v, list) and v:
# # #                                         val = v[0]
# # #                                         if val.startswith(("★", "○")):
# # #                                             cleaned_val = val[2:].strip()
# # #                                             if self._should_skip_translation(k.split("||")[-1], cleaned_val):
# # #                                                 skipped += 1
# # #                                                 continue
# # #                                             translations_memory[k] = [f"{val[0]} {cleaned_val}"]
# # #                                         else:
# # #                                             translations_memory[k] = v
# # #                             if skipped > 0:
# # #                                 self._display_status(f"Skipped {skipped} bad/broken translations from old JSON")
# # #                     except Exception as e:
# # #                         self._display_error(f"Failed to load JSON: {e}")

# # #                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
# # #                 glossary = glossary_data[0]
# # #                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

# # #                 existing_lookup = existing_by_lang.get(target_language, {})
# # #                 wporg_lookup = wporg_by_lang.get(target_language, {})

# # #                 version = 1
# # #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# # #                     version += 1

# # #                 po = polib.POFile()
# # #                 po.metadata = {
# # #                     'Project-Id-Version': '1.0',
# # #                     'Language': target_language,
# # #                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
# # #                     'X-Generator': 'Advanced Localization Tool 2026',
# # #                 }

# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue

# # #                     user_override = user_edits.get(entry.msgid, None) if user_edits else None

# # #                     if entry.msgid_plural:
# # #                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
# # #                         clean_plurals = {i: self._preserve_placeholders(entry.msgid, v.strip()) for i, v in plurals.items()}
# # #                         po.append(polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgid_plural=entry.msgid_plural,
# # #                             msgstr_plural=clean_plurals,
# # #                             msgctxt=entry.msgctxt,
# # #                         ))
# # #                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
# # #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
# # #                     else:
# # #                         translated, source = self._process_translation(
# # #                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language, user_override=user_override
# # #                         )
# # #                         clean = self._preserve_placeholders(entry.msgid, translated.strip())
# # #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
# # #                         symbol = "★" if "Google" not in source else "○"
# # #                         prefixed = f"{symbol} {clean}"
# # #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

# # #                         if user_override is not None and user_override.strip() != clean:
# # #                             changes_made = True

# # #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# # #                 out_mo = out_po.replace('.po', '.mo')
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)

# # #                 translations_memory[""] = {"lang": target_language}
# # #                 with open(jed_path, 'w', encoding='utf-8') as f:
# # #                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

# # #                 self._display_status(f"{target_language.upper()} v{version} complete")
# # #                 for k, v in self._counts.items():
# # #                     if v:
# # #                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")
# # #                 if self._counts["placeholder_fixed"] > 0:
# # #                     self._display_status(f"   ⚠ Fixed {self._counts['placeholder_fixed']} corrupted/duplicated placeholders!")

# # #             if changes_made:
# # #                 self._display_status("Changes saved successfully!")
# # #             else:
# # #                 self._display_status("No changes detected (check if you edited non-protected strings)")

# # #             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
# # #             return True

# # #         except Exception as e:
# # #             import traceback
# # #             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
# # #             return False

# # #     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
# # #         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
# # #         npl = 2
# # #         if "nplurals=1" in header:
# # #             npl = 1
# # #         elif "nplurals=3" in header:
# # #             npl = 3
# # #         elif "nplurals=6" in header:
# # #             npl = 6

# # #         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
# # #         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
# # #             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

# # #         results = {}
# # #         singular = self._fallback_translate(memory, entry.msgid, target_language)
# # #         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

# # #         results[0] = singular
# # #         for i in range(1, npl):
# # #             results[i] = plural

# # #         self._counts["translated_google"] += 2
# # #         return results











# # # localizationtool/localization_logic.py
# # # FINAL, COMPLETE, COPY‑PASTE VERSION — Safe, Stable, Ready to Test

# # import polib
# # import csv
# # import os
# # import re
# # import json
# # import requests
# # import time
# # from typing import Dict, Tuple, List, Optional
# # from django.conf import settings
# # from charset_normalizer import from_path
# # from deep_translator import GoogleTranslator as _GoogleTranslator


# # class GoogleTranslatorEngine:
# #     _BLOCK_KEYWORDS = [
# #         "error 500", "504", "that’s an error", "please try again later",
# #         "that’s all we know", "1500", "1504", "unusual traffic",
# #         "server error", "blocked", "captcha", "<html", "<!doctype"
# #     ]

# #     def translate_single(self, text: str, target_lang: str) -> str:
# #         original = text
# #         for attempt in range(5):
# #             try:
# #                 translator = _GoogleTranslator(source="auto", target=target_lang)
# #                 trans = translator.translate(text)
# #                 time.sleep(3.5)

# #                 trans_str = str(trans).strip()
# #                 if any(kw.lower() in trans_str.lower() for kw in self._BLOCK_KEYWORDS):
# #                     return original
# #                 return trans_str
# #             except Exception:
# #                 time.sleep(6)
# #         return original


# # class ColabLocalizationTool:
# #     def __init__(self):
# #         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
# #         os.makedirs(self.json_dir, exist_ok=True)

# #         self.CACHE_DIR = "/tmp/popular_po_cache"
# #         os.makedirs(self.CACHE_DIR, exist_ok=True)
# #         self.CACHE_DAYS = 7

# #         self.PROTECTED_ENTITIES = {
# #             "&copy;", "&reg;", "&trade;", "&euro;", "&nbsp;",
# #             "&lt;", "&gt;", "&amp;"
# #         }

# #         self.PROTECTED_STRINGS = {
# #             "Copyright &copy; All rights reserved.",
# #             "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews",
# #             "Magnitude", "CoverNews", "EnterNews", "Elegant Magazine",
# #             "DarkNews", "Newsium", "NewsCrunch", "AF themes"
# #         }

# #         self._BAD_TRANSLATION_PATTERNS = [
# #             r"error\s*5\d{2}", r"that’s an error", r"please try again later",
# #             r"that’s all we know", r"\!\!150[0-9]", r"unusual traffic",
# #             r"server error", r"<html", r"<!doctype", 
# #             r"&copy\b(?!;)", r"&reg\b(?!;)", r"&trade\b(?!;)"
# #         ]

# #         # Only real PHP‑style placeholders
# #         self.placeholder_regex = re.compile(r"%(?:\d+\$)?[sdifuxXeEgGcCr]")

# #         self._counts = {
# #             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
# #             "reused_zip": 0, "reused_json": 0, "translated_google": 0,
# #             "protected": 0, "skipped_bad": 0, "saved_edits": 0,
# #             "skipped_protected": 0, "placeholder_preserved": 0,
# #             "placeholder_fixed": 0
# #         }

# #         self._cache: Dict[Tuple[str, str], str] = {}
# #         self.translator_engine = GoogleTranslatorEngine()

# #         self.plural_forms_header = {
# #             "en": "nplurals=2; plural=(n != 1);",
# #             "es": "nplurals=2; plural=(n != 1);",
# #             "de": "nplurals=2; plural=(n != 1);",
# #             "fr": "nplurals=2; plural=(n > 1);",
# #             "pt": "nplurals=2; plural=(n != 1);",
# #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# #             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# #             "ar": "nplurals=6; plural=(n==0?0:n==1?1:n==2?2:n%100>=3&&n%100<=10?3:n%100>=11?4:5);",
# #             "nl": "nplurals=2; plural=(n != 1);",
# #             "hi": "nplurals=2; plural=(n != 1);",
# #             "ne": "nplurals=2; plural=(n != 1);",
# #             "it": "nplurals=2; plural=(n != 1);",
# #             "ja": "nplurals=1; plural=0;"
# #         }

# #         self.LANGUAGE_PRIORITY = [
# #             "en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"
# #         ]

# #         self.POPULAR_THEMES_FALLBACK = [
# #             "astra", "neve", "generatepress", "oceanwp", "kadence",
# #             "blocksy", "hello-elementor", "sydney", "hestia", "zakra"
# #         ]

# #     def _display_status(self, message: str):
# #         print(f"\n--- STATUS: {message} ---")

# #     def _display_error(self, message: str):
# #         print(f"\n--- ERROR: {message} ---")

# #     def _is_bad_translation(self, text: str) -> bool:
# #         if not text:
# #             return False
# #         text_lower = text.lower()
# #         return any(re.search(pat, text_lower) for pat in self._BAD_TRANSLATION_PATTERNS)

# #     def _should_skip_translation(self, original: str, translated: str = None) -> bool:
# #         if any(ent in original for ent in self.PROTECTED_ENTITIES):
# #             return True
# #         if translated and self._is_bad_translation(translated):
# #             return True
# #         return False

# #     def _sanitize_for_php(self, text: str) -> str:
# #         if not text:
# #             return text

# #         # Remove junk
# #         for junk in ['�', '\u200B', '\uFEFF', '\x00']:
# #             text = text.replace(junk, '')

# #         # Escape raw '%' not part of placeholders
# #         text = re.sub(r'%(?!\d*\$?[sdifuxXeEgGcCr])', '%%', text)

# #         # Normalize uppercase placeholders
# #         text = re.sub(r'%([DSF])', lambda m: '%' + m.group(1).lower(), text)

# #         # Fix double escapes
# #         text = re.sub(r'%%+', '%%', text)

# #         return text.strip()

# #     def _preserve_placeholders(self, original: str, translated: str) -> str:
# #         orig_ph = self.placeholder_regex.findall(original)
# #         if not orig_ph:
# #             return self._sanitize_for_php(translated)

# #         temp = self.placeholder_regex.sub("<<PH>>", translated)
# #         for ph in orig_ph:
# #             temp = temp.replace("<<PH>>", ph, 1)

# #         return self._sanitize_for_php(temp)

# #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# #         return sorted(self.placeholder_regex.findall(original)) == sorted(self.placeholder_regex.findall(translated))

# #     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
# #         key = (text, target_language)
# #         if key in self._cache:
# #             cached = self._cache[key]
# #             if self._is_bad_translation(cached):
# #                 self._counts["skipped_bad"] += 1
# #                 return text
# #             return cached

# #         translated = self.translator_engine.translate_single(text, target_language)
# #         safe_text = self._sanitize_for_php(translated)

# #         if self._is_bad_translation(safe_text):
# #             self._counts["skipped_bad"] += 1
# #             return text

# #         self._cache[key] = safe_text
# #         memory[text] = safe_text
# #         return safe_text

# #     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
# #         glossary_lookup = {}
# #         short_terms = {}
# #         if not csv_file_path or not os.path.exists(csv_file_path):
# #             return glossary_lookup, short_terms

# #         encodings = ['utf-8', 'latin1', 'cp1252']
# #         for encoding in encodings:
# #             try:
# #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# #                     reader = csv.DictReader(f)
# #                     for row in reader:
# #                         orig = (row.get("Original String", "") or "").strip()
# #                         ctx = (row.get("Context", "") or "").strip()
# #                         trans = (row.get("Translated String", "") or "").strip()
# #                         if orig and trans:
# #                             if self._should_skip_translation(orig, trans):
# #                                 continue
# #                             trans = self._preserve_placeholders(orig, trans)
# #                             glossary_lookup[(orig, ctx)] = trans
# #                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
# #                                 short_terms[orig] = trans
# #                 return glossary_lookup, short_terms
# #             except:
# #                 continue
# #         return glossary_lookup, short_terms

# #     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
# #         lookup = {}
# #         if not folder_path or not os.path.exists(folder_path):
# #             return lookup

# #         lang_pattern = f"-{lang_code}."
# #         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

# #         skipped = 0
# #         for root, _, files in os.walk(folder_path):
# #             for file in files:
# #                 if file.startswith('._') or file.startswith('__MACOSX'):
# #                     continue
# #                 if file.lower().endswith('.po') and lang_pattern in file.lower():
# #                     file_path = os.path.join(root, file)
# #                     try:
# #                         detection = from_path(file_path).best()
# #                         encoding = detection.encoding if detection else 'utf-8'
# #                         po = polib.pofile(file_path, encoding=encoding)
# #                         for entry in po:
# #                             if entry.msgstr.strip():
# #                                 cleaned = self._sanitize_for_php(entry.msgstr.strip())
# #                                 cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# #                                 if self._should_skip_translation(entry.msgid, cleaned):
# #                                     skipped += 1
# #                                     continue
# #                                 if self._placeholders_are_valid(entry.msgid, cleaned):
# #                                     key = (entry.msgid, entry.msgctxt or '')
# #                                     lookup[key] = cleaned
# #                         print(f"   ✓ Loaded: {file} ({len(lookup)} good, skipped {skipped} bad/broken)")
# #                     except Exception as e:
# #                         print(f"   ✗ Failed: {file} ({e})")
# #         if skipped > 0:
# #             print(f"   ⚠ Skipped {skipped} bad/broken translations from ZIP")
# #         return lookup

# #     def _download_wporg_po(self, theme_slug: str, lang_code: str, use_cache: bool = True) -> Dict[Tuple[str, str], str]:
# #         cache_path = os.path.join(self.CACHE_DIR, f"{theme_slug}-{lang_code}.po")
        
# #         if use_cache and os.path.exists(cache_path):
# #             age_days = (time.time() - os.path.getmtime(cache_path)) / (24 * 3600)
# #             if age_days < self.CACHE_DAYS:
# #                 print(f"   ✓ Using weekly cached .po for {theme_slug}/{lang_code}")
# #                 return self._load_single_po(cache_path)
        
# #         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
# #         headers = {
# #             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
# #             'Accept': 'text/plain,*/*;q=0.9',
# #             'Referer': 'https://translate.wordpress.org/',
# #         }
# #         try:
# #             response = requests.get(url, timeout=30, headers=headers)
# #             if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
# #                 if use_cache:
# #                     with open(cache_path, 'w', encoding='utf-8') as f:
# #                         f.write(response.text)
# #                     print(f"   ✓ Downloaded & cached {theme_slug}/{lang_code}")
                
# #                 temp_path = os.path.join("/tmp", f"temp-{theme_slug}-{lang_code}.po")
# #                 with open(temp_path, 'w', encoding='utf-8') as f:
# #                     f.write(response.text)
# #                 lookup = self._load_single_po(temp_path)
# #                 os.remove(temp_path)
# #                 return lookup
# #             else:
# #                 print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
# #         except Exception as e:
# #             print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
# #         return {}

# #     def _load_single_po(self, file_path: str) -> Dict[Tuple[str, str], str]:
# #         lookup = {}
# #         if not os.path.exists(file_path):
# #             return lookup
# #         try:
# #             detection = from_path(file_path).best()
# #             encoding = detection.encoding if detection else 'utf-8'
# #             po = polib.pofile(file_path, encoding=encoding)
# #             for entry in po:
# #                 if entry.msgstr.strip():
# #                     cleaned = self._sanitize_for_php(entry.msgstr.strip())
# #                     cleaned = self._preserve_placeholders(entry.msgid, cleaned)
# #                     if self._should_skip_translation(entry.msgid, cleaned):
# #                         continue
# #                     if self._placeholders_are_valid(entry.msgid, cleaned):
# #                         lookup[(entry.msgid, entry.msgctxt or '')] = cleaned
# #             print(f"   ✓ Loaded cached/single PO ({len(lookup)} strings)")
# #         except Exception as e:
# #             print(f"   ✗ Failed to load PO: {e}")
# #         return lookup

# #     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
# #                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str, user_override: str = None):
# #         msgid = pot_entry.msgid
# #         msgctxt = pot_entry.msgctxt or ''
# #         key = (msgid, msgctxt)
# #         full_key = f"{msgctxt}||{msgid}"

# #         self._counts["total"] += 1

# #         if self.placeholder_regex.search(msgid):
# #             self._counts["placeholder_preserved"] += 1

# #             if user_override is not None and user_override.strip():
# #                 clean = self._preserve_placeholders(msgid, user_override)
# #                 self._counts["saved_edits"] += 1
# #                 return clean, "User Edited (placeholders preserved)"

# #             if key in wporg_lookup:
# #                 trans = self._preserve_placeholders(msgid, wporg_lookup[key])
# #                 self._counts["reused_wporg"] += 1
# #                 return trans, "WP.org (placeholders preserved)"

# #             if gloss := glossary_lookup.get(key):
# #                 trans = self._preserve_placeholders(msgid, gloss)
# #                 self._counts["reused_glossary"] += 1
# #                 return trans, "Glossary (placeholders preserved)"

# #             if existing := existing_po_lookup.get(key):
# #                 trans = self._preserve_placeholders(msgid, existing)
# #                 self._counts["reused_zip"] += 1
# #                 return trans, "Existing PO (placeholders preserved)"

# #             if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# #                 text = val[0]
# #                 if text.startswith(("★", "○")):
# #                     cleaned = self._preserve_placeholders(msgid, text[2:].strip())
# #                     self._counts["reused_json"] += 1
# #                     return cleaned, "Global JSON (placeholders preserved)"

# #             fb = self._fallback_translate(memory, msgid, target_language)
# #             fb = self._preserve_placeholders(msgid, fb)
# #             self._counts["translated_google"] += 1
# #             return fb, "Google (placeholders preserved)"

# #         if user_override is not None and user_override.strip():
# #             self._counts["saved_edits"] += 1
# #             return user_override.strip(), "User Edited"

# #         if msgid in self.PROTECTED_STRINGS:
# #             self._counts["protected"] += 1
# #             return msgid, "Protected String"

# #         if key in wporg_lookup:
# #             self._counts["reused_wporg"] += 1
# #             return wporg_lookup[key], "WP.org Official"

# #         if gloss := glossary_lookup.get(key):
# #             self._counts["reused_glossary"] += 1
# #             return gloss, "Glossary"

# #         if existing := existing_po_lookup.get(key):
# #             self._counts["reused_zip"] += 1
# #             return existing, "Existing PO"

# #         if full_key in memory and isinstance((val := memory[full_key]), list) and val:
# #             text = val[0]
# #             if text.startswith(("★", "○")):
# #                 self._counts["reused_json"] += 1
# #                 return text[2:].strip(), "Global JSON"

# #         fb = self._fallback_translate(memory, msgid, target_language)
# #         self._counts["translated_google"] += 1

# #         if short_terms:
# #             final = fb
# #             for term, replacement in short_terms.items():
# #                 pattern = rf'\b{re.escape(term)}\b'
# #                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
# #                 if new_text != final:
# #                     final = new_text
# #                     self._counts["reused_glossary"] += 1
# #             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

# #         return fb, "Google Translate"

# #     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
# #             use_wporg=False, user_edits=None):
# #         self._display_status("Starting Localization Tool")

# #         if zip_paths_by_lang is None:
# #             zip_paths_by_lang = {}
# #         if user_edits is None:
# #             user_edits = {}

# #         project_dir = output_dir or os.path.dirname(pot_path)
# #         os.makedirs(project_dir, exist_ok=True)

# #         valid_langs = [code for code, _ in settings.LANGUAGES]
# #         selected_langs = [lang for lang in target_langs if lang in valid_langs]

# #         if not selected_langs:
# #             self._display_error("No valid languages")
# #             return False

# #         def priority_key(lang):
# #             try:
# #                 return self.LANGUAGE_PRIORITY.index(lang)
# #             except ValueError:
# #                 return len(self.LANGUAGE_PRIORITY)

# #         target_languages = sorted(selected_langs, key=priority_key)

# #         self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

# #         pot_filename = os.path.basename(pot_path)
# #         raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
# #         raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
# #         raw_name = raw_name.replace(' ', '-').strip('-').lower()

# #         af_themes_mapping = {
# #             "chromenews": "chromenews",
# #             "reviewnews": "reviewnews",
# #             "morenews": "morenews",
# #             "newsever": "newsever",
# #             "broadnews": "broadnews",
# #             "magnitude": "magnitude",
# #             "covernews": "covernews",
# #             "enternews": "enternews",
# #             "newsium": "newsium",
# #             "darknews": "darknews",
# #             "newscrunch": "newscrunch",
# #             "elegantmagazine": "elegant-magazine",
# #         }

# #         theme_slug = af_themes_mapping.get(raw_name, raw_name)
# #         if not theme_slug or len(theme_slug) < 3:
# #             theme_slug = "unknown-theme"

# #         self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

# #         try:
# #             pot_file = polib.pofile(pot_path)

# #             existing_by_lang = {}
# #             for lang in target_languages:
# #                 folder = zip_paths_by_lang.get(lang)
# #                 if folder:
# #                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
# #                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
# #                 else:
# #                     existing_by_lang[lang] = {}

# #             wporg_by_lang = {}
# #             if use_wporg:
# #                 self._display_status("Downloading official + cached popular themes translations...")
# #                 for lang in target_languages:
# #                     primary = self._download_wporg_po(theme_slug, lang, use_cache=False)
                    
# #                     fallback = {}
# #                     self._display_status(f"   Loading popular themes (weekly cache) for {lang.upper()}")
# #                     for popular in self.POPULAR_THEMES_FALLBACK:
# #                         temp = self._download_wporg_po(popular, lang, use_cache=True)
# #                         for k, v in temp.items():
# #                             if k not in fallback:
# #                                 fallback[k] = v
                    
# #                     combined = primary.copy()
# #                     combined.update(fallback)
# #                     wporg_by_lang[lang] = combined
# #                     print(f"   → Total strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular cached: {len(fallback)})")

# #             changes_made = False

# #             for target_language in target_languages:
# #                 self._counts = {k: 0 for k in self._counts}

# #                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
# #                 translations_memory = {}
# #                 if os.path.exists(jed_path):
# #                     try:
# #                         with open(jed_path, 'r', encoding='utf-8') as f:
# #                             data = json.load(f)
# #                             skipped = 0
# #                             for k, v in data.items():
# #                                 if k:
# #                                     if isinstance(v, list) and v:
# #                                         val = v[0]
# #                                         if val.startswith(("★", "○")):
# #                                             cleaned_val = val[2:].strip()
# #                                             if self._should_skip_translation(k.split("||")[-1], cleaned_val):
# #                                                 skipped += 1
# #                                                 continue
# #                                             translations_memory[k] = [f"{val[0]} {cleaned_val}"]
# #                                         else:
# #                                             translations_memory[k] = v
# #                             if skipped > 0:
# #                                 self._display_status(f"Skipped {skipped} bad/broken translations from old JSON")
# #                     except Exception as e:
# #                         self._display_error(f"Failed to load JSON: {e}")

# #                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
# #                 glossary = glossary_data[0]
# #                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

# #                 existing_lookup = existing_by_lang.get(target_language, {})
# #                 wporg_lookup = wporg_by_lang.get(target_language, {})

# #                 version = 1
# #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# #                     version += 1

# #                 po = polib.POFile()
# #                 po.metadata = {
# #                     'Project-Id-Version': '1.0',
# #                     'Language': target_language,
# #                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
# #                     'X-Generator': 'Advanced Localization Tool 2026',
# #                 }

# #                 for entry in pot_file:
# #                     if not entry.msgid:
# #                         continue

# #                     user_override = user_edits.get(entry.msgid, None) if user_edits else None

# #                     if entry.msgid_plural:
# #                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
# #                         clean_plurals = {i: self._preserve_placeholders(entry.msgid, v.strip()) for i, v in plurals.items()}
# #                         po.append(polib.POEntry(
# #                             msgid=entry.msgid,
# #                             msgid_plural=entry.msgid_plural,
# #                             msgstr_plural=clean_plurals,
# #                             msgctxt=entry.msgctxt,
# #                         ))
# #                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
# #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
# #                     else:
# #                         translated, source = self._process_translation(
# #                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language, user_override=user_override
# #                         )
# #                         clean = self._preserve_placeholders(entry.msgid, translated.strip())
# #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
# #                         symbol = "★" if "Google" not in source else "○"
# #                         prefixed = f"{symbol} {clean}"
# #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

# #                         if user_override is not None and user_override.strip() != clean:
# #                             changes_made = True

# #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# #                 out_mo = out_po.replace('.po', '.mo')
# #                 po.save(out_po)
# #                 po.save_as_mofile(out_mo)

# #                 translations_memory[""] = {"lang": target_language}
# #                 with open(jed_path, 'w', encoding='utf-8') as f:
# #                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

# #                 self._display_status(f"{target_language.upper()} v{version} complete")
# #                 for k, v in self._counts.items():
# #                     if v:
# #                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")
# #                 if self._counts["placeholder_fixed"] > 0:
# #                     self._display_status(f"   ⚠ Fixed {self._counts['placeholder_fixed']} corrupted/duplicated placeholders!")

# #             if changes_made:
# #                 self._display_status("Changes saved successfully!")
# #             else:
# #                 self._display_status("No changes detected (check if you edited non-protected strings)")

# #             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
# #             return True

# #         except Exception as e:
# #             import traceback
# #             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
# #             return False

# #     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
# #         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
# #         npl = 2
# #         if "nplurals=1" in header:
# #             npl = 1
# #         elif "nplurals=3" in header:
# #             npl = 3
# #         elif "nplurals=6" in header:
# #             npl = 6

# #         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
# #         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
# #             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

# #         results = {}
# #         singular = self._fallback_translate(memory, entry.msgid, target_language)
# #         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

# #         results[0] = singular
# #         for i in range(1, npl):
# #             results[i] = plural

# #         self._counts["translated_google"] += 2
# #         return results










#Grok said best code
# # localizationtool/localization_logic.py
# # FINAL, COMPLETE, COPY‑PASTE VERSION — Safe, Stable, Ready to Test

# import polib
# import csv
# import os
# import re
# import json
# import requests
# import time
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings
# from charset_normalizer import from_path
# from deep_translator import GoogleTranslator as _GoogleTranslator


# class GoogleTranslatorEngine:
#     _BLOCK_KEYWORDS = [
#         "error 500", "504", "that’s an error", "please try again later",
#         "that’s all we know", "1500", "1504", "unusual traffic",
#         "server error", "blocked", "captcha", "<html", "<!doctype"
#     ]

#     def translate_single(self, text: str, target_lang: str) -> str:
#         original = text
#         for attempt in range(5):
#             try:
#                 translator = _GoogleTranslator(source="auto", target=target_lang)
#                 trans = translator.translate(text)
#                 time.sleep(3.5)

#                 trans_str = str(trans).strip()
#                 if any(kw.lower() in trans_str.lower() for kw in self._BLOCK_KEYWORDS):
#                     return original
#                 return trans_str
#             except Exception:
#                 time.sleep(6)
#         return original


# class ColabLocalizationTool:
#     def __init__(self):
#         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
#         os.makedirs(self.json_dir, exist_ok=True)

#         self.CACHE_DIR = "/tmp/popular_po_cache"
#         os.makedirs(self.CACHE_DIR, exist_ok=True)
#         self.CACHE_DAYS = 7

#         self.PROTECTED_ENTITIES = {
#             "&copy;", "©",
#             "&reg;", "®",
#             "&trade;", "™",
#             "&euro;", "€",
#             "&nbsp;", "\u00A0",
#             "&lt;", "<",
#             "&gt;", ">",
#             "&amp;", "&"
#         }

#         self.PROTECTED_STRINGS = {
#             "Copyright &copy; All rights reserved.",
#             "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews",
#             "Magnitude", "CoverNews", "EnterNews", "Elegant Magazine",
#             "DarkNews", "Newsium", "NewsCrunch", "AF themes"
#         }

#         self._BAD_TRANSLATION_PATTERNS = [
#             r"error\s*5\d{2}", r"that’s an error", r"please try again later",
#             r"that’s all we know", r"\!\!150[0-9]", r"unusual traffic",
#             r"server error", r"<html", r"<!doctype", 
#             r"&copy\b(?!;)", r"&reg\b(?!;)", r"&trade\b(?!;)"
#         ]

#         # Only real PHP‑style placeholders
#         self.placeholder_regex = re.compile(r"%(?:\d+\$)?[sdifuxXeEgGcCr]")

#         self._counts = {
#             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
#             "reused_zip": 0, "reused_json": 0, "translated_google": 0,
#             "protected": 0, "skipped_bad": 0, "saved_edits": 0,
#             "skipped_protected": 0, "placeholder_preserved": 0,
#             "placeholder_fixed": 0
#         }

#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);",
#             "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);",
#             "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
#             "ar": "nplurals=6; plural=(n==0?0:n==1?1:n==2?2:n%100>=3&&n%100<=10?3:n%100>=11?4:5);",
#             "nl": "nplurals=2; plural=(n != 1);",
#             "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);",
#             "it": "nplurals=2; plural=(n != 1);",
#             "ja": "nplurals=1; plural=0;"
#         }

#         self.LANGUAGE_PRIORITY = [
#             "en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"
#         ]

#         self.POPULAR_THEMES_FALLBACK = [
#             "astra", "neve", "generatepress", "oceanwp", "kadence",
#             "blocksy", "hello-elementor", "sydney", "hestia", "zakra"
#         ]

#     def _display_status(self, message: str):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message: str):
#         print(f"\n--- ERROR: {message} ---")

#     def _is_bad_translation(self, text: str) -> bool:
#         if not text:
#             return False
#         text_lower = text.lower()
#         return any(re.search(pat, text_lower) for pat in self._BAD_TRANSLATION_PATTERNS)

#     def _should_skip_translation(self, original: str, translated: str = None) -> bool:
#         if any(ent in original for ent in self.PROTECTED_ENTITIES):
#             return True
#         if translated and self._is_bad_translation(translated):
#             return True
#         return False

#     def _sanitize_for_php(self, text: str) -> str:
#         if not text:
#             return text

#         # Remove junk
#         for junk in ['�', '\u200B', '\uFEFF', '\x00']:
#             text = text.replace(junk, '')

#         # Escape raw '%' not part of placeholders
#         text = re.sub(r'%(?!\d*\$?[sdifuxXeEgGcCr])', '%%', text)

#         # Normalize uppercase placeholders
#         text = re.sub(r'%([DSF])', lambda m: '%' + m.group(1).lower(), text)

#         # Fix double escapes
#         text = re.sub(r'%%+', '%%', text)

#         return text.strip()

#     def _preserve_placeholders(self, original: str, translated: str) -> str:
#         orig_ph = self.placeholder_regex.findall(original)
#         if not orig_ph:
#             return self._sanitize_for_php(translated)

#         temp = self.placeholder_regex.sub("<<PH>>", translated)
#         for ph in orig_ph:
#             temp = temp.replace("<<PH>>", ph, 1)

#         return self._sanitize_for_php(temp)

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         return sorted(self.placeholder_regex.findall(original)) == sorted(self.placeholder_regex.findall(translated))

#     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
#         key = (text, target_language)
#         if key in self._cache:
#             cached = self._cache[key]
#             if self._is_bad_translation(cached):
#                 self._counts["skipped_bad"] += 1
#                 return text
#             return cached

#         translated = self.translator_engine.translate_single(text, target_language)
#         safe_text = self._sanitize_for_php(translated)

#         if self._is_bad_translation(safe_text):
#             self._counts["skipped_bad"] += 1
#             return text

#         self._cache[key] = safe_text
#         memory[text] = safe_text
#         return safe_text

#     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
#         glossary_lookup = {}
#         short_terms = {}
#         if not csv_file_path or not os.path.exists(csv_file_path):
#             return glossary_lookup, short_terms

#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         if orig and trans:
#                             if self._should_skip_translation(orig, trans):
#                                 continue
#                             trans = self._preserve_placeholders(orig, trans)
#                             glossary_lookup[(orig, ctx)] = trans
#                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
#                                 short_terms[orig] = trans
#                 return glossary_lookup, short_terms
#             except:
#                 continue
#         return glossary_lookup, short_terms

#     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
#         lookup = {}
#         if not folder_path or not os.path.exists(folder_path):
#             return lookup

#         lang_pattern = f"-{lang_code}."
#         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

#         skipped = 0
#         for root, _, files in os.walk(folder_path):
#             for file in files:
#                 if file.startswith('._') or file.startswith('__MACOSX'):
#                     continue
#                 if file.lower().endswith('.po') and lang_pattern in file.lower():
#                     file_path = os.path.join(root, file)
#                     try:
#                         detection = from_path(file_path).best()
#                         encoding = detection.encoding if detection else 'utf-8'
#                         po = polib.pofile(file_path, encoding=encoding)
#                         for entry in po:
#                             if entry.msgstr.strip():
#                                 cleaned = self._sanitize_for_php(entry.msgstr.strip())
#                                 cleaned = self._preserve_placeholders(entry.msgid, cleaned)
#                                 if self._should_skip_translation(entry.msgid, cleaned):
#                                     skipped += 1
#                                     continue
#                                 if self._placeholders_are_valid(entry.msgid, cleaned):
#                                     key = (entry.msgid, entry.msgctxt or '')
#                                     lookup[key] = cleaned
#                         print(f"   ✓ Loaded: {file} ({len(lookup)} good, skipped {skipped} bad/broken)")
#                     except Exception as e:
#                         print(f"   ✗ Failed: {file} ({e})")
#         if skipped > 0:
#             print(f"   ⚠ Skipped {skipped} bad/broken translations from ZIP")
#         return lookup

#     def _download_wporg_po(self, theme_slug: str, lang_code: str, use_cache: bool = True) -> Dict[Tuple[str, str], str]:
#         cache_path = os.path.join(self.CACHE_DIR, f"{theme_slug}-{lang_code}.po")
        
#         if use_cache and os.path.exists(cache_path):
#             age_days = (time.time() - os.path.getmtime(cache_path)) / (24 * 3600)
#             if age_days < self.CACHE_DAYS:
#                 print(f"   ✓ Using weekly cached .po for {theme_slug}/{lang_code}")
#                 return self._load_single_po(cache_path)
        
#         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
#             'Accept': 'text/plain,*/*;q=0.9',
#             'Referer': 'https://translate.wordpress.org/',
#         }
#         try:
#             response = requests.get(url, timeout=30, headers=headers)
#             if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
#                 if use_cache:
#                     with open(cache_path, 'w', encoding='utf-8') as f:
#                         f.write(response.text)
#                     print(f"   ✓ Downloaded & cached {theme_slug}/{lang_code}")
                
#                 temp_path = os.path.join("/tmp", f"temp-{theme_slug}-{lang_code}.po")
#                 with open(temp_path, 'w', encoding='utf-8') as f:
#                     f.write(response.text)
#                 lookup = self._load_single_po(temp_path)
#                 os.remove(temp_path)
#                 return lookup
#             else:
#                 print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
#         except Exception as e:
#             print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
#         return {}

#     def _load_single_po(self, file_path: str) -> Dict[Tuple[str, str], str]:
#         lookup = {}
#         if not os.path.exists(file_path):
#             return lookup
#         try:
#             detection = from_path(file_path).best()
#             encoding = detection.encoding if detection else 'utf-8'
#             po = polib.pofile(file_path, encoding=encoding)
#             for entry in po:
#                 if entry.msgstr.strip():
#                     cleaned = self._sanitize_for_php(entry.msgstr.strip())
#                     cleaned = self._preserve_placeholders(entry.msgid, cleaned)
#                     if self._should_skip_translation(entry.msgid, cleaned):
#                         continue
#                     if self._placeholders_are_valid(entry.msgid, cleaned):
#                         lookup[(entry.msgid, entry.msgctxt or '')] = cleaned
#             print(f"   ✓ Loaded cached/single PO ({len(lookup)} strings)")
#         except Exception as e:
#             print(f"   ✗ Failed to load PO: {e}")
#         return lookup

#     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
#                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str, user_override: str = None):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''
#         key = (msgid, msgctxt)
#         full_key = f"{msgctxt}||{msgid}"

#         self._counts["total"] += 1

#         if self.placeholder_regex.search(msgid):
#             self._counts["placeholder_preserved"] += 1

#             if user_override is not None and user_override.strip():
#                 clean = self._preserve_placeholders(msgid, user_override)
#                 self._counts["saved_edits"] += 1
#                 return clean, "User Edited (placeholders preserved)"

#             if key in wporg_lookup:
#                 trans = self._preserve_placeholders(msgid, wporg_lookup[key])
#                 self._counts["reused_wporg"] += 1
#                 return trans, "WP.org (placeholders preserved)"

#             if gloss := glossary_lookup.get(key):
#                 trans = self._preserve_placeholders(msgid, gloss)
#                 self._counts["reused_glossary"] += 1
#                 return trans, "Glossary (placeholders preserved)"

#             if existing := existing_po_lookup.get(key):
#                 trans = self._preserve_placeholders(msgid, existing)
#                 self._counts["reused_zip"] += 1
#                 return trans, "Existing PO (placeholders preserved)"

#             if full_key in memory and isinstance((val := memory[full_key]), list) and val:
#                 text = val[0]
#                 if text.startswith(("★", "○")):
#                     cleaned = self._preserve_placeholders(msgid, text[2:].strip())
#                     self._counts["reused_json"] += 1
#                     return cleaned, "Global JSON (placeholders preserved)"

#             fb = self._fallback_translate(memory, msgid, target_language)
#             fb = self._preserve_placeholders(msgid, fb)
#             self._counts["translated_google"] += 1
#             return fb, "Google (placeholders preserved)"

#         if user_override is not None and user_override.strip():
#             self._counts["saved_edits"] += 1
#             return user_override.strip(), "User Edited"

#         if msgid in self.PROTECTED_STRINGS:
#             self._counts["protected"] += 1
#             return msgid, "Protected String"

#         if key in wporg_lookup:
#             self._counts["reused_wporg"] += 1
#             return wporg_lookup[key], "WP.org Official"

#         if gloss := glossary_lookup.get(key):
#             self._counts["reused_glossary"] += 1
#             return gloss, "Glossary"

#         if existing := existing_po_lookup.get(key):
#             self._counts["reused_zip"] += 1
#             return existing, "Existing PO"

#         if full_key in memory and isinstance((val := memory[full_key]), list) and val:
#             text = val[0]
#             if text.startswith(("★", "○")):
#                 self._counts["reused_json"] += 1
#                 return text[2:].strip(), "Global JSON"

#         fb = self._fallback_translate(memory, msgid, target_language)
#         self._counts["translated_google"] += 1

#         if short_terms:
#             final = fb
#             for term, replacement in short_terms.items():
#                 pattern = rf'\b{re.escape(term)}\b'
#                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
#                 if new_text != final:
#                     final = new_text
#                     self._counts["reused_glossary"] += 1
#             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

#         return fb, "Google Translate"

#     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
#             use_wporg=False, user_edits=None):
#         self._display_status("Starting Localization Tool")

#         if zip_paths_by_lang is None:
#             zip_paths_by_lang = {}
#         if user_edits is None:
#             user_edits = {}

#         project_dir = output_dir or os.path.dirname(pot_path)
#         os.makedirs(project_dir, exist_ok=True)

#         valid_langs = [code for code, _ in settings.LANGUAGES]
#         selected_langs = [lang for lang in target_langs if lang in valid_langs]

#         if not selected_langs:
#             self._display_error("No valid languages")
#             return False

#         def priority_key(lang):
#             try:
#                 return self.LANGUAGE_PRIORITY.index(lang)
#             except ValueError:
#                 return len(self.LANGUAGE_PRIORITY)

#         target_languages = sorted(selected_langs, key=priority_key)

#         self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

#         pot_filename = os.path.basename(pot_path)
#         raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
#         raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
#         raw_name = raw_name.replace(' ', '-').strip('-').lower()

#         af_themes_mapping = {
#             "chromenews": "chromenews",
#             "reviewnews": "reviewnews",
#             "morenews": "morenews",
#             "newsever": "newsever",
#             "broadnews": "broadnews",
#             "magnitude": "magnitude",
#             "covernews": "covernews",
#             "enternews": "enternews",
#             "newsium": "newsium",
#             "darknews": "darknews",
#             "newscrunch": "newscrunch",
#             "elegantmagazine": "elegant-magazine",
#         }

#         theme_slug = af_themes_mapping.get(raw_name, raw_name)
#         if not theme_slug or len(theme_slug) < 3:
#             theme_slug = "unknown-theme"

#         self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

#         try:
#             pot_file = polib.pofile(pot_path)

#             existing_by_lang = {}
#             for lang in target_languages:
#                 folder = zip_paths_by_lang.get(lang)
#                 if folder:
#                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
#                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
#                 else:
#                     existing_by_lang[lang] = {}

#             wporg_by_lang = {}
#             if use_wporg:
#                 self._display_status("Downloading official + cached popular themes translations...")
#                 for lang in target_languages:
#                     primary = self._download_wporg_po(theme_slug, lang, use_cache=False)
                    
#                     fallback = {}
#                     self._display_status(f"   Loading popular themes (weekly cache) for {lang.upper()}")
#                     for popular in self.POPULAR_THEMES_FALLBACK:
#                         temp = self._download_wporg_po(popular, lang, use_cache=True)
#                         for k, v in temp.items():
#                             if k not in fallback:
#                                 fallback[k] = v
                    
#                     combined = primary.copy()
#                     combined.update(fallback)
#                     wporg_by_lang[lang] = combined
#                     print(f"   → Total strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular cached: {len(fallback)})")

#             changes_made = False

#             for target_language in target_languages:
#                 self._counts = {k: 0 for k in self._counts}

#                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
#                 translations_memory = {}
#                 if os.path.exists(jed_path):
#                     try:
#                         with open(jed_path, 'r', encoding='utf-8') as f:
#                             data = json.load(f)
#                             skipped = 0
#                             for k, v in data.items():
#                                 if k:
#                                     if isinstance(v, list) and v:
#                                         val = v[0]
#                                         if val.startswith(("★", "○")):
#                                             cleaned_val = val[2:].strip()
#                                             if self._should_skip_translation(k.split("||")[-1], cleaned_val):
#                                                 skipped += 1
#                                                 continue
#                                             translations_memory[k] = [f"{val[0]} {cleaned_val}"]
#                                         else:
#                                             translations_memory[k] = v
#                             if skipped > 0:
#                                 self._display_status(f"Skipped {skipped} bad/broken translations from old JSON")
#                     except Exception as e:
#                         self._display_error(f"Failed to load JSON: {e}")

#                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
#                 glossary = glossary_data[0]
#                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

#                 existing_lookup = existing_by_lang.get(target_language, {})
#                 wporg_lookup = wporg_by_lang.get(target_language, {})

#                 version = 1
#                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
#                     version += 1

#                 po = polib.POFile()
#                 po.metadata = {
#                     'Project-Id-Version': '1.0',
#                     'Language': target_language,
#                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
#                     'X-Generator': 'Advanced Localization Tool 2026',
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     user_override = user_edits.get(entry.msgid, None) if user_edits else None

#                     if entry.msgid_plural:
#                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
#                         clean_plurals = {i: self._preserve_placeholders(entry.msgid, v.strip()) for i, v in plurals.items()}
#                         po.append(polib.POEntry(
#                             msgid=entry.msgid,
#                             msgid_plural=entry.msgid_plural,
#                             msgstr_plural=clean_plurals,
#                             msgctxt=entry.msgctxt,
#                         ))
#                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
#                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
#                     else:
#                         translated, source = self._process_translation(
#                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language, user_override=user_override
#                         )
#                         clean = self._preserve_placeholders(entry.msgid, translated.strip())
#                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
#                         symbol = "★" if "Google" not in source else "○"
#                         prefixed = f"{symbol} {clean}"
#                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

#                         if user_override is not None and user_override.strip() != clean:
#                             changes_made = True

#                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 translations_memory[""] = {"lang": target_language}
#                 with open(jed_path, 'w', encoding='utf-8') as f:
#                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

#                 self._display_status(f"{target_language.upper()} v{version} complete")
#                 for k, v in self._counts.items():
#                     if v:
#                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")
#                 if self._counts["placeholder_fixed"] > 0:
#                     self._display_status(f"   ⚠ Fixed {self._counts['placeholder_fixed']} corrupted/duplicated placeholders!")

#             if changes_made:
#                 self._display_status("Changes saved successfully!")
#             else:
#                 self._display_status("No changes detected (check if you edited non-protected strings)")

#             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
#             return True

#         except Exception as e:
#             import traceback
#             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
#             return False

#     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
#         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
#         npl = 2
#         if "nplurals=1" in header:
#             npl = 1
#         elif "nplurals=3" in header:
#             npl = 3
#         elif "nplurals=6" in header:
#             npl = 6

#         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
#         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
#             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

#         results = {}
#         singular = self._fallback_translate(memory, entry.msgid, target_language)
#         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

#         results[0] = singular
#         for i in range(1, npl):
#             results[i] = plural

#         self._counts["translated_google"] += 2
#         return results



# #formatchecking like loco translate
# # localizationtool/localization_logic.py
# # FULLY UPDATED FINAL VERSION — All Issues Fixed (Feb 17, 2026)

# localizationtool/localization_logic.py
# FULL SINGLE COMPLETE FILE — All Issues Fixed & Ready (Feb 18, 2026)

import polib
import csv
import os
import re
import json
import requests
import time
from typing import Dict, Tuple, List, Optional
from django.conf import settings
from charset_normalizer import from_path
from deep_translator import GoogleTranslator as _GoogleTranslator


class GoogleTranslatorEngine:
    _BLOCK_KEYWORDS = [
        "error 500", "504", "that’s an error", "please try again later",
        "that’s all we know", "1500", "1504", "unusual traffic",
        "server error", "blocked", "captcha", "<html", "<!doctype"
    ]

    def translate_single(self, text: str, target_lang: str) -> str:
        original = text
        for attempt in range(5):
            try:
                translator = _GoogleTranslator(source="auto", target=target_lang)
                trans = translator.translate(text)
                time.sleep(3.5)
                trans_str = str(trans).strip()
                if any(kw.lower() in trans_str.lower() for kw in self._BLOCK_KEYWORDS):
                    return original
                return trans_str
            except Exception:
                time.sleep(6)
        return original


class ColabLocalizationTool:
    def __init__(self):
        self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
        os.makedirs(self.json_dir, exist_ok=True)

        self.CACHE_DIR = "/tmp/popular_po_cache"
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        self.CACHE_DAYS = 7

        self.PROTECTED_ENTITIES = {
            "&copy;", "©", "&reg;", "®", "&trade;", "™",
            "&euro;", "€", "&nbsp;", "\u00A0", "&lt;", "<",
            "&gt;", ">", "&amp;", "&"
        }

        self.PROTECTED_STRINGS = {
            "Copyright &copy; All rights reserved.",
            "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews",
            "Magnitude", "CoverNews", "EnterNews", "Elegant Magazine",
            "DarkNews", "Newsium", "NewsCrunch", "AF themes"
        }

        self._BAD_TRANSLATION_PATTERNS = [
            r"error\s*5\d{2}", r"that’s an error", r"please try again later",
            r"that’s all we know", r"\!\!150[0-9]", r"unusual traffic",
            r"server error", r"<html", r"<!doctype"
        ]

        self.placeholder_regex = re.compile(r"%(?:\d+\$)?[sdifuxXeEgGcCr]")

        self._counts = {
            "total": 0, "reused_wporg": 0, "reused_glossary": 0,
            "reused_zip": 0, "reused_json": 0, "translated_google": 0,
            "protected": 0, "skipped_bad": 0, "saved_edits": 0,
            "placeholder_preserved": 0, "placeholder_fixed": 0,
            "validation_warnings": 0
        }

        self._cache: Dict[Tuple[str, str], str] = {}
        self.translator_engine = GoogleTranslatorEngine()

        self.plural_forms_header = {
            "en": "nplurals=2; plural=(n != 1);",
            "es": "nplurals=2; plural=(n != 1);",
            "de": "nplurals=2; plural=(n != 1);",
            "fr": "nplurals=2; plural=(n > 1);",
            "pt": "nplurals=2; plural=(n != 1);",
            "hi": "nplurals=2; plural=(n != 1);",
            "ne": "nplurals=2; plural=(n != 1);",
        }

        self.LANGUAGE_PRIORITY = ["en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"]
        self.POPULAR_THEMES_FALLBACK = ["astra", "neve", "generatepress", "oceanwp", "kadence"]

    def _display_status(self, message: str):
        print(f"\n--- STATUS: {message} ---")

    def _display_error(self, message: str):
        print(f"\n--- ERROR: {message} ---")

    def _is_bad_translation(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        return any(re.search(pat, text_lower) for pat in self._BAD_TRANSLATION_PATTERNS)

    def _should_skip_translation(self, original: str) -> bool:
        if any(ent in original for ent in self.PROTECTED_ENTITIES):
            return True
        if original.strip() in self.PROTECTED_STRINGS:
            return True
        return False

    def _sanitize_for_php(self, text: str) -> str:
        if not text:
            return text
        for junk in ['�', '\u200B', '\uFEFF', '\x00']:
            text = text.replace(junk, '')
        text = re.sub(r'%(?!\d*\$?[sdifuxXeEgGcCr])', '%%', text)
        return text.strip()

    def _preserve_placeholders(self, original: str, translated: str) -> str:
        orig_ph = self.placeholder_regex.findall(original)
        if not orig_ph:
            return self._sanitize_for_php(translated)
        temp = self.placeholder_regex.sub("<<PH>>", translated)
        for ph in orig_ph:
            temp = temp.replace("<<PH>>", ph, 1)
        return self._sanitize_for_php(temp)

    def _placeholders_are_valid(self, original: str, translated: str) -> bool:
        return sorted(self.placeholder_regex.findall(original)) == sorted(self.placeholder_regex.findall(translated))

    def _validate_po_file(self, po_path: str) -> List[str]:
        """Returns list of warnings so we can show them on webpage"""
        warnings = []
        try:
            po = polib.pofile(po_path)
            for entry in po:
                if not entry.msgstr or not entry.msgid:
                    continue

                orig_ph = self.placeholder_regex.findall(entry.msgid)
                trans_ph = self.placeholder_regex.findall(entry.msgstr)

                if len(orig_ph) != len(trans_ph):
                    msg = f"Placeholder mismatch → {entry.msgid[:60]}..."
                    warnings.append(msg)
                    print(f"   ⚠ {msg}")

                if re.search(r'%(?!\d*\$?[sdifuxXeEgGcCr])', entry.msgstr):
                    msg = f"Unescaped '%' → {entry.msgid[:60]}..."
                    warnings.append(msg)
                    print(f"   ⚠ {msg}")

                if re.search(r'&[a-zA-Z0-9]+(?![;])', entry.msgstr):
                    msg = f"Broken HTML entity → {entry.msgid[:60]}..."
                    warnings.append(msg)
                    print(f"   ⚠ {msg}")

            self._counts["validation_warnings"] = len(warnings)

            if not warnings:
                print(f"   ✅ Validation Passed: No format errors")
            else:
                print(f"   ⚠ Validation completed with {len(warnings)} warning(s)")

        except Exception as e:
            msg = f"Validation error: {e}"
            warnings.append(msg)
            print(f"   ✗ {msg}")

        return warnings

    def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
        key = (text, target_language)
        if key in self._cache:
            cached = self._cache[key]
            if self._is_bad_translation(cached):
                self._counts["skipped_bad"] += 1
                return text
            return cached

        translated = self.translator_engine.translate_single(text, target_language)
        safe_text = self._sanitize_for_php(translated)

        if self._is_bad_translation(safe_text):
            self._counts["skipped_bad"] += 1
            return text

        self._cache[key] = safe_text
        memory[text] = safe_text
        return safe_text

    def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
        glossary_lookup = {}
        short_terms = {}
        if not csv_file_path or not os.path.exists(csv_file_path):
            return glossary_lookup, short_terms

        encodings = ['utf-8', 'latin1', 'cp1252']
        for encoding in encodings:
            try:
                with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        orig = (row.get("Original String", "") or "").strip()
                        ctx = (row.get("Context", "") or "").strip()
                        trans = (row.get("Translated String", "") or "").strip()
                        if orig and trans:
                            if self._should_skip_translation(orig):
                                continue
                            trans = self._preserve_placeholders(orig, trans)
                            glossary_lookup[(orig, ctx)] = trans
                            if len(orig) <= 10 and orig.isalpha() and orig.isupper():
                                short_terms[orig] = trans
                return glossary_lookup, short_terms
            except:
                continue
        return glossary_lookup, short_terms

    def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
        lookup = {}
        if not folder_path or not os.path.exists(folder_path):
            return lookup

        lang_pattern = f"-{lang_code}."
        print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

        skipped = 0
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.startswith('._') or file.startswith('__MACOSX'):
                    continue
                if file.lower().endswith('.po') and lang_pattern in file.lower():
                    file_path = os.path.join(root, file)
                    try:
                        detection = from_path(file_path).best()
                        encoding = detection.encoding if detection else 'utf-8'
                        po = polib.pofile(file_path, encoding=encoding)
                        for entry in po:
                            if entry.msgstr.strip():
                                cleaned = self._sanitize_for_php(entry.msgstr.strip())
                                cleaned = self._preserve_placeholders(entry.msgid, cleaned)
                                if self._should_skip_translation(entry.msgid):
                                    skipped += 1
                                    continue
                                if self._placeholders_are_valid(entry.msgid, cleaned):
                                    key = (entry.msgid, entry.msgctxt or '')
                                    lookup[key] = cleaned
                        print(f"   ✓ Loaded: {file} ({len(lookup)} good, skipped {skipped} bad/broken)")
                    except Exception as e:
                        print(f"   ✗ Failed: {file} ({e})")
        if skipped > 0:
            print(f"   ⚠ Skipped {skipped} bad/broken translations from ZIP")
        return lookup

    def _download_wporg_po(self, theme_slug: str, lang_code: str, use_cache: bool = True) -> Dict[Tuple[str, str], str]:
        cache_path = os.path.join(self.CACHE_DIR, f"{theme_slug}-{lang_code}.po")
        
        if use_cache and os.path.exists(cache_path):
            age_days = (time.time() - os.path.getmtime(cache_path)) / (24 * 3600)
            if age_days < self.CACHE_DAYS:
                print(f"   ✓ Using weekly cached .po for {theme_slug}/{lang_code}")
                return self._load_single_po(cache_path)
        
        url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/plain,*/*;q=0.9',
            'Referer': 'https://translate.wordpress.org/',
        }
        try:
            response = requests.get(url, timeout=30, headers=headers)
            if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
                if use_cache:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"   ✓ Downloaded & cached {theme_slug}/{lang_code}")
                
                temp_path = os.path.join("/tmp", f"temp-{theme_slug}-{lang_code}.po")
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                lookup = self._load_single_po(temp_path)
                os.remove(temp_path)
                return lookup
            else:
                print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
        except Exception as e:
            print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
        return {}

    def _load_single_po(self, file_path: str) -> Dict[Tuple[str, str], str]:
        lookup = {}
        if not os.path.exists(file_path):
            return lookup
        try:
            detection = from_path(file_path).best()
            encoding = detection.encoding if detection else 'utf-8'
            po = polib.pofile(file_path, encoding=encoding)
            for entry in po:
                if entry.msgstr.strip():
                    cleaned = self._sanitize_for_php(entry.msgstr.strip())
                    cleaned = self._preserve_placeholders(entry.msgid, cleaned)
                    if self._should_skip_translation(entry.msgid):
                        continue
                    if self._placeholders_are_valid(entry.msgid, cleaned):
                        lookup[(entry.msgid, entry.msgctxt or '')] = cleaned
            print(f"   ✓ Loaded cached/single PO ({len(lookup)} strings)")
        except Exception as e:
            print(f"   ✗ Failed to load PO: {e}")
        return lookup

    def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
                             wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str, user_override: str = None):
        msgid = pot_entry.msgid
        msgctxt = pot_entry.msgctxt or ''
        key = (msgid, msgctxt)
        full_key = f"{msgctxt}||{msgid}"

        self._counts["total"] += 1

        if self.placeholder_regex.search(msgid):
            self._counts["placeholder_preserved"] += 1

            if user_override is not None and user_override.strip():
                clean = self._preserve_placeholders(msgid, user_override)
                self._counts["saved_edits"] += 1
                return clean, "User Edited (placeholders preserved)"

            if key in wporg_lookup:
                trans = self._preserve_placeholders(msgid, wporg_lookup[key])
                self._counts["reused_wporg"] += 1
                return trans, "WP.org (placeholders preserved)"

            if gloss := glossary_lookup.get(key):
                trans = self._preserve_placeholders(msgid, gloss)
                self._counts["reused_glossary"] += 1
                return trans, "Glossary (placeholders preserved)"

            if existing := existing_po_lookup.get(key):
                trans = self._preserve_placeholders(msgid, existing)
                self._counts["reused_zip"] += 1
                return trans, "Existing PO (placeholders preserved)"

            if full_key in memory and isinstance((val := memory[full_key]), list) and val:
                text = val[0]
                if text.startswith(("★", "○")):
                    cleaned = self._preserve_placeholders(msgid, text[2:].strip())
                    self._counts["reused_json"] += 1
                    return cleaned, "Global JSON (placeholders preserved)"

            fb = self._fallback_translate(memory, msgid, target_language)
            fb = self._preserve_placeholders(msgid, fb)
            self._counts["translated_google"] += 1
            return fb, "Google (placeholders preserved)"

        if user_override is not None and user_override.strip():
            self._counts["saved_edits"] += 1
            return user_override.strip(), "User Edited"

        if msgid in self.PROTECTED_STRINGS:
            self._counts["protected"] += 1
            return msgid, "Protected String"

        if key in wporg_lookup:
            self._counts["reused_wporg"] += 1
            return wporg_lookup[key], "WP.org Official"

        if gloss := glossary_lookup.get(key):
            self._counts["reused_glossary"] += 1
            return gloss, "Glossary"

        if existing := existing_po_lookup.get(key):
            self._counts["reused_zip"] += 1
            return existing, "Existing PO"

        if full_key in memory and isinstance((val := memory[full_key]), list) and val:
            text = val[0]
            if text.startswith(("★", "○")):
                self._counts["reused_json"] += 1
                return text[2:].strip(), "Global JSON"

        fb = self._fallback_translate(memory, msgid, target_language)
        self._counts["translated_google"] += 1

        if short_terms:
            final = fb
            for term, replacement in short_terms.items():
                pattern = rf'\b{re.escape(term)}\b'
                new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
                if new_text != final:
                    final = new_text
                    self._counts["reused_glossary"] += 1
            return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

        return fb, "Google Translate"

    def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
            use_wporg=False, user_edits=None):
        self._display_status("Starting Localization Tool")

        if zip_paths_by_lang is None:
            zip_paths_by_lang = {}
        if user_edits is None:
            user_edits = {}

        project_dir = output_dir or os.path.dirname(pot_path)
        os.makedirs(project_dir, exist_ok=True)

        valid_langs = [code for code, _ in settings.LANGUAGES]
        selected_langs = [lang for lang in target_langs if lang in valid_langs]

        if not selected_langs:
            self._display_error("No valid languages")
            return False

        def priority_key(lang):
            try:
                return self.LANGUAGE_PRIORITY.index(lang)
            except ValueError:
                return len(self.LANGUAGE_PRIORITY)

        target_languages = sorted(selected_langs, key=priority_key)

        self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

        pot_filename = os.path.basename(pot_path)
        raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
        raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
        raw_name = raw_name.replace(' ', '-').strip('-').lower()

        af_themes_mapping = {
            "chromenews": "chromenews", "reviewnews": "reviewnews", "morenews": "morenews",
            "newsever": "newsever", "broadnews": "broadnews", "magnitude": "magnitude",
            "covernews": "covernews", "enternews": "enternews", "newsium": "newsium",
            "darknews": "darknews", "newscrunch": "newscrunch", "elegantmagazine": "elegant-magazine",
        }

        theme_slug = af_themes_mapping.get(raw_name, raw_name)
        if not theme_slug or len(theme_slug) < 3:
            theme_slug = "unknown-theme"

        self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

        try:
            pot_file = polib.pofile(pot_path)

            existing_by_lang = {}
            for lang in target_languages:
                folder = zip_paths_by_lang.get(lang)
                if folder:
                    self._display_status(f"Loading existing translations for {lang.upper()} from folder")
                    existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
                else:
                    existing_by_lang[lang] = {}

            wporg_by_lang = {}
            if use_wporg:
                self._display_status("Downloading official + cached popular themes translations...")
                for lang in target_languages:
                    primary = self._download_wporg_po(theme_slug, lang, use_cache=False)
                    
                    fallback = {}
                    self._display_status(f"   Loading popular themes (weekly cache) for {lang.upper()}")
                    for popular in self.POPULAR_THEMES_FALLBACK:
                        temp = self._download_wporg_po(popular, lang, use_cache=True)
                        for k, v in temp.items():
                            if k not in fallback:
                                fallback[k] = v
                    
                    combined = primary.copy()
                    combined.update(fallback)
                    wporg_by_lang[lang] = combined
                    print(f"   → Total strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular cached: {len(fallback)})")

            changes_made = False

            for target_language in target_languages:
                self._counts = {k: 0 for k in self._counts}

                jed_path = os.path.join(self.json_dir, f"{target_language}.json")
                translations_memory = {}
                if os.path.exists(jed_path):
                    try:
                        with open(jed_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            skipped = 0
                            for k, v in data.items():
                                if k:
                                    if isinstance(v, list) and v:
                                        val = v[0]
                                        if val.startswith(("★", "○")):
                                            cleaned_val = val[2:].strip()
                                            if self._should_skip_translation(k.split("||")[-1]):
                                                skipped += 1
                                                continue
                                            translations_memory[k] = [f"{val[0]} {cleaned_val}"]
                                        else:
                                            translations_memory[k] = v
                            if skipped > 0:
                                self._display_status(f"Skipped {skipped} bad/broken translations from old JSON")
                    except Exception as e:
                        self._display_error(f"Failed to load JSON: {e}")

                glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
                glossary = glossary_data[0]
                short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

                existing_lookup = existing_by_lang.get(target_language, {})
                wporg_lookup = wporg_by_lang.get(target_language, {})

                version = 1
                while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
                    version += 1

                po = polib.POFile()
                po.metadata = {
                    'Project-Id-Version': '1.0',
                    'Language': target_language,
                    'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
                    'X-Generator': 'Advanced Localization Tool 2026',
                }

                for entry in pot_file:
                    if not entry.msgid:
                        continue

                    user_override = user_edits.get(entry.msgid, None) if user_edits else None

                    if entry.msgid_plural:
                        plurals = self._pluralize_entry(translations_memory, entry, target_language)
                        clean_plurals = {i: self._preserve_placeholders(entry.msgid, v.strip()) for i, v in plurals.items()}
                        po.append(polib.POEntry(
                            msgid=entry.msgid,
                            msgid_plural=entry.msgid_plural,
                            msgstr_plural=clean_plurals,
                            msgctxt=entry.msgctxt,
                        ))
                        prefixed = [f"★ {v.strip()}" for v in plurals.values()]
                        translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
                    else:
                        translated, source = self._process_translation(
                            translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language, user_override=user_override
                        )
                        clean = self._preserve_placeholders(entry.msgid, translated.strip())
                        po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
                        symbol = "★" if "Google" not in source else "○"
                        prefixed = f"{symbol} {clean}"
                        translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

                        if user_override is not None and user_override.strip() != clean:
                            changes_made = True

                out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
                out_mo = out_po.replace('.po', '.mo')
                po.save(out_po)
                po.save_as_mofile(out_mo)

                # === VALIDATION CHECKER ===
                self._validate_po_file(out_po)

                translations_memory[""] = {"lang": target_language}
                with open(jed_path, 'w', encoding='utf-8') as f:
                    json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

                self._display_status(f"{target_language.upper()} v{version} complete")
                for k, v in self._counts.items():
                    if v:
                        self._display_status(f"   {k.replace('_', ' ').title()}: {v}")

            if changes_made:
                self._display_status("Changes saved successfully!")
            else:
                self._display_status("No changes detected (check if you edited non-protected strings)")

            self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
            return True

        except Exception as e:
            import traceback
            self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
            return False

    def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
        header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
        npl = 2
        if "nplurals=1" in header:
            npl = 1
        elif "nplurals=3" in header:
            npl = 3
        elif "nplurals=6" in header:
            npl = 6

        full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
        if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
            return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

        results = {}
        singular = self._fallback_translate(memory, entry.msgid, target_language)
        plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

        results[0] = singular
        for i in range(1, npl):
            results[i] = plural

        self._counts["translated_google"] += 2
        return results