from django.urls import path, include


urlpatterns = [
    path('api/', include('app.deals.api.urls'))
]
