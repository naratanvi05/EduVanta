from django.db import migrations, models


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
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_remove_user_departments_remove_user_specializations_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand_name', models.CharField(default='EduVanta', max_length=120)),
                ('brand_color', models.CharField(default='#4f46e5', max_length=20)),
                ('logo_url', models.URLField(blank=True, default='')),
                ('email_subject_prefix', models.CharField(blank=True, default='[EduVanta]', max_length=60)),
            ],
            options={
                'verbose_name': 'Site Setting',
                'verbose_name_plural': 'Site Settings',
            },
        ),
        migrations.RunPython(seed_sitesetting, reverse_code=noop),
    ]
