from django.urls import path
from . import views

app_name = 'Wiki'

urlpatterns = [
    path('', views.discovery_page, name='discovery'), 
    path('group/<int:group_id>/', views.group_detail_page, name='group_detail'),
    path('auth/', views.LoginView.as_view(), name='login_page'),
    
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', views.user_logout, name='logout'),


    path('my/', views.my_page_view, name='my_page'),
    path('my/edit/', views.profile_edit_view, name='profile_edit'),
    path('create/', views.create_group_view, name='create_group'),
]