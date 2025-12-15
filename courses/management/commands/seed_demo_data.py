from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import Department, Program, Specialization, SubSpecialization, Course
from accounts.models import User

class Command(BaseCommand):
    help = "Seed demo Departments, Specializations, SubSpecializations, and Courses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete existing courses and learning area data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fresh = options.get("fresh", False)
        if fresh:
            self.stdout.write(self.style.WARNING("Wiping existing Courses, SubSpecializations, Specializations, and Departments..."))
            Course.objects.all().delete()
            SubSpecialization.objects.all().delete()
            Specialization.objects.all().delete()
            Department.objects.all().delete()
        self.stdout.write(self.style.NOTICE("Seeding demo learning areas and courses..."))

        # Departments (expanded)
        depts = [
            # Engineering family
            ("CSE", "Computer Science & Engineering"),
            ("ECE", "Electronics & Communication Engineering"),
            ("ME", "Mechanical Engineering"),
            ("CE", "Civil Engineering"),
            ("EE", "Electrical Engineering"),
            ("IT", "Information Technology"),
            ("AI", "Artificial Intelligence"),
            ("ENG", "General Engineering"),
            # Business family
            ("BUS", "Business Management"),
            ("FIN", "Finance"),
            ("MKT", "Marketing"),
            ("HR", "Human Resources"),
            ("OPS", "Operations & Supply Chain"),
            ("ANA", "Business Analytics"),
            # Science family
            ("PHY", "Physics"),
            ("MTH", "Mathematics"),
            ("CHE", "Chemistry"),
            ("DS", "Data Science"),
            ("BT", "Biotechnology"),
            ("SCI", "Natural Sciences"),
            # Other schools
            ("ART", "Arts & Humanities"),
            ("MED", "Medical Sciences"),
            ("LAW", "Law"),
            ("EDU", "Education"),
        ]
        dept_map = {}
        for code, name in depts:
            dept, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
            dept_map[code] = dept

        # Specializations (expanded)
        specs = [
            # CSE
            ("AI", "Artificial Intelligence", "CSE"),
            ("ML", "Machine Learning", "CSE"),
            ("SEC", "Cybersecurity", "CSE"),
            ("CLOUD", "Cloud Computing", "CSE"),
            ("DS", "Data Science", "CSE"),
            ("WEB", "Web Development", "CSE"),
            ("BC", "Blockchain", "CSE"),
            # ECE
            ("VLSI", "VLSI Design", "ECE"),
            ("EMB", "Embedded Systems", "ECE"),
            ("WIRE", "Wireless Communication", "ECE"),
            ("IOT", "Internet of Things", "ECE"),
            ("SIG", "Signal Processing", "ECE"),
            # ME
            ("ROB", "Robotics", "ME"),
            ("AUTO", "Automobile Engineering", "ME"),
            ("THERM", "Thermal Engineering", "ME"),
            ("MFG", "Manufacturing Systems", "ME"),
            # CE
            ("STR", "Structural Engineering", "CE"),
            ("ENV", "Environmental Engineering", "CE"),
            ("TRANS", "Transportation Engineering", "CE"),
            ("SMCTY", "Smart Cities", "CE"),
            # EE
            ("PWR", "Power Systems", "EE"),
            ("REN", "Renewable Energy", "EE"),
            ("CTRL", "Control Systems", "EE"),
            ("SMART", "Smart Grids", "EE"),
            # IT & AI departments
            ("WEBIT", "Web Technologies", "IT"),
            ("BIG", "Big Data Analytics", "IT"),
            ("BLK", "Blockchain", "IT"),
            ("NETSEC", "Network Security", "IT"),
            ("APPAI", "Applied AI", "AI"),
            ("RSPAI", "Responsible AI", "AI"),
            # Business
            ("FIN", "Finance", "BUS"),
            ("MKT", "Marketing", "BUS"),
            ("HR", "Human Resources", "BUS"),
            ("OPSX", "Operations", "BUS"),
            ("ANABIZ", "Business Analytics", "BUS"),
            # Science as departments
            ("QMECH", "Quantum Mechanics", "PHY"),
            ("OPT", "Optics", "PHY"),
            ("SOL", "Solid State", "PHY"),
            ("ALG", "Algebra", "MTH"),
            ("PROB", "Probability", "MTH"),
            ("STAT", "Statistics", "MTH"),
            ("ORG", "Organic Chemistry", "CHE"),
            ("ANL", "Analytical Chemistry", "CHE"),
            ("PHYCH", "Physical Chemistry", "CHE"),
            ("DSCORE", "Core DS", "DS"),
            ("MLAPP", "ML Applications", "DS"),
            ("DATAENG", "Data Engineering", "DS"),
            ("BIOINF", "Bioinformatics", "BT"),
            ("GEN", "Genetic Engineering", "BT"),
            ("PHAR", "Pharma Tech", "BT"),
            # Existing other schools
            ("HIS", "History", "ART"),
            ("LIT", "Literature", "ART"),
            ("CAR", "Cardiology", "MED"),
            ("NEU", "Neurology", "MED"),
            ("CML", "Commercial Law", "LAW"),
            ("CSEDU", "Curriculum Studies", "EDU"),
        ]
        spec_map = {}
        for code, name, dcode in specs:
            dept = dept_map[dcode]
            spec, _ = Specialization.objects.get_or_create(
                name=name, department=dept
            )
            spec_map[code] = spec

        # SubSpecializations
        subs = [
            ("NLP", "Natural Language Processing", "AI"),
            ("CV", "Computer Vision", "AI"),
            ("RL", "Reinforcement Learning", "AI"),
            ("AIE", "AI Ethics", "AI"),
            ("EAI", "Edge AI", "AI"),
            ("NLPAPP", "NLP Applications", "AI"),
            ("SUP", "Supervised Learning", "ML"),
            ("UNSUP", "Unsupervised Learning", "ML"),
            ("DL", "Deep Learning", "ML"),
            ("FD", "Front-end Development", "WEB"),
            ("BD", "Back-end Development", "WEB"),
            ("FS", "Full-Stack", "WEB"),
            ("NETSEC", "Network Security", "SEC"),
            ("APPSEC", "Application Security", "SEC"),
            ("CLSEC", "Cloud Security", "SEC"),
            ("ML", "Machine Learning", "DS"),
            ("DA", "Data Analytics", "DS"),
            ("BIGD", "Big Data", "DS"),
            ("BI", "Business Intelligence", "DS"),
            ("INV", "Investments", "FIN"),
            ("RK", "Risk Management", "FIN"),
            ("IB", "Investment Banking", "FIN"),
            ("SEO", "SEO & Content", "MKT"),
            ("MKTAN", "Marketing Analytics", "MKT"),
            ("REC", "Recruitment", "HR"),
            ("HRAN", "HR Analytics", "HR"),
            ("THERMO", "Thermodynamics", "THERM"),
            ("POW", "Power Systems", "PWR"),
            ("STR", "Structural", "STR"),
            ("ENVENG", "Environmental Quality", "ENV"),
            ("TRANSOP", "Traffic Engineering", "TRANS"),
            ("MOD", "Modern History", "HIS"),
            ("CLIT", "Classical Literature", "LIT"),
            ("QMECH", "Quantum Mechanics", "QMECH"),
            ("ORG", "Organic Chemistry", "ORG"),
            ("MICRO", "Microbiology", "BIOINF"),
            ("LINALG", "Linear Algebra", "ALG"),
            ("PROB", "Probability Theory", "STA"),
            ("INTCAR", "Interventional Cardiology", "CAR"),
            ("NEUIMG", "Neuroimaging", "NEU"),
            ("CORP", "Corporate Law", "CML"),
            ("CURR", "Curriculum Design", "CSEDU"),
            # ECE-focused
            ("CHIP", "Chip Design", "VLSI"),
            ("FPGA", "FPGA", "VLSI"),
            ("LOWP", "Low Power Systems", "VLSI"),
            ("ARM", "ARM Platforms", "EMB"),
            ("RTOS", "RTOS", "EMB"),
            ("IOTFW", "IoT Firmware", "EMB"),
            ("5G", "5G Systems", "WIRE"),
            ("MIMO", "MIMO", "WIRE"),
            ("RF", "RF Design", "WIRE"),
            ("EDGE", "Edge Devices", "IOT"),
            ("IOTPL", "IoT Platforms", "IOT"),
            # Business deep-dives
            ("FINTECH", "FinTech", "FIN"),
            ("WEALTH", "Wealth Management", "FIN"),
            ("SUSTFIN", "Sustainable Finance", "FIN"),
            ("SCM", "Supply Chain", "OPSX"),
            ("LEAN", "Lean Systems", "OPSX"),
            ("OR", "Operations Research", "OPSX"),
            ("BI2", "Business Intelligence", "ANABIZ"),
            ("DM", "Data Mining", "ANABIZ"),
            ("FCST", "Forecasting", "ANABIZ"),
        ]
        subs_map = {}
        for code, name, scode in subs:
            spec = spec_map.get(scode)
            if not spec:
                self.stdout.write(self.style.WARNING(f"Skipping unknown specialization for subspec {code}: {scode}"))
                continue
            ss, _ = SubSpecialization.objects.get_or_create(
                name=name, specialization=spec
            )
            subs_map[code] = ss

        # Ensure there is at least one instructor for courses
        instructor = User.objects.filter(role='teacher').first()
        if not instructor:
            instructor = User.objects.filter(is_staff=True).first()

        # Courses (expanded)
        courses = [
            ("Introduction to AI", dept_map["CSE"], spec_map["AI"], subs_map.get("NLP")),
            ("Deep Learning Fundamentals", dept_map["CSE"], spec_map["AI"], subs_map.get("CV")),
            ("Reinforcement Learning", dept_map["CSE"], spec_map["AI"], subs_map.get("RL")),
            ("Applied NLP", dept_map["CSE"], spec_map["AI"], subs_map.get("NLPAPP")),
            ("Front-end with React", dept_map["CSE"], spec_map["WEB"], subs_map.get("FD")),
            ("Back-end with Django", dept_map["CSE"], spec_map["WEB"], subs_map.get("BD")),
            ("Full‑Stack Web Development", dept_map["CSE"], spec_map["WEB"], subs_map.get("FS")),
            ("Network Security Basics", dept_map["CSE"], spec_map["SEC"], subs_map.get("NETSEC")),
            ("Application Security", dept_map["CSE"], spec_map["SEC"], subs_map.get("APPSEC")),
            ("Machine Learning 101", dept_map["CSE"], spec_map["DS"], subs_map.get("ML")),
            ("Data Analytics with Python", dept_map["CSE"], spec_map["DS"], subs_map.get("DA")),
            ("Big Data Systems", dept_map["IT"], spec_map["BIG"], subs_map.get("BIGD")),
            ("Blockchain Fundamentals", dept_map["IT"], spec_map["BLK"], subs_map.get("BI")),
            ("Corporate Finance", dept_map["BUS"], spec_map["FIN"], subs_map.get("INV")),
            ("Risk Management", dept_map["BUS"], spec_map["FIN"], subs_map.get("RK")),
            ("Investment Banking", dept_map["BUS"], spec_map["FIN"], subs_map.get("IB")),
            ("Digital Marketing Essentials", dept_map["BUS"], spec_map["MKT"], subs_map.get("SEO")),
            ("Marketing Analytics", dept_map["BUS"], spec_map["MKT"], subs_map.get("MKTAN")),
            ("Recruitment Strategy", dept_map["BUS"], spec_map["HR"], subs_map.get("REC")),
            ("HR Analytics", dept_map["BUS"], spec_map["HR"], subs_map.get("HRAN")),
            ("Thermodynamics I", dept_map["ME"], spec_map["THERM"], subs_map.get("THERMO")),
            ("Power Systems", dept_map["EE"], spec_map["PWR"], subs_map.get("POW")),
            ("Structural Analysis", dept_map["CE"], spec_map["STR"], subs_map.get("STR")),
            ("Chip Design", dept_map["ECE"], spec_map["VLSI"], subs_map.get("CHIP")),
            ("FPGA Design", dept_map["ECE"], spec_map["VLSI"], subs_map.get("FPGA")),
            ("Low Power VLSI", dept_map["ECE"], spec_map["VLSI"], subs_map.get("LOWP")),
            ("Embedded ARM", dept_map["ECE"], spec_map["EMB"], subs_map.get("ARM")),
            ("RTOS in Embedded", dept_map["ECE"], spec_map["EMB"], subs_map.get("RTOS")),
            ("IoT Firmware", dept_map["ECE"], spec_map["EMB"], subs_map.get("IOTFW")),
            ("5G Systems", dept_map["ECE"], spec_map["WIRE"], subs_map.get("5G")),
            ("MIMO Techniques", dept_map["ECE"], spec_map["WIRE"], subs_map.get("MIMO")),
            ("RF Design Basics", dept_map["ECE"], spec_map["WIRE"], subs_map.get("RF")),
            ("Edge Devices", dept_map["ECE"], spec_map["IOT"], subs_map.get("EDGE")),
            ("IoT Platforms", dept_map["ECE"], spec_map["IOT"], subs_map.get("IOTPL")),
            ("Modern World History", dept_map["ART"], spec_map["HIS"], subs_map.get("MOD")),
            ("Classical Literature", dept_map["ART"], spec_map["LIT"], subs_map.get("CLIT")),
            ("Quantum Mechanics", dept_map["PHY"], spec_map["QMECH"], subs_map.get("QMECH")),
            ("Organic Chemistry", dept_map["CHE"], spec_map["ORG"], subs_map.get("ORG")),
            ("Microbiology", dept_map["BT"], spec_map["BIOINF"], subs_map.get("MICRO")),
            ("Linear Algebra", dept_map["MTH"], spec_map["ALG"], subs_map.get("LINALG")),
            ("Probability & Statistics", dept_map["MTH"], spec_map["PROB"], subs_map.get("PROB")),
            ("Interventional Cardiology", dept_map["MED"], spec_map["CAR"], subs_map.get("INTCAR")),
            ("Neuroimaging", dept_map["MED"], spec_map["NEU"], subs_map.get("NEUIMG")),
            ("Corporate Law", dept_map["LAW"], spec_map["CML"], subs_map.get("CORP")),
            ("Curriculum Design", dept_map["EDU"], spec_map["CSEDU"], subs_map.get("CURR")),
        ]
        from django.utils.text import slugify
        created_courses = 0
        # Programs per department (expanded)
        program_defs = {
            # Engineering/CS families
            "CSE": [("B.Tech", "UG", "4 years"), ("M.Tech", "PG", "2 years"), ("MCA", "PG", "2 years"), ("PhD", "Doctorate", None), ("Post-Doctoral Research", "Post-Doctoral", None)],
            "ECE": [("B.Tech", "UG", "4 years"), ("M.Tech", "PG", "2 years"), ("PhD", "Doctorate", None), ("Post-Doctoral Research", "Post-Doctoral", None)],
            "ME": [("B.Tech", "UG", "4 years"), ("M.Tech", "PG", "2 years"), ("PhD", "Doctorate", None)],
            "CE": [("B.Tech", "UG", "4 years"), ("M.Tech", "PG", "2 years"), ("Diploma", "Diploma", None), ("PhD", "Doctorate", None)],
            "EE": [("B.Tech", "UG", "4 years"), ("M.Tech", "PG", "2 years"), ("PhD", "Doctorate", None)],
            "IT":  [("B.Tech", "UG", "4 years"), ("M.Tech", "PG", "2 years"), ("MCA", "PG", "2 years"), ("PhD", "Doctorate", None)],
            "AI": [("B.Tech", "UG", "4 years"), ("M.Tech", "PG", "2 years"), ("PhD", "Doctorate", None)],
            # Business/Management
            "BUS": [("BBA", "UG", "3 years"), ("MBA", "PG", "2 years"), ("PhD", "Doctorate", None), ("Post-Doctoral Research", "Post-Doctoral", None)],
            "FIN": [("BBA", "UG", "3 years"), ("MBA", "PG", "2 years"), ("PhD", "Doctorate", None)],
            "MKT": [("BBA", "UG", "3 years"), ("MBA", "PG", "2 years"), ("PhD", "Doctorate", None)],
            "HR": [("BBA", "UG", "3 years"), ("MBA", "PG", "2 years"), ("PhD", "Doctorate", None)],
            "OPS": [("BBA", "UG", "3 years"), ("MBA", "PG", "2 years"), ("PhD", "Doctorate", None)],
            "ANA": [("BBA", "UG", "3 years"), ("MBA", "PG", "2 years"), ("PhD", "Doctorate", None)],
            # Arts/Humanities
            "ART": [("B.A.", "UG", None), ("M.A.", "PG", None)],
            # Sciences
            "PHY": [("B.Sc (Hons.)", "UG", None), ("M.Sc.", "PG", None), ("PhD", "Doctorate", None), ("Post-Doctoral Research", "Post-Doctoral", None)],
            "MTH": [("B.Sc (Hons.)", "UG", None), ("M.Sc.", "PG", None), ("PhD", "Doctorate", None)],
            "CHE": [("B.Sc (Hons.)", "UG", None), ("M.Sc.", "PG", None), ("PhD", "Doctorate", None)],
            "DS": [("B.Sc (Hons.)", "UG", None), ("M.Sc.", "PG", None), ("PhD", "Doctorate", None)],
            "BT": [("B.Sc (Hons.)", "UG", None), ("M.Sc.", "PG", None), ("PhD", "Doctorate", None), ("Post-Doctoral Research", "Post-Doctoral", None)],
            "SCI": [("B.Sc.", "UG", None), ("M.Sc.", "PG", None), ("PhD", "Doctorate", None)],
            # Medicine/Education
            "MED": [("MBBS", "UG", None), ("MD", "PG", None), ("PhD", "Doctorate", None), ("Post-Doctoral Research", "Post-Doctoral", None)],
            "EDU": [("B.Ed", "UG", None), ("M.Ed", "PG", None), ("PhD", "Doctorate", None)],
        }
        for code, dept in dept_map.items():
            for name, level, duration in program_defs.get(code, []):
                Program.objects.get_or_create(
                    department=dept,
                    name=name,
                    defaults={"code": name.replace('.', '').replace(' ', '').upper(), "level": level, "duration": duration},
                )
        for title, dept, spec, subspec in courses:
            base_slug = slugify(title)
            slug = base_slug
            # Ensure slug uniqueness in case of collisions
            i = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            defaults = {
                "title": title,
                "department": dept,
                "specialization": spec,
                "subspecialization": subspec,
            }
            if instructor:
                defaults["instructor"] = instructor
            obj, was_created = Course.objects.get_or_create(slug=slug, defaults=defaults)
            if was_created:
                created_courses += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete:{Program.objects.count()} programs, {Department.objects.count()} depts, {Specialization.objects.count()} specs, "
            f"{SubSpecialization.objects.count()} subs, {created_courses} courses created (or already present)."
        ))
