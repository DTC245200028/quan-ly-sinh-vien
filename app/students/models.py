from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ClassRoom(models.Model):
    code = models.CharField("Mã lớp", max_length=20, unique=True)
    name = models.CharField("Tên lớp", max_length=100)

    class Meta:
        ordering = ["code"]
        verbose_name = "Lớp học"
        verbose_name_plural = "Lớp học"

    def __str__(self):
        return f"{self.code} — {self.name}"


class Student(models.Model):
    student_code = models.CharField("Mã sinh viên", max_length=20, unique=True)
    full_name = models.CharField("Họ và tên", max_length=150)
    date_of_birth = models.DateField("Ngày sinh")
    email = models.EmailField("Email", blank=True)
    class_room = models.ForeignKey(
        ClassRoom,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="Lớp học",
    )

    class Meta:
        ordering = ["student_code"]
        verbose_name = "Sinh viên"
        verbose_name_plural = "Sinh viên"

    def __str__(self):
        return f"{self.student_code} — {self.full_name}"


class Subject(models.Model):
    code = models.CharField("Mã môn học", max_length=20, unique=True)
    name = models.CharField("Tên môn học", max_length=150)

    class Meta:
        ordering = ["code"]
        verbose_name = "Môn học"
        verbose_name_plural = "Môn học"

    def __str__(self):
        return f"{self.code} — {self.name}"


class Grade(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="grades",
        verbose_name="Sinh viên",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="grades",
        verbose_name="Môn học",
    )
    score = models.DecimalField(
        "Điểm",
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("10"))],
        help_text="Nhập điểm từ 0 đến 10. Mỗi sinh viên có một điểm cho mỗi môn học.",
    )

    class Meta:
        ordering = ["student__student_code", "subject__code"]
        verbose_name = "Điểm số"
        verbose_name_plural = "Điểm số"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "subject"], name="unique_student_subject_grade"
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=0) & models.Q(score__lte=10),
                name="grade_score_between_0_and_10",
            ),
        ]

    def __str__(self):
        return f"{self.student.student_code} / {self.subject.code}: {self.score}"
