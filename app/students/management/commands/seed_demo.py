from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import ClassRoom, Grade, Student, Subject


class Command(BaseCommand):
    help = "Thêm dữ liệu giả để demo; chạy lại không tạo trùng hoặc ghi đè dữ liệu đã sửa."

    @transaction.atomic
    def handle(self, *args, **options):
        classes = []
        for code, name in [("CNTT23A", "Công nghệ thông tin K23 A"), ("CNTT23B", "Công nghệ thông tin K23 B")]:
            classroom, _ = ClassRoom.objects.get_or_create(code=code, defaults={"name": name})
            classes.append(classroom)

        subjects = []
        for code, name in [("CSDL", "Cơ sở dữ liệu"), ("LTWEB", "Lập trình web"), ("TKQT", "Triển khai và quản trị hệ thống phần mềm")]:
            subject, _ = Subject.objects.get_or_create(code=code, defaults={"name": name})
            subjects.append(subject)

        names = ["Nguyễn Minh An", "Trần Ngọc Bình", "Lê Hoàng Chi", "Phạm Minh Dũng", "Hoàng Thanh Hà", "Võ Gia Linh"]
        for index, name in enumerate(names, start=1):
            student, _ = Student.objects.get_or_create(
                student_code=f"SV{index:03d}",
                defaults={
                    "full_name": name,
                    "date_of_birth": date(2005, index, 10),
                    "email": f"sv{index:03d}@example.com",
                    "class_room": classes[0 if index <= 3 else 1],
                },
            )
            for subject_index, subject in enumerate(subjects):
                Grade.objects.get_or_create(
                    student=student,
                    subject=subject,
                    defaults={"score": Decimal("6.00") + Decimal(index + subject_index) / Decimal("2")},
                )

        self.stdout.write(self.style.SUCCESS("Đã bổ sung dữ liệu demo: 2 lớp, 3 môn, 6 sinh viên, 18 điểm. Dữ liệu hiện có được giữ nguyên."))
