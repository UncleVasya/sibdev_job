import csv
import datetime

from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status, views
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from app.deals.api import const, serializers
from app.deals.api.paginators import SimpleLimitPagination
from app.deals.models import Customer, Deal, Gem


class DealsUploadView(views.APIView):
    """Эндпоинт для импорта сделок из файла."""

    # само по себе это поле не используется в классе APIView,
    # однако его использует веб-морда DRF для правильного
    # отображения интерфейса
    serializer_class = serializers.DealsUploadSerializer

    def post(self, request, version=None):
        file = request.FILES.get('deals')
        if not file:
            raise ValidationError({
                    'detail': 'Отсутствует файл со сделками.',
                    'code': 'file_missing',
                })

        try:
            text = file.read().decode('utf-8')
            if not text:
                raise ValidationError({
                    'detail': 'В файле отсутствуют данные.',
                    'code': 'file_empty',
                })
            data = csv.DictReader(text.splitlines())
        except (UnicodeDecodeError, AttributeError):
            raise ValidationError({
                'detail': 'Формат файла не поддерживается.',
                'code': 'file_wrong_format',
            })

        try:
            rows_count = self._parse_deals_data_from_csv(data)
        except (KeyError, ValueError) as e:
            raise ValidationError({
                'detail': f'Ошибка в данных: {e.__class__.__name__} ({e})',
                'code': 'file_corrupt_data',
            })
        except Exception as e:
            raise ValidationError(
                f'Неизвестная ошибка при обработке файла: {e.__class__.__name__} ({e})'
            )

        if rows_count == 0:
            raise ValidationError({
                'detail': 'В файле отсутствуют данные.',
                'code': 'file_empty',
            })

        # успешно импортировали сделки в базу,
        # нужно очистить кеш страницы с данными о сделках
        # TODO: В будущем если будут предусмотрены другие способы
        #       обновления данных (админка, скрипт, др.), то логично будет
        #       повесить очищение кэша на сигнал при сохранении моделей.
        cache.delete_many(
            keys=cache.keys(f'*{const.top_customers_cache_key_prefix}*')
        )

        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def _parse_deals_data_from_csv(data: csv.DictReader) -> int:
        """
        Логика сохранения информации о сделках.
        Возвращает количество обработанных записей.
        """
        row_counter = 0
        with transaction.atomic():
            for row in data:
                # TODO: если будет нужна оптимизация, можно сделать следующим образом:
                #       1) составить список всех имен в файле
                #       2) одним запросом определить, какие имена отсутсвуют
                #       3) добавить в базу отсутствующие
                #       (аналогично для камней)
                customer = Customer.objects.get_or_create(username=row['customer'])[0]
                customer.save()

                item = Gem.objects.get_or_create(name=row['item'])[0]
                item.save()

                # Если в базе уже имеется сделка по паре пользователь + таймстамп,
                # то считаем новые данные исправлением и перезаписываем данные из БД.
                # TODO: уточнить у заказчика, возможно несколько валидных сделок
                #       могут провести по одному таймстампу. В таком случае все сделки
                #       нужно будет считать правильными и сохранять.
                deal = Deal.objects.update_or_create(
                    customer=customer,
                    date=datetime.datetime.fromisoformat(row['date']),
                    defaults={
                        'item': item,
                        'total_cost': row['total'],
                        'quantity': row['quantity'],
                    }
                )[0]
                deal.save()
                row_counter += 1
        return row_counter


class TopCustomersView(generics.ListAPIView):
    """Эндпоинт для отображение наиболее потратившихся покупателей."""
    serializer_class = serializers.TopCustomersSerializer
    pagination_class = SimpleLimitPagination

    @method_decorator(cache_page(
        const.top_customers_cache_key_duration,
        key_prefix=const.top_customers_cache_key_prefix
    ))
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_queryset(self):
        qs = Customer.objects.annotate(
            spent_money=Sum('deals__total_cost', default=0),
        ).order_by('-spent_money')

        return qs
