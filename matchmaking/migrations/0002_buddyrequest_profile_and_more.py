# Generated by Django 5.2.4 on 2025-07-25 00:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_alter_event_options_event_introduction_and_more'),
        ('matchmaking', '0001_initial'),
        ('profiles', '0002_userprofile_contact_info'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='buddyrequest',
            name='profile',
            field=models.ForeignKey(blank=True, help_text='使用的用户档案', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='buddy_requests', to='profiles.userprofile'),
        ),
        migrations.AddIndex(
            model_name='buddyrequest',
            index=models.Index(fields=['profile'], name='matchmaking_profile_5616a0_idx'),
        ),
    ]
