# mylocalizationproject02/urls.py

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from localizationtool.views import (
    localize_tool_view,
    download_folder,
    delete_folder,
    view_and_edit_translations,
    edit_language_version,
    check_po_validation,
    save_translation,          
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', localize_tool_view, name='localize_tool_view'),
    path('download/<str:folder_name>/', download_folder, name='download_folder'),
    path('delete/<str:folder_name>/', delete_folder, name='delete_folder'),

    path('edit/<str:folder_name>/', view_and_edit_translations, name='view_and_edit_translations'),
    path('edit/<str:folder_name>/<str:lang_code>/<int:version>/', 
         edit_language_version, name='edit_language_version'),

    # AJAX Endpoints
    path('check-validation/', check_po_validation, name='check_validation'),
    path('save-translation/', save_translation, name='save_translation'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)