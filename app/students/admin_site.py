"""Permission-aware overview for the existing Django administration site."""

from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode

from django.contrib.admin import AdminSite
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils import timezone

from .models import ClassRoom, Grade, Student, Subject


class StudentAdminSite(AdminSite):
    site_header = "Hệ thống quản lý sinh viên"
    site_title = "Quản lý sinh viên"
    index_title = "Tổng quan"
    # The public root redirects here; a second "View site" link would loop back.
    site_url = None

    dashboard_models = (
        (Student, "Sinh viên"),
        (ClassRoom, "Lớp học"),
        (Subject, "Môn học"),
        (Grade, "Điểm số"),
    )

    def _can_view(self, request, model):
        model_admin = self.get_model_admin(model)
        return (
            self.has_permission(request)
            and model_admin.has_module_permission(request)
            and model_admin.has_view_or_change_permission(request)
        )

    def _model_url(self, model, action):
        return reverse(
            f"admin:{model._meta.app_label}_{model._meta.model_name}_{action}",
            current_app=self.name,
        )

    def _navigation(self, request):
        return [
            {
                "key": model._meta.model_name,
                "label": label,
                "url": self._model_url(model, "changelist"),
                "add_url": (
                    self._model_url(model, "add")
                    if self.get_model_admin(model).has_add_permission(request)
                    else None
                ),
            }
            for model, label in self.dashboard_models
            if self._can_view(request, model)
        ]

    def each_context(self, request):
        add_only_navigation = []
        if self.has_permission(request):
            for model, label in self.dashboard_models:
                model_admin = self.get_model_admin(model)
                if (
                    not self._can_view(request, model)
                    and model_admin.has_module_permission(request)
                    and model_admin.has_add_permission(request)
                ):
                    add_only_navigation.append(
                        {
                            "key": model._meta.model_name,
                            "label": f"Thêm {label.lower()}",
                            "url": self._model_url(model, "add"),
                        }
                    )
        return {
            **super().each_context(request),
            "qlsv_navigation": self._navigation(request),
            "qlsv_add_only_navigation": add_only_navigation,
            "qlsv_today": timezone.localdate(),
        }

    def get_log_entries(self, request):
        """Do not reveal previous access after a user's permissions are removed."""
        entries = LogEntry.objects.select_related("content_type", "user")
        if not self.has_permission(request):
            return entries.none()
        allowed = Q(pk__in=[])
        for model in self._registry:
            if self._can_view(request, model):
                allowed |= Q(
                    content_type__app_label=model._meta.app_label,
                    content_type__model=model._meta.model_name,
                )
        return entries.filter(allowed, user=request.user)

    def _recent_activity(self, request):
        actions = {
            ADDITION: ("add", "Thêm mới"),
            CHANGE: ("change", "Cập nhật"),
            DELETION: ("delete", "Đã xóa"),
        }
        return [
            {
                "object_label": entry.object_repr,
                "model_label": str(entry.content_type),
                "action": actions.get(entry.action_flag, ("change", "Cập nhật"))[0],
                "action_label": actions.get(entry.action_flag, ("change", "Cập nhật"))[1],
                "url": None if entry.is_deletion() else entry.get_admin_url(),
                "time": entry.action_time,
            }
            for entry in self.get_log_entries(request).order_by("-action_time", "-pk")[:6]
        ]

    def _dashboard(self, request):
        navigation = self._navigation(request)
        visible_keys = {item["key"] for item in navigation}
        counts = {}
        for model, _label in self.dashboard_models:
            key = model._meta.model_name
            counts[key] = (
                self.get_model_admin(model).get_queryset(request).count()
                if key in visible_keys
                else None
            )

        grade_average = None
        grade_bands = []
        if "grade" in visible_keys:
            grades = self.get_model_admin(Grade).get_queryset(request)
            distribution = grades.aggregate(
                average=Avg("score"),
                low=Count("pk", filter=Q(score__lt=5)),
                mid=Count("pk", filter=Q(score__gte=5, score__lt=7)),
                good=Count("pk", filter=Q(score__gte=7, score__lt=Decimal("8.5"))),
                high=Count("pk", filter=Q(score__gte=Decimal("8.5"))),
            )
            if distribution["average"] is not None:
                grade_average = distribution["average"].quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            for tone, label in (
                ("low", "Dưới 5"),
                ("mid", "5 đến dưới 7"),
                ("good", "7 đến dưới 8,5"),
                ("high", "8,5 đến 10"),
            ):
                count = distribution[tone]
                grade_bands.append(
                    {
                        "label": label,
                        "count": count,
                        "percent": round(count * 100 / counts["grade"]) if counts["grade"] else 0,
                        "tone": tone,
                    }
                )

        can_view_classrooms = {"classroom", "student"}.issubset(visible_keys)
        classrooms = []
        if can_view_classrooms:
            students_url = self._model_url(Student, "changelist")
            classroom_rows = (
                self.get_model_admin(ClassRoom)
                .get_queryset(request)
                .annotate(student_count=Count("students"))
                .order_by("-student_count", "code")[:6]
            )
            classrooms = [
                {
                    "code": classroom.code,
                    "name": classroom.name,
                    "student_count": classroom.student_count,
                    "url": f"{students_url}?{urlencode({'class_room__id__exact': classroom.pk})}",
                }
                for classroom in classroom_rows
            ]

        student_admin = self.get_model_admin(Student)
        can_add_student = (
            self.has_permission(request)
            and student_admin.has_module_permission(request)
            and student_admin.has_add_permission(request)
        )
        return {
            "cards": [{**item, "value": counts[item["key"]]} for item in navigation],
            **{f"{key}_count": value for key, value in counts.items()},
            "grade_average": grade_average,
            "grade_bands": grade_bands,
            "classrooms": classrooms,
            "recent_activity": self._recent_activity(request),
            "can_view_grades": "grade" in visible_keys,
            "can_view_classrooms": can_view_classrooms,
            "can_add_student": can_add_student,
            "add_student_url": self._model_url(Student, "add") if can_add_student else None,
            "students_url": (
                self._model_url(Student, "changelist") if "student" in visible_keys else None
            ),
        }

    def index(self, request, extra_context=None):
        return super().index(
            request,
            extra_context={
                "qlsv_dashboard": self._dashboard(request),
                **(extra_context or {}),
            },
        )
