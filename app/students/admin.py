from django.contrib import admin

from .models import ClassRoom, Grade, Student, Subject


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["student_code", "full_name", "date_of_birth", "email", "class_room"]
    search_fields = ["student_code", "full_name", "email"]
    list_filter = ["class_room"]
    list_select_related = ["class_room"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "score"]
    search_fields = ["student__student_code", "student__full_name", "subject__code"]
    list_filter = ["subject", "student__class_room"]
    list_select_related = ["student", "subject"]
    autocomplete_fields = ["student", "subject"]
