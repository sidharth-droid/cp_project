# Generated by Django 5.0.6 on 2024-06-26 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ComplainApp', '0010_fir'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fir',
            name='date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='fir',
            name='date_of_dispatch_from_ps',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
