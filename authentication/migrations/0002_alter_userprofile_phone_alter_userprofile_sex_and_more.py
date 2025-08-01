# Generated by Django 5.2.4 on 2025-07-24 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(max_length=15),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(choices=[('男', '男'), ('女', '女'), ('其他', '其他')], help_text='性别', max_length=10),
        ),
        migrations.AlterUniqueTogether(
            name='address',
            unique_together={('country', 'province', 'city', 'district')},
        ),
    ]
