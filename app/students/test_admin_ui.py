"""Integration coverage for dashboard permissions and existing admin workflows."""

from datetime import date
from decimal import Decimal
import re

from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse

from .admin_site import StudentAdminSite
from .models import ClassRoom, Grade, Student, Subject


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="overview-admin", email="admin@example.com", password="local-test-only"
        )
        cls.staff = get_user_model().objects.create_user(
            username="limited-staff", is_staff=True
        )
        cls.classroom = ClassRoom.objects.create(code="UI-A", name="Lớp giao diện A")
        cls.other_classroom = ClassRoom.objects.create(code="UI-B", name="Lớp giao diện B")
        cls.student = Student.objects.create(
            student_code="UI001",
            full_name="Sinh viên kiểm tra giao diện",
            date_of_birth=date(2005, 5, 1),
            class_room=cls.classroom,
        )
        scores = ["0", "4.99", "5", "6.99", "7", "8.49", "8.5", "10"]
        for index, score in enumerate(scores):
            subject = Subject.objects.create(code=f"UI-M{index}", name=f"Môn học {index}")
            Grade.objects.create(student=cls.student, subject=subject, score=score)

    def grant(self, *codenames):
        self.staff.user_permissions.add(
            *Permission.objects.filter(content_type__app_label="students", codename__in=codenames)
        )
        self.client.force_login(self.staff)

    def write_log(self, user, obj, flag=CHANGE, label=None):
        return LogEntry.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=str(obj.pk),
            object_repr=label or str(obj),
            action_flag=flag,
        )

    def test_custom_site_keeps_auth_and_student_admin_registration(self):
        self.assertIsInstance(admin.site._wrapped, StudentAdminSite)
        for model in [get_user_model(), Group, Student, ClassRoom, Subject, Grade]:
            self.assertTrue(admin.site.is_registered(model))
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 200)

    def test_dashboard_requires_active_staff_authentication(self):
        index_url = reverse("admin:index")
        self.assertRedirects(self.client.get(index_url), f"/admin/login/?next={index_url}")
        for flags in [{"is_staff": False}, {"is_staff": True, "is_active": False}]:
            with self.subTest(flags=flags):
                user = get_user_model().objects.create_user(
                    username=f"blocked-{len(get_user_model().objects.all())}", **flags
                )
                self.client.force_login(user)
                self.assertEqual(self.client.get(index_url).status_code, 302)

    def test_real_counts_and_grade_range_boundaries(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        dashboard = response.context["qlsv_dashboard"]
        self.assertEqual(dashboard["student_count"], 1)
        self.assertEqual(dashboard["classroom_count"], 2)
        self.assertEqual(dashboard["subject_count"], 8)
        self.assertEqual(dashboard["grade_count"], 8)
        self.assertEqual(dashboard["grade_average"], Decimal("6.37"))
        self.assertEqual([band["count"] for band in dashboard["grade_bands"]], [2, 2, 2, 2])
        self.assertEqual([band["percent"] for band in dashboard["grade_bands"]], [25] * 4)
        first_class = dashboard["classrooms"][0]
        self.assertEqual((first_class["code"], first_class["student_count"]), ("UI-A", 1))
        filtered = self.client.get(first_class["url"])
        self.assertEqual(list(filtered.context["cl"].result_list), [self.student])

    def test_staff_without_model_permissions_gets_no_data(self):
        self.write_log(self.staff, self.student, label="Confidential former access")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:index"))
        dashboard = response.context["qlsv_dashboard"]
        self.assertEqual(response.context["qlsv_navigation"], [])
        self.assertEqual(dashboard["cards"], [])
        self.assertEqual(dashboard["classrooms"], [])
        self.assertEqual(dashboard["grade_bands"], [])
        self.assertEqual(dashboard["recent_activity"], [])
        self.assertIsNone(dashboard["student_count"])
        self.assertIsNone(dashboard["grade_average"])
        self.assertFalse(dashboard["can_add_student"])
        self.assertNotContains(response, self.student.full_name)
        self.assertNotContains(response, "Confidential former access")

    def test_view_only_student_permission_hides_other_totals_and_actions(self):
        self.grant("view_student")
        self.write_log(self.staff, self.student, ADDITION)
        self.write_log(self.staff, self.classroom, label="Classroom log must stay hidden")
        self.write_log(self.admin_user, self.student, label="Another user's activity")
        response = self.client.get(reverse("admin:index"))
        dashboard = response.context["qlsv_dashboard"]
        self.assertEqual([card["key"] for card in dashboard["cards"]], ["student"])
        self.assertEqual(dashboard["student_count"], 1)
        self.assertIsNone(dashboard["classroom_count"])
        self.assertIsNone(dashboard["grade_count"])
        self.assertFalse(dashboard["can_view_grades"])
        self.assertFalse(dashboard["can_view_classrooms"])
        self.assertIsNone(dashboard["add_student_url"])
        self.assertIsNone(dashboard["cards"][0]["add_url"])
        self.assertEqual(len(dashboard["recent_activity"]), 1)
        self.assertEqual(dashboard["recent_activity"][0]["object_label"], str(self.student))
        self.assertEqual(list(response.context["log_entries"].values_list("object_repr", flat=True)), [str(self.student)])
        self.assertNotContains(response, "Classroom log must stay hidden")
        self.assertNotContains(response, "Another user's activity")
        self.assertEqual(self.client.get(reverse("admin:students_student_add")).status_code, 403)

    def test_classroom_counts_require_student_permission_too(self):
        self.grant("view_classroom")
        response = self.client.get(reverse("admin:index"))
        dashboard = response.context["qlsv_dashboard"]
        self.assertEqual(dashboard["classroom_count"], 2)
        self.assertIsNone(dashboard["student_count"])
        self.assertEqual(dashboard["classrooms"], [])
        self.assertFalse(dashboard["can_view_classrooms"])

    def test_add_only_permission_offers_entry_without_revealing_records(self):
        self.grant("add_subject")
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.context["qlsv_navigation"], [])
        self.assertEqual(response.context["qlsv_dashboard"]["cards"], [])
        add_entry = response.context["qlsv_add_only_navigation"][0]
        self.assertEqual(add_entry["url"], reverse("admin:students_subject_add"))
        self.assertEqual(self.client.get(add_entry["url"]).status_code, 200)

    def test_empty_dashboard_has_zero_counts_without_fake_average(self):
        Grade.objects.all().delete()
        Student.objects.all().delete()
        Subject.objects.all().delete()
        ClassRoom.objects.all().delete()
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        dashboard = response.context["qlsv_dashboard"]
        self.assertEqual([card["value"] for card in dashboard["cards"]], [0] * 4)
        self.assertIsNone(dashboard["grade_average"])
        self.assertEqual([band["percent"] for band in dashboard["grade_bands"]], [0] * 4)
        self.assertEqual(dashboard["classrooms"], [])
        self.assertEqual(dashboard["recent_activity"], [])

    def test_recent_deletion_has_no_link_and_escapes_object_representation(self):
        self.write_log(self.admin_user, self.student, DELETION, '<script>alert("log")</script>')
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        activity = response.context["qlsv_dashboard"]["recent_activity"][0]
        self.assertEqual(activity["action"], "delete")
        self.assertIsNone(activity["url"])
        self.assertNotContains(response, '<script>alert("log")</script>')


class AdminUIWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="forms-admin", email="admin@example.com", password="local-test-only"
        )
        cls.staff = get_user_model().objects.create_user(username="forms-reader", is_staff=True)
        cls.classroom = ClassRoom.objects.create(code="FORM-A", name="Lớp biểu mẫu")
        cls.student = Student.objects.create(
            student_code="FORM001", full_name="Sinh viên biểu mẫu",
            date_of_birth=date(2005, 1, 1), class_room=cls.classroom,
        )
        cls.subject = Subject.objects.create(code="FORM-MON", name="Môn biểu mẫu")
        cls.grade = Grade.objects.create(student=cls.student, subject=cls.subject, score="9.00")

    def test_custom_login_and_logout_preserve_csrf_and_authentication(self):
        client = Client(enforce_csrf_checks=True)
        login_url = reverse("admin:login")
        login_page = client.get(login_url)
        token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.content.decode()
        )
        self.assertIsNotNone(token)
        self.assertEqual(login_page.context["next"], reverse("admin:index"))
        credentials = {
            "username": "forms-admin",
            "password": "local-test-only",
            "next": login_page.context["next"],
        }
        with self.assertLogs("django.security.csrf", level="WARNING"):
            self.assertEqual(client.post(login_url, credentials).status_code, 403)
        response = client.post(login_url, {**credentials, "csrfmiddlewaretoken": token.group(1)})
        self.assertRedirects(response, reverse("admin:index"))
        dashboard = client.get(reverse("admin:index"))
        logout_token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"', dashboard.content.decode()
        )
        self.assertIsNotNone(logout_token)
        with self.assertLogs("django.security.csrf", level="WARNING"):
            self.assertEqual(client.post(reverse("admin:logout")).status_code, 403)
        response = client.post(
            reverse("admin:logout"), {"csrfmiddlewaretoken": logout_token.group(1)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get(reverse("admin:index")).status_code, 302)

    def test_grade_edit_rejects_invalid_values_and_preserves_existing_score(self):
        self.client.force_login(self.admin_user)
        change_url = reverse("admin:students_grade_change", args=[self.grade.pk])
        for score in ["-1", "11"]:
            with self.subTest(score=score):
                response = self.client.post(change_url, {
                    "student": self.student.pk, "subject": self.subject.pk, "score": score,
                })
                self.assertEqual(response.status_code, 200)
                self.assertIn("score", response.context["adminform"].form.errors)
                self.grade.refresh_from_db()
                self.assertEqual(self.grade.score, Decimal("9.00"))

    def test_duplicate_grade_and_protected_class_remain_blocked(self):
        self.client.force_login(self.admin_user)
        duplicate = self.client.post(reverse("admin:students_grade_add"), {
            "student": self.student.pk, "subject": self.subject.pk, "score": "8",
        })
        self.assertEqual(duplicate.status_code, 200)
        self.assertTrue(duplicate.context["adminform"].form.non_field_errors())
        deletion = self.client.post(
            reverse("admin:students_classroom_delete", args=[self.classroom.pk]), {"post": "yes"}
        )
        self.assertEqual(deletion.status_code, 200)
        self.assertTrue(deletion.context["protected"])
        self.assertTrue(ClassRoom.objects.filter(pk=self.classroom.pk).exists())
        self.assertEqual(Grade.objects.count(), 1)

    def test_autocomplete_keeps_search_and_related_model_permissions(self):
        url = reverse("admin:autocomplete")
        cases = [("student", self.student.student_code, self.student), ("subject", self.subject.code, self.subject)]
        self.client.force_login(self.admin_user)
        for field, term, expected in cases:
            with self.subTest(field=field):
                response = self.client.get(url, {
                    "app_label": "students", "model_name": "grade", "field_name": field, "term": term,
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["results"], [{"id": str(expected.pk), "text": str(expected)}])
        self.client.force_login(self.staff)
        forbidden = self.client.get(url, {
            "app_label": "students", "model_name": "grade", "field_name": "student", "term": "FORM",
        })
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotContains(forbidden, self.student.full_name, status_code=403)
