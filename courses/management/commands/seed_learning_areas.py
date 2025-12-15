from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = "Seed essential Departments, Programs, Specializations, SubSpecializations, and a few Courses for the Profile Setup page. Safe to run multiple times."

    @transaction.atomic
    def handle(self, *args, **options):
        from courses.models import Department, Program, Specialization, SubSpecialization, Course

        # Departments
        dept_specs = [
            ("CSE", "Computer Science & Engineering"),
            ("ECE", "Electronics & Communication"),
            ("AI", "Artificial Intelligence"),
            ("BUS", "Business Management"),
        ]
        dept_map = {}
        for code, name in dept_specs:
            d, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
            dept_map[code] = d
        self.stdout.write(self.style.SUCCESS(f"Departments ready: {', '.join(dept_map.keys())}"))

        # Programs (one per department as examples)
        prog_specs = [
            ("B.Tech", "Undergraduate program in engineering", "CSE"),
            ("M.Tech", "Postgraduate program in engineering", "ECE"),
            ("BBA", "Undergraduate in management", "BUS"),
            ("MSc AI", "Masters in Artificial Intelligence", "AI"),
        ]
        prog_map = {}
        for name, level, dept_code in prog_specs:
            d = dept_map[dept_code]
            p, _ = Program.objects.get_or_create(department=d, name=name, defaults={"level": level})
            if p.level != level and level:
                p.level = level
                p.save(update_fields=["level"])
            prog_map[name] = p
        self.stdout.write(self.style.SUCCESS(f"Programs ready: {', '.join(prog_map.keys())}"))

        # Specializations
        spec_specs = [
            ("Data Science", "CSE"),
            ("Computer Networks", "CSE"),
            ("VLSI", "ECE"),
            ("Digital Signal Processing", "ECE"),
            ("Machine Learning", "AI"),
            ("Deep Learning", "AI"),
            ("Marketing", "BUS"),
            ("Finance", "BUS"),
        ]
        spec_map = {}
        for name, dept_code in spec_specs:
            d = dept_map[dept_code]
            s, _ = Specialization.objects.get_or_create(name=name, department=d)
            spec_map[name] = s
        self.stdout.write(self.style.SUCCESS(f"Specializations ready: {', '.join(spec_map.keys())}"))

        # SubSpecializations
        subspec_specs = [
            ("NLP", "Machine Learning"),
            ("Computer Vision", "Deep Learning"),
            ("Time Series", "Data Science"),
            ("Wireless Networks", "Computer Networks"),
            ("Portfolio Theory", "Finance"),
            ("Brand Strategy", "Marketing"),
        ]
        subspec_map = {}
        for name, spec_name in subspec_specs:
            s = spec_map.get(spec_name)
            if not s:
                continue
            ss, _ = SubSpecialization.objects.get_or_create(name=name, specialization=s)
            subspec_map[name] = ss
        self.stdout.write(self.style.SUCCESS(f"SubSpecializations ready: {', '.join(subspec_map.keys())}"))

        # Courses
        course_specs = [
            ("Intro to Data Science", "CSE", "Data Science", "Time Series"),
            ("Neural Networks Basics", "AI", "Deep Learning", "Computer Vision"),
            ("Marketing Analytics", "BUS", "Marketing", None),
            ("Advanced VLSI", "ECE", "VLSI", None),
        ]
        created = 0
        from django.utils.text import slugify
        from django.db import IntegrityError
        for title, dcode, sname, ssname in course_specs:
            d = dept_map[dcode]
            s = spec_map.get(sname)
            ss = subspec_map.get(ssname) if ssname else None
            # Ensure a unique slug from title
            base_slug = slugify(title) or f"course-{dcode.lower()}"
            slug = base_slug
            n = 2
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            c, was_created = Course.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "department": d,
                    "specialization": s or Specialization.objects.filter(department=d).first(),
                    "subspecialization": ss,
                    "published": True,
                }
            )
            if not was_created:
                # Backfill relations if missing
                updates = []
                if c.department_id is None:
                    c.department = d; updates.append("department")
                if (s or c.specialization_id is None) and not c.specialization_id:
                    c.specialization = s; updates.append("specialization")
                if ss and getattr(c, 'subspecialization_id', None) is None:
                    c.subspecialization = ss; updates.append("subspecialization")
                if updates:
                    c.save(update_fields=updates)
            else:
                created += 1
        # ---- Additional comprehensive university-level seeding ----
        # 1) Extra Departments
        extra_departments = [
            ("ME", "Mechanical Engineering"),
            ("CE", "Civil Engineering"),
            ("EE", "Electrical Engineering"),
            ("IT", "Information Technology"),
            ("CHE", "Chemical Engineering"),
            ("PHY", "Physics"),
            ("MTH", "Mathematics"),
            ("BIO", "Biotechnology"),
            ("LAW", "Law"),
            ("MED", "Medicine"),
            ("ART", "Arts"),
            ("EDU", "Education"),
        ]
        for code, name in extra_departments:
            d, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
            dept_map[code] = d

        # 2) Extra Programs per department
        extra_programs_by_dept = {
            "CSE": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate"), ("PhD", "Doctoral"), ("BCA", "Undergraduate"), ("MCA", "Postgraduate")],
            "ECE": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate"), ("PhD", "Doctoral")],
            "ME": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate")],
            "CE": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate")],
            "EE": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate")],
            "IT": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate"), ("BCA", "Undergraduate"), ("MCA", "Postgraduate")],
            "CHE": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate")],
            "PHY": [("B.Sc", "Undergraduate"), ("M.Sc", "Postgraduate"), ("PhD", "Doctoral")],
            "MTH": [("B.Sc", "Undergraduate"), ("M.Sc", "Postgraduate"), ("PhD", "Doctoral")],
            "BIO": [("B.Tech", "Undergraduate"), ("M.Tech", "Postgraduate"), ("PhD", "Doctoral")],
            "BUS": [("BBA", "Undergraduate"), ("MBA", "Postgraduate"), ("PhD", "Doctoral")],
            "LAW": [("LLB", "Undergraduate"), ("LLM", "Postgraduate")],
            "MED": [("MBBS", "Undergraduate"), ("MD", "Postgraduate")],
            "ART": [("BA", "Undergraduate"), ("MA", "Postgraduate")],
            "EDU": [("B.Ed", "Undergraduate"), ("M.Ed", "Postgraduate")],
            "AI": [("MSc AI", "Postgraduate"), ("PhD", "Doctoral")],
        }
        for dcode, items in extra_programs_by_dept.items():
            d = dept_map.get(dcode)
            if not d:
                continue
            for name, level in items:
                Program.objects.get_or_create(department=d, name=name, defaults={"level": level})

        # 3) Extra Specializations by department
        extra_specs_by_dept = {
            "CSE": ["Operating Systems", "Algorithms", "Databases", "Cybersecurity", "Cloud Computing"],
            "ECE": ["Embedded Systems", "Control Systems", "RF & Microwaves"],
            "ME": ["Thermal Engineering", "Robotics", "Manufacturing"],
            "CE": ["Structural Engineering", "Transportation", "Geotechnical"],
            "EE": ["Power Systems", "Power Electronics", "Signal Processing"],
            "IT": ["Software Engineering", "DevOps", "Information Security"],
            "CHE": ["Process Engineering", "Polymer Science"],
            "PHY": ["Quantum Mechanics", "Astrophysics", "Optics"],
            "MTH": ["Statistics", "Applied Mathematics", "Pure Mathematics"],
            "BIO": ["Genetic Engineering", "Bioinformatics"],
            "BUS": ["Operations", "Human Resources", "Business Analytics"],
            "LAW": ["Corporate Law", "Criminal Law"],
            "MED": ["Cardiology", "Neurology"],
            "ART": ["Psychology", "Sociology", "History"],
            "EDU": ["Curriculum Design", "Educational Technology"],
            "AI": ["Reinforcement Learning", "Explainable AI"],
        }
        spec_objs = {}  # (dept_code, spec_name) -> obj
        for dcode, names in extra_specs_by_dept.items():
            d = dept_map.get(dcode)
            if not d:
                continue
            for name in names:
                s, _ = Specialization.objects.get_or_create(department=d, name=name, defaults={"slug": ""})
                spec_objs[(dcode, name)] = s

        # 4) SubSpecializations per (dept, spec)
        extra_subspecs = {
            ("CSE", "Cybersecurity"): ["Network Security", "Application Security"],
            ("CSE", "Cloud Computing"): ["Distributed Systems", "Serverless"],
            ("ECE", "Embedded Systems"): ["IoT", "Real-time Systems"],
            ("ME", "Robotics"): ["Autonomous Systems", "Industrial Robotics"],
            ("CE", "Structural Engineering"): ["Earthquake Engineering", "Bridge Design"],
            ("EE", "Power Electronics"): ["Drives", "Converters"],
            ("IT", "DevOps"): ["CI/CD", "SRE"],
            ("PHY", "Optics"): ["Laser Physics", "Photonics"],
            ("MTH", "Statistics"): ["Bayesian", "Time Series"],
            ("BIO", "Bioinformatics"): ["Genomics", "Proteomics"],
            ("BUS", "Business Analytics"): ["Data Visualization", "Predictive Analytics"],
            ("LAW", "Corporate Law"): ["M&A", "Compliance"],
            ("MED", "Cardiology"): ["Interventional", "Electrophysiology"],
            ("ART", "Psychology"): ["Cognitive", "Clinical"],
            ("EDU", "Educational Technology"): ["LMS Design", "Adaptive Learning"],
            ("AI", "Reinforcement Learning"): ["Multi-agent", "Model-based RL"],
        }
        subspec_created = 0
        for (dcode, sname), subs in extra_subspecs.items():
            s = spec_objs.get((dcode, sname)) or Specialization.objects.filter(department__code=dcode, name=sname).first()
            if not s:
                continue
            for ss_name in subs:
                SubSpecialization.objects.get_or_create(specialization=s, name=ss_name)
                subspec_created += 1

        # 5) Auto-generate Courses for each specialization (2 per spec)
        from django.utils.text import slugify
        new_courses = 0
        for (dcode, sname), s in spec_objs.items():
            d = dept_map.get(dcode)
            if not d or not s:
                continue
            titles = [f"Introduction to {sname}", f"Advanced Topics in {sname}"]
            for title in titles:
                base_slug = slugify(title) or f"course-{dcode.lower()}"
                slug = base_slug
                n = 2
                while Course.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{n}"
                    n += 1
                c, created_c = Course.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "title": title,
                        "department": d,
                        "specialization": s,
                        "published": True,
                    }
                )
                if created_c:
                    new_courses += 1

        # 6) Tagging and featured flags via tags
        from courses.models import Tag
        tag_names = ["featured", "popular", "ai", "data-science", "fullstack", "cybersecurity", "cloud"]
        tag_map = {}
        for tn in tag_names:
            t, _ = Tag.objects.get_or_create(name=tn, defaults={"slug": tn})
            tag_map[tn] = t
        # Heuristic tagging by specialization and title
        for c in Course.objects.all():
            spec_name = (getattr(c.specialization, 'name', '') or '').lower()
            title_l = (c.title or '').lower()
            to_add = []
            if any(k in spec_name for k in ["machine", "deep", "reinforcement", "ai"]):
                to_add.extend([tag_map["ai"], tag_map["featured"]])
            if any(k in spec_name for k in ["data", "analytics"]) or "data" in title_l:
                to_add.append(tag_map["data-science"])
            if any(k in spec_name for k in ["cyber", "security"]) or "security" in title_l:
                to_add.append(tag_map["cybersecurity"])
            if any(k in spec_name for k in ["cloud"]) or "cloud" in title_l:
                to_add.append(tag_map["cloud"])
            if any(k in spec_name for k in ["software", "devops"]) or "introduction" in title_l:
                to_add.append(tag_map["fullstack"])
            # make popular a default for intro courses
            if title_l.startswith('introduction'):
                to_add.append(tag_map["popular"])
            if to_add:
                c.tags.add(*{t.id for t in to_add})
        self.stdout.write(self.style.SUCCESS(f"Courses ready (new={created + new_courses}). Tags applied."))

        self.stdout.write(self.style.SUCCESS("Learning areas seeding complete."))
