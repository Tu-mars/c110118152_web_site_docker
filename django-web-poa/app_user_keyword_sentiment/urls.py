from django.urls import path

from . import views

app_name="app_user_keyword_sentiment"

urlpatterns = [
    path('', views.home, name='home'),
    path('api_get_userkey_sentiment/', views.api_get_userkey_sentiment),

]
