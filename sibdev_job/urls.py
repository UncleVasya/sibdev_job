from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path('api/', include('app.deals.api.urls'))
]

# TODO заменить на whitenoise
urlpatterns += staticfiles_urlpatterns()
