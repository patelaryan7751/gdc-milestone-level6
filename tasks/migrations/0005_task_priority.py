# Generated by Django 4.0.1 on 2022-02-07 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_task_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
    ]
