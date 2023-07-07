from django.urls import path

from app.deals.api import views

app_name = 'deals'

urlpatterns = [
    path(
        'deals-upload/',
        views.DealsUploadView.as_view(),
        name='deals-upload'
    ),
    path(
        'top-customers/',
        views.TopCustomersView.as_view(),
        name='top-customers'
    ),
]
