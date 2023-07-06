from django.urls import path

from app.deals.api import views

urlpatterns = [
    path('deals-upload/', views.DealsUploadView.as_view()),
    path('top-customers/', views.TopCustomersView.as_view()),
]
