from django.db.models import (Count, F, Prefetch, Q, Value,
                              prefetch_related_objects)
from rest_framework import serializers

from app.deals.models import Customer, Gem
from sibdev_job import const


class DealsUploadSerializer(serializers.Serializer):
    """Сериализатор для загрузки файла со сделками."""
    deals = serializers.FileField()


class GemNameSerializer(serializers.ModelSerializer):
    """Сериализатор драгоценных камней, отображает только имя."""
    class Meta:
        model = Gem
        fields = ('name', )


class TopCustomersSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения наиболее потратившихся покупателей."""
    username = serializers.CharField()
    spent_money = serializers.DecimalField(
        decimal_places=2,
        max_digits=const.decimal_max_digits,
    )
    gems = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        exclude = ('id', )

    def __init__(self, top_customers, *args, **kwargs):
        super().__init__(top_customers, *args, **kwargs)

        # Здесь мы фильтруем камни, оставляя лишь те, которые есть
        # как минимум у двух топовых покупателей
        top_customers_ids = [customer.id for customer in top_customers]
        filtered_gems = Gem.objects.annotate(
            cnt=Count(
                'customers__username',
                distinct=True,
                filter=Q(customers__id__in=top_customers_ids)
            )
        ).filter(cnt__gte=2).values_list('name', flat=True)

        # Используем prefetch_related_objects, чтобы дополнить
        # уже вычисленный qs покупателей данными о камнях.
        prefetch_related_objects(
            top_customers,
            Prefetch(
                'gems',
                Gem.objects.filter(name__in=filtered_gems).distinct()
            )
        )

    def get_gems(self, obj):
        return [f'{gem.name}' for gem in obj.gems.all()]
