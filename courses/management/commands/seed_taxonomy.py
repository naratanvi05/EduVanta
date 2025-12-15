from django.core.management.base import BaseCommand
from courses.models import Department, Specialization, SubSpecialization, Course
from accounts.models import User

class Command(BaseCommand):
    help = "Seed Departments, Specializations, SubSpecializations, and sample Courses for demo/testing."

    def handle(self, *args, **options):
        created_counts = {"departments": 0, "specializations": 0, "subspecializations": 0, "courses": 0}

        # Departments
        depts = [
            {"code": "CS", "name": "Computer Science"},
            {"code": "MAT", "name": "Mathematics"},
            {"code": "PHY", "name": "Physics"},
        ]
        dept_objs = {}
        for d in depts:
            obj, created = Department.objects.get_or_create(code=d["code"], defaults={"name": d["name"]})
            dept_objs[d["code"]] = obj
            if created:
                created_counts["departments"] += 1

        # Specializations
        specs = [
            {"name": "AI & ML", "department": "CS"},
            {"name": "Web Development", "department": "CS"},
            {"name": "Algebra", "department": "MAT"},
            {"name": "Calculus", "department": "MAT"},
            {"name": "Quantum Mechanics", "department": "PHY"},
        ]
        spec_objs = {}
        for s in specs:
            dept = dept_objs[s["department"]]
            obj, created = Specialization.objects.get_or_create(name=s["name"], department=dept)
            spec_objs[(s["name"], s["department"])]= obj
            if created:
                created_counts["specializations"] += 1

        # SubSpecializations
        subs = [
            {"name": "Deep Learning", "specialization": ("AI & ML", "CS")},
            {"name": "NLP", "specialization": ("AI & ML", "CS")},
            {"name": "Frontend", "specialization": ("Web Development", "CS")},
            {"name": "Backend", "specialization": ("Web Development", "CS")},
            {"name": "Abstract Algebra", "specialization": ("Algebra", "MAT")},
            {"name": "Real Analysis", "specialization": ("Calculus", "MAT")},
        ]
        subs_objs = {}
        for ss in subs:
            spec = spec_objs[ss["specialization"]]
            obj, created = SubSpecialization.objects.get_or_create(name=ss["name"], specialization=spec)
            subs_objs[(ss["name"], ss["specialization"])]= obj
            if created:
                created_counts["subspecializations"] += 1

        # Sample courses
        courses = [
            {"title": "Intro to Machine Learning", "slug": "intro-ml", "dept": "CS", "spec": ("AI & ML", "CS"), "subspec": ("Deep Learning", ("AI & ML", "CS"))},
            {"title": "Modern Web Apps", "slug": "modern-web-apps", "dept": "CS", "spec": ("Web Development", "CS"), "subspec": ("Frontend", ("Web Development", "CS"))},
            {"title": "Abstract Algebra I", "slug": "abstract-algebra-1", "dept": "MAT", "spec": ("Algebra", "MAT"), "subspec": None},
        ]
        # Try to assign an instructor if exists
        instructor = User.objects.filter(role='teacher').first()
        for c in courses:
            dept = dept_objs[c["dept"]]
            spec = spec_objs[c["spec"]]
            subspec = None
            if c["subspec"]:
                subspec = subs_objs[c["subspec"]]
            obj, created = Course.objects.get_or_create(
                slug=c["slug"],
                defaults={
                    "title": c["title"],
                    "department": dept,
                    "specialization": spec,
                    "subspecialization": subspec,
                    "instructor": instructor,
                    "published": True,
                    "description": f"Auto-seeded course: {c['title']}",
                }
            )
            if created:
                created_counts["courses"] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. Created Departments={created_counts['departments']}, "
            f"Specializations={created_counts['specializations']}, SubSpecializations={created_counts['subspecializations']}, "
            f"Courses={created_counts['courses']}"
        ))
