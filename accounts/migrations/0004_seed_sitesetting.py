from django.db import migrations


def seed_sitesetting(apps, schema_editor):
    SiteSetting = apps.get_model('accounts', 'SiteSetting')
    if not SiteSetting.objects.exists():
        SiteSetting.objects.create(
            brand_name='EduVanta',
            brand_color='#4f46e5',
            logo_url='',
            email_subject_prefix='[EduVanta]'
        )


def noop(apps, schema_editor):
    # We don't delete settings on reverse migration
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_sitesetting_model'),
    ]

    operations = [
        migrations.RunPython(seed_sitesetting, reverse_code=noop),
    ]
