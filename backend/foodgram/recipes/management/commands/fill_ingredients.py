import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Загрузка ингредиентов.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Началось заполнение БД'))
        with open(
            os.path.join(DATA_ROOT, 'ingredients.json'), 'r', encoding='utf-8'
        ) as data_file_ingredients:
            ingredient_data = json.loads(data_file_ingredients.read())
            for ingredients in ingredient_data:
                Ingredient.objects.get_or_create(
                    name=ingredients['name'],
                    measurement_unit=ingredients['measurement_unit']
                )

        self.stdout.write(self.style.SUCCESS('Данные загружены'))
