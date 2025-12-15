from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from typing import List

from courses.models import Course


DEFAULT_PATTERNS = [
    "test",
    "demo",
    "sample",
    "lorem",
    "ipsum",
    "fake",
    "dummy",
    "placeholder",
]


class Command(BaseCommand):
    help = (
        "Identify and optionally delete likely-fake Course records based on heuristics. "
        "By default this runs in dry-run mode and only reports what would be deleted."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--patterns",
            nargs="*",
            default=DEFAULT_PATTERNS,
            help="Title substrings (case-insensitive) to match as fake, e.g., test demo sample",
        )
        parser.add_argument(
            "--include-unpublished",
            action="store_true",
            help="Include unpublished courses (published=False) as fake candidates",
        )
        parser.add_argument(
            "--include-no-instructor",
            action="store_true",
            help="Include courses with no instructor assigned as fake candidates",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Target ALL Course records, ignoring heuristics (use with caution)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Max number of titles to display in the report (does not limit deletion)",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Actually delete the matching courses (otherwise dry-run)",
        )

    def build_q(self, patterns: List[str], include_unpublished: bool, include_no_instructor: bool) -> Q:
        q = Q()
        # Title patterns
        for p in patterns:
            p = (p or "").strip()
            if not p:
                continue
            q |= Q(title__icontains=p)
        # Additional heuristics
        if include_unpublished:
            q |= Q(published=False)
        if include_no_instructor:
            q |= Q(instructor__isnull=True)
        return q

    def handle(self, *args, **options):
        patterns = options["patterns"] or []
        include_unpublished = options["include_unpublished"]
        include_no_instructor = options["include_no_instructor"]
        target_all = options["all"]
        limit = options["limit"]
        do_delete = options["delete"]

        if target_all:
            qs = Course.objects.all().order_by("title")
        else:
            q = self.build_q(patterns, include_unpublished, include_no_instructor)
            if not q.children:
                raise CommandError(
                    "No criteria specified. Provide --patterns and/or --include-unpublished/--include-no-instructor, or use --all to target everything."
                )
            qs = Course.objects.filter(q).distinct().order_by("title")
        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No matching fake courses found."))
            return

        # Report
        self.stdout.write(
            self.style.WARNING(
                f"Found {total} course(s) matching fake heuristics. Showing up to {limit} titles:"
            )
        )
        for title in qs.values_list("title", flat=True)[:limit]:
            self.stdout.write(f" - {title}")

        if not do_delete:
            self.stdout.write(
                self.style.WARNING(
                    "Dry-run only. Re-run with --delete to actually remove these courses."
                )
            )
            return

        deleted_count, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} object(s) (including related cascades)."))
