import os
import uuid
import django
from django.utils import timezone
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduvanta.settings")
django.setup()

from accounts.models import User, ParentChildLink, Notification, ParentInvite, ParentLinkRequest
from accounts.views import _send_email_with_fallback


def main():
    # Create or reset test users
    stu, _ = User.objects.get_or_create(
        email="student.test+1@example.com",
        defaults={
            "username": "student.test+1@example.com",
            "role": "student",
        },
    )
    if not stu.has_usable_password():
        stu.set_password("Pass1234!")
    stu.is_verified = True
    stu.is_profile_completed = False
    stu.save()

    par, _ = User.objects.get_or_create(
        email="parent.test+1@example.com",
        defaults={
            "username": "parent.test+1@example.com",
            "role": "parent",
        },
    )
    if not par.has_usable_password():
        par.set_password("Pass1234!")
    par.is_verified = True
    par.is_profile_completed = False
    par.save()

    # Simulate student sending parent invite email
    ok, err = _send_email_with_fallback(
        "[Test] Parent Link Invitation",
        "<b>Test invite from student to parent</b>",
        ["parent.test+1@example.com"],
    )

    # Simulate parent linking child immediately (and opening approval request)
    ParentChildLink.objects.get_or_create(parent=par, child=stu)
    req, _ = ParentLinkRequest.objects.get_or_create(
        parent=par,
        target_identifier=(stu.email or stu.username).lower(),
        student=stu,
        status="pending",
        defaults={
            "token": uuid.uuid4().hex,
            "expires_at": timezone.now() + timezone.timedelta(days=7),
        },
    )
    Notification.objects.create(
        user=stu,
        category="system",
        severity="info",
        title="Parent link request",
        body=f"{par.username} requested to link as a parent.",
    )

    print("OK_EMAIL=", ok)
    print("PCL_COUNT=", ParentChildLink.objects.count())
    print("INVITES=", ParentInvite.objects.count())
    print("REQ_PENDING=", ParentLinkRequest.objects.filter(status="pending").count())
    print("NOTIFS=", Notification.objects.count())


if __name__ == "__main__":
    main()
