from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.management import call_command

class Command(BaseCommand):
    help = "Purge and reseed learning areas. Use --size and --include-tags. WARNING: deletes courses and related records."

    def add_arguments(self, parser):
        parser.add_argument('--size', choices=['small', 'medium', 'large'], default='large', help='Dataset size preset (affects only future extensions).')
        parser.add_argument('--include-tags', action='store_true', help='Reapply tags (seed command already applies).')
        parser.add_argument('--noinput', action='store_true', help='Do not prompt for confirmation.')

    @transaction.atomic
    def handle(self, *args, **opts):
        size = opts['size']
        include_tags = opts['include_tags']
        noinput = opts['noinput']

        from courses.models import (
            Course, Module, Lesson, CourseInstructor, Enrollment, Submission,
            Specialization, SubSpecialization, Program, Tag
        )

        if not noinput:
            confirm = input("This will DELETE all Courses, Modules, Lessons, CourseInstructors, Enrollments, Submissions, and Specializations/SubSpecializations/Programs, then reseed. Continue? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Aborted.'))
                return

        # Delete in safe order
        self.stdout.write(self.style.NOTICE('Purging course-related data...'))
        deleted_counts = {}
        for model in (CourseInstructor, Submission, Enrollment, Lesson, Module, Course):
            cnt, _ = model.objects.all().delete()
            deleted_counts[model.__name__] = cnt
        self.stdout.write(self.style.SUCCESS('Courses & related removed.'))

        self.stdout.write(self.style.NOTICE('Purging learning areas (specializations/subspecializations/programs)...'))
        for model in (SubSpecialization, Specialization, Program):
            cnt, _ = model.objects.all().delete()
            deleted_counts[model.__name__] = cnt
        self.stdout.write(self.style.SUCCESS('Learning areas removed.'))

        # Keep Departments and Tags, reseed will reuse Departments or create if missing
        self.stdout.write(self.style.NOTICE('Reseeding datasets...'))
        call_command('seed_learning_areas')

        if include_tags:
            # seed_learning_areas already applies tags heuristically; re-run to ensure tags exist and associated
            call_command('seed_learning_areas')

        self.stdout.write(self.style.SUCCESS('Reseed complete. Deleted: ' + ', '.join(f"{k}={v}" for k,v in deleted_counts.items())))
