from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .models import ClassRoom, Grade, Student, Subject


class StudentDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.classroom = ClassRoom.objects.create(code="TEST-A", name="Lớp kiểm thử A")
        cls.student = Student.objects.create(
            student_code="TEST001",
            full_name="Sinh viên mẫu",
            date_of_birth=date(2005, 1, 1),
            class_room=cls.classroom,
        )
        cls.subject = Subject.objects.create(code="TEST-MON", name="Môn kiểm thử")

    def test_codes_are_unique(self):
        duplicates = [
            ClassRoom(code=self.classroom.code, name="Lớp trùng"),
            Subject(code=self.subject.code, name="Môn trùng"),
            Student(
                student_code=self.student.student_code,
                full_name="Sinh viên trùng",
                date_of_birth=date(2005, 1, 1),
                class_room=self.classroom,
            ),
        ]
        for duplicate in duplicates:
            with self.subTest(model=type(duplicate).__name__):
                with self.assertRaises(ValidationError):
                    duplicate.full_clean()
                with self.assertRaises(IntegrityError), transaction.atomic():
                    duplicate.save()

    def test_grade_allows_boundaries_and_rejects_outside_range(self):
        for score in [Decimal("0.00"), Decimal("10.00")]:
            with self.subTest(score=score):
                Grade(student=self.student, subject=self.subject, score=score).full_clean()
        for score in [Decimal("-0.01"), Decimal("10.01")]:
            with self.subTest(score=score):
                grade = Grade(student=self.student, subject=self.subject, score=score)
                with self.assertRaises(ValidationError):
                    grade.full_clean()
                with self.assertRaises(IntegrityError), transaction.atomic():
                    grade.save()

    def test_only_one_grade_per_student_and_subject(self):
        Grade.objects.create(student=self.student, subject=self.subject, score=7)
        duplicate = Grade(student=self.student, subject=self.subject, score=8)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            duplicate.save()

    def test_related_records_cannot_be_deleted_accidentally(self):
        grade = Grade.objects.create(student=self.student, subject=self.subject, score=7)
        for record in [self.classroom, self.student, self.subject]:
            with self.subTest(model=type(record).__name__):
                with self.assertRaises(ProtectedError):
                    record.delete()
        self.assertTrue(Grade.objects.filter(pk=grade.pk).exists())
        grade.delete()
        self.student.delete()
        self.classroom.delete()
        self.subject.delete()
        self.assertEqual(Student.objects.count(), 0)


class AdminWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="test-admin", email="admin@example.com", password="test-only-password"
        )
        cls.classroom = ClassRoom.objects.create(code="BASE-A", name="Lớp gốc")
        cls.student = Student.objects.create(
            student_code="BASE001",
            full_name="Sinh viên gốc",
            date_of_birth=date(2005, 1, 1),
            class_room=cls.classroom,
        )
        cls.subject = Subject.objects.create(code="BASE-MON", name="Môn gốc")

    def test_anonymous_visitor_must_log_in(self):
        for model in [ClassRoom, Student, Subject, Grade]:
            url = reverse(f"admin:students_{model._meta.model_name}_changelist")
            response = self.client.get(url)
            self.assertRedirects(response, f"/admin/login/?next={url}")

    def assert_admin_crud(self, model, values, changes, lookup):
        self.client.force_login(self.admin_user)
        prefix = f"admin:students_{model._meta.model_name}"
        response = self.client.post(reverse(f"{prefix}_add"), values)
        self.assertEqual(response.status_code, 302)
        obj = model.objects.get(**lookup)
        response = self.client.get(reverse(f"{prefix}_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(obj, response.context["cl"].result_list)
        response = self.client.post(
            reverse(f"{prefix}_change", args=[obj.pk]), {**values, **changes}
        )
        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db()
        for key, value in changes.items():
            self.assertEqual(str(getattr(obj, key)), str(value))
        response = self.client.post(reverse(f"{prefix}_delete", args=[obj.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_classroom_admin_crud(self):
        self.assert_admin_crud(
            ClassRoom,
            {"code": "NEW-A", "name": "Lớp mới"},
            {"name": "Lớp đã sửa"},
            {"code": "NEW-A"},
        )

    def test_subject_admin_crud(self):
        self.assert_admin_crud(
            Subject,
            {"code": "NEW-MON", "name": "Môn mới"},
            {"name": "Môn đã sửa"},
            {"code": "NEW-MON"},
        )

    def test_student_admin_crud(self):
        self.assert_admin_crud(
            Student,
            {
                "student_code": "NEW001",
                "full_name": "Sinh viên mới",
                "date_of_birth": "2005-01-02",
                "email": "demo@example.com",
                "class_room": self.classroom.pk,
            },
            {"full_name": "Sinh viên đã sửa"},
            {"student_code": "NEW001"},
        )

    def test_grade_admin_crud(self):
        self.assert_admin_crud(
            Grade,
            {"student": self.student.pk, "subject": self.subject.pk, "score": "7.50"},
            {"score": "8.25"},
            {"student": self.student, "subject": self.subject},
        )

    def test_invalid_grade_form_does_not_save(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:students_grade_add"),
            {"student": self.student.pk, "subject": self.subject.pk, "score": "10.01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("score", response.context["adminform"].form.errors)
        self.assertEqual(Grade.objects.count(), 0)

    def test_search_and_class_filter_find_the_student(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse("admin:students_student_changelist"),
            {"q": self.student.student_code, "class_room__id__exact": self.classroom.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.full_name)


class DemoDataTests(TestCase):
    def test_seed_is_repeatable_and_preserves_edits(self):
        call_command("seed_demo", stdout=StringIO())
        classroom = ClassRoom.objects.get(code="CNTT23A")
        classroom.name = "Tên lớp do người dùng sửa"
        classroom.save()
        student = Student.objects.get(student_code="SV001")
        student.full_name = "Tên sinh viên do người dùng sửa"
        student.save()
        grade = student.grades.first()
        grade.score = Decimal("9.75")
        grade.save()
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(ClassRoom.objects.count(), 2)
        self.assertEqual(Subject.objects.count(), 3)
        self.assertEqual(Student.objects.count(), 6)
        self.assertEqual(Grade.objects.count(), 18)
        self.assertEqual(get_user_model().objects.count(), 0)
        classroom.refresh_from_db()
        student.refresh_from_db()
        grade.refresh_from_db()
        self.assertEqual(classroom.name, "Tên lớp do người dùng sửa")
        self.assertEqual(student.full_name, "Tên sinh viên do người dùng sửa")
        self.assertEqual(grade.score, Decimal("9.75"))


class HealthEndpointTests(TestCase):
    def test_root_redirects_to_admin(self):
        self.assertRedirects(self.client.get("/"), "/admin/", fetch_redirect_response=False)

    def test_database_ready(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_database_failure_returns_generic_503(self):
        with patch("config.urls.connection.cursor", side_effect=DatabaseError("private connection details")):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotContains(response, "private", status_code=503)

    def test_health_endpoint_rejects_post(self):
        self.assertEqual(self.client.post("/healthz").status_code, 405)
