from django.urls import path
from .views import downloadpdf_view

urlpatterns = [
    path('downloadpdf/<int:id>/', downloadpdf_view, name='download_view'),
]