from django.urls import path
from stocks import views

app_name='stocks'
urlpatterns = [
    path('', views.combined_stock_view, name='combined_stock_view'),
]