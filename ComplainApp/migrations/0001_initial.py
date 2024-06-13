# Generated by Django 5.0.6 on 2024-06-13 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Complains',
            fields=[
                ('ack_number', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('mobile_number', models.TextField(help_text='Enter Mobile Numbers')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('fraud_type', models.TextField(help_text='Enter Type of Fraud')),
                ('steps_taken', models.TextField()),
                ('images_videos', models.FileField(blank=True, null=True, upload_to='case_files/')),
                ('status', models.CharField(default='Pending', max_length=50)),
            ],
        ),
    ]