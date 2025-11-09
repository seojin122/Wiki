from django.urls import path
from . import views

app_name = 'Wiki'

urlpatterns = [
    path('', views.discovery_page, name='discovery'), 
    path('group/<int:group_id>/', views.group_detail_page, name='group_detail'),
    path('auth/', views.LoginView.as_view(), name='login_page'),
    path('my/', views.my_page_view, name='my_page'),
]