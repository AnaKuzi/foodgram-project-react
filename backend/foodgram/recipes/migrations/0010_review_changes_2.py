# Generated by Django 2.2.19 on 2023-01-20 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_review_changes_1'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(help_text='Формат - HEX', max_length=7, unique=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(help_text='Создайте уникальную ссылку', max_length=200, unique=True),
        ),
    ]