# Generated by Django 4.1.5 on 2023-01-11 09:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_comment_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='post_id',
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='backend.post'),
            preserve_default=False,
        ),
    ]
