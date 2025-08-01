# Generated by Django 5.2.4 on 2025-07-24 18:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0004_delete_userprofile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='档案名称', max_length=20)),
                ('phone', models.CharField(blank=True, help_text='联系电话', max_length=15, null=True)),
                ('mbti', models.CharField(blank=True, help_text='MBTI性格类型', max_length=8, null=True)),
                ('bio', models.TextField(blank=True, help_text='个人简介', null=True)),
                ('avatar_url', models.URLField(blank=True, help_text='头像URL', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='是否激活')),
                ('is_primary', models.BooleanField(default=False, help_text='是否为主档案')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('address', models.ForeignKey(blank=True, help_text='用户地址', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_profiles', to='authentication.address')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '用户档案',
                'verbose_name_plural': '用户档案',
                'indexes': [models.Index(fields=['user'], name='profiles_us_user_id_65af30_idx'), models.Index(fields=['is_active'], name='profiles_us_is_acti_50c4e6_idx'), models.Index(fields=['is_primary'], name='profiles_us_is_prim_e4ba2e_idx')],
                'constraints': [models.UniqueConstraint(condition=models.Q(('is_primary', True)), fields=('user',), name='unique_primary_profile_per_user')],
            },
        ),
    ]
