# Generated by Django 4.2.11 on 2024-08-12 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0022_passwordresettoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='passwordresettoken',
            name='token',
            field=models.IntegerField(editable=False, unique=True),
        ),
    ]
