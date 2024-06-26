# Generated by Django 5.0.6 on 2024-06-14 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ComplainApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='complains',
            name='address',
            field=models.TextField(blank=True, help_text='Enter Address'),
        ),
        migrations.AddField(
            model_name='complains',
            name='investigating_officer',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='complains',
            name='steps_taken',
            field=models.TextField(blank=True, null=True),
        ),
    ]
