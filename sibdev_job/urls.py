from django.urls import include, path

urlpatterns = [
    path('api/', include('app.deals.api.urls', namespace='deals'))
]
