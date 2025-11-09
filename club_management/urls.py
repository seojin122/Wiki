from django.urls import path
from . import views

app_name = 'Wiki'

urlpatterns = [
    path('', views.club_discovery_view, name='discovery'), 
    path('auth/', views.LoginView.as_view(), name='login_page'),
]