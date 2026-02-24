import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'localizationtool'))

from localization_logic import ColabLocalizationTool

# Define your file paths and target languages here.
pot_file = "localizationtool/template.pot"
zip_file = "existing_po_files.zip"
csv_file = "glossary.csv"
target_languages = ["es", "fr", "de", "it", "ja", "ar", "nl", "ru", "pl", "pt"]

tool = ColabLocalizationTool()

print("--- Starting localization process... ---")
output_zip = tool.run(pot_file, zip_file, csv_file, target_languages)

if output_zip:
    print(f"\n✅ Localization complete! Output file is at: {output_zip}")
else:
    print("\n❌ Localization failed.")