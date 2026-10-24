from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class StudentsAdminConfig(AdminConfig):
    default_site = "students.admin_site.StudentAdminSite"


class StudentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "students"
    verbose_name = "Quản lý sinh viên"
