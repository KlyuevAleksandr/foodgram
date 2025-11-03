from csv import reader as csv_reader

from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help_text = 'Загрузка списка ингредиентов в базу данных'

    def execute_command(self):
        p = 'data/ingredients.csv'
        try:
            with open(p, mode='r', encoding='UTF-8') as file:
                food_items = self._prepare_food_items(file)
                saved_count = self._save_to_database(food_items)

                self._show_success_message(saved_count, p)

        except FileNotFoundError:
            self._show_error_message(f'Отсутствует файл данных: {p}')
        except Exception as error:
            self._show_error_message(f'Произошла ошибка: {error}')

    def _prepare_food_items(self, file_object):
        return [
            Ingredient(
                name=row[0].strip(),
                measurement_unit=row[1].strip()
            )
            for row in csv_reader(file_object)
        ]

    def _save_to_database(self, items):
        return len(Ingredient.objects.bulk_create(
            items,
            ignore_conflicts=True
        ))

    def _show_success_message(self, count, path):
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено {count} записей из файла {path}'
            )
        )

    def _show_error_message(self, text):
        self.stdout.write(
            self.style.ERROR(text)
        )

    def handle(self, *args, **options):
        self.execute_command()
