from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.apps import apps
from collections import defaultdict

class Command(BaseCommand):
    help = (
        "Merge duplicate Program rows grouped by name/level into a canonical row. "
        "Dry-run by default; use --apply to perform changes. Optionally prefer a department code when picking canonical."
    )

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run).')
        parser.add_argument('--only-name', action='store_true', help='Group by name only (ignore level).')
        parser.add_argument('--prefer-dept', default='', help='Department code to prefer for canonical pick (optional).')
        parser.add_argument('--case-sensitive', action='store_true', help='Use case-sensitive grouping (default insensitive).')

    def handle(self, *args, **opts):
        apply_changes = bool(opts['apply'])
        only_name = bool(opts['only_name'])
        prefer_dept_code = (opts['prefer_dept'] or '').strip().upper()
        case_sensitive = bool(opts['case_sensitive'])

        Program = apps.get_model('courses', 'Program')
        Department = apps.get_model('courses', 'Department')

        def norm(s: str) -> str:
            s = (s or '').strip()
            return s if case_sensitive else s.lower()

        # Build groups
        groups = defaultdict(list)
        for p in Program.objects.select_related('department').all():
            key_name = norm(p.name)
            key_level = '' if only_name else norm(p.level or '')
            groups[(key_name, key_level)].append(p)

        # Helper: pick canonical program from duplicates
        def pick_canonical(items):
            # Prefer department code match, else smallest id
            if prefer_dept_code:
                for it in items:
                    try:
                        if (getattr(it.department, 'code', '') or '').upper() == prefer_dept_code:
                            return it
                    except Exception:
                        pass
            # Fallback to earliest created (smallest id)
            return sorted(items, key=lambda x: (x.department.code if getattr(x, 'department', None) else 'ZZZ', x.id))[0]

        # Discover reverse FKs to Program throughout all models
        program_model = Program
        rel_fields = []
        for model in apps.get_models():
            for f in model._meta.get_fields():
                if f.is_relation and f.many_to_one and getattr(f.remote_field, 'model', None) is program_model:
                    rel_fields.append((model, f))
        # Provide context
        self.stdout.write(self.style.NOTICE(f"Found {len(groups)} program groups; scanning for duplicates..."))
        total_dupe_groups = 0
        total_merged = 0

        # Transactional merge
        @transaction.atomic
        def do_merge():
            nonlocal total_dupe_groups, total_merged
            for (kname, klevel), items in groups.items():
                if len(items) <= 1:
                    continue
                total_dupe_groups += 1
                # Choose canonical
                canon = pick_canonical(items)
                dupes = [p for p in items if p.id != canon.id]
                self.stdout.write(self.style.WARNING(
                    f"Group name='{kname or ''}' level='{klevel or ''}': canonical id={canon.id} dept={getattr(canon.department,'code', '?')} merging {len(dupes)} duplicates"
                ))

                for d in dupes:
                    # Reassign all FK references from d -> canon
                    for model, fk in rel_fields:
                        q = {fk.name: d}
                        updated = model.objects.filter(**q).update(**{fk.name: canon})
                        if updated:
                            self.stdout.write(f"  - {model._meta.label}.{fk.name}: reassigned {updated}")
                    # Try to delete duplicate
                    d.delete()
                    total_merged += 1

        if apply_changes:
            do_merge()
            self.stdout.write(self.style.SUCCESS(f"Merge complete. Duplicate groups: {total_dupe_groups}, rows deleted: {total_merged}"))
        else:
            # Dry run: simulate and report without mutating
            sim_dupe_groups = 0
            sim_total_dupes = 0
            for (kname, klevel), items in groups.items():
                if len(items) <= 1:
                    continue
                sim_dupe_groups += 1
                canon = pick_canonical(items)
                dupes = [p for p in items if p.id != canon.id]
                sim_total_dupes += len(dupes)
                self.stdout.write(
                    f"[DRY-RUN] Would keep Program id={canon.id} '{getattr(canon,'name','')}' level='{getattr(canon,'level','')}' dept={getattr(canon.department,'code','?')} and delete {[p.id for p in dupes]}"
                )
            self.stdout.write(self.style.SUCCESS(f"Dry-run summary: duplicate groups={sim_dupe_groups}, duplicate rows={sim_total_dupes}. Use --apply to execute."))
