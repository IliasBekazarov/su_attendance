from django.urls import path
from .views import ReportView, ExportReportView

urlpatterns = [
    path('reports/<str:report_type>/', ReportView.as_view(), name='report'),
    path('reports/export/<str:format>/', ExportReportView.as_view(), name='export-report'),
]