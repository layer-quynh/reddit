# Generated by Django 4.1.5 on 2023-01-12 05:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_remove_post_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='parent',
        ),
        migrations.AlterField(
            model_name='comment',
            name='path',
            field=models.CharField(default='', max_length=255),
        ),
    ]