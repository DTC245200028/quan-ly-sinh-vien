import decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ClassRoom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="Mã lớp")),
                ("name", models.CharField(max_length=100, verbose_name="Tên lớp")),
            ],
            options={"verbose_name": "Lớp học", "verbose_name_plural": "Lớp học", "ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Subject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="Mã môn học")),
                ("name", models.CharField(max_length=150, verbose_name="Tên môn học")),
            ],
            options={"verbose_name": "Môn học", "verbose_name_plural": "Môn học", "ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_code", models.CharField(max_length=20, unique=True, verbose_name="Mã sinh viên")),
                ("full_name", models.CharField(max_length=150, verbose_name="Họ và tên")),
                ("date_of_birth", models.DateField(verbose_name="Ngày sinh")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="Email")),
                ("class_room", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="students", to="students.classroom", verbose_name="Lớp học")),
            ],
            options={"verbose_name": "Sinh viên", "verbose_name_plural": "Sinh viên", "ordering": ["student_code"]},
        ),
        migrations.CreateModel(
            name="Grade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.DecimalField(decimal_places=2, help_text="Nhập điểm từ 0 đến 10. Mỗi sinh viên có một điểm cho mỗi môn học.", max_digits=4, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0")), django.core.validators.MaxValueValidator(decimal.Decimal("10"))], verbose_name="Điểm")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="grades", to="students.student", verbose_name="Sinh viên")),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="grades", to="students.subject", verbose_name="Môn học")),
            ],
            options={
                "verbose_name": "Điểm số",
                "verbose_name_plural": "Điểm số",
                "ordering": ["student__student_code", "subject__code"],
                "constraints": [
                    models.UniqueConstraint(fields=("student", "subject"), name="unique_student_subject_grade"),
                    models.CheckConstraint(condition=models.Q(("score__gte", 0), ("score__lte", 10)), name="grade_score_between_0_and_10"),
                ],
            },
        ),
    ]
