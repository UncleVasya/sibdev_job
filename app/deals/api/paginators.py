from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from sibdev_job import const


class SimpleLimitPagination(LimitOffsetPagination):
    """
    Пагинатор, который:
    - устанавливает лимит на общее количество отображаемых записей
    - и отключает параметр оффсет;
    - приводит список объектов в соответствие с требованиями задачи
      (данные хранятся в поле response)
    """
    default_limit = const.top_customers_limit

    def paginate_queryset(self, queryset, request, view=None):
        result = super().paginate_queryset(queryset, request, view)
        self.display_page_controls = False
        return result

    def get_offset(self, request):
        return 0

    def get_paginated_response(self, data):
        return Response(dict({'response': data}))
