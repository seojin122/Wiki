from django.urls import path
from . import views

app_name = 'Wiki'

urlpatterns = [
    path('', views.discovery_page, name='discovery'),
    path('group/<int:group_id>/', views.group_detail_page, name='group_detail'),
    path('group/<int:group_id>/join/', views.group_join, name='group_join'),
    path('group/<int:group_id>/members/<int:member_id>/approve/', views.member_approve, name='member_approve'),
    path('group/<int:group_id>/members/<int:member_id>/reject/', views.member_reject, name='member_reject'),
    path('group/<int:group_id>/schedule/new/', views.schedule_create, name='schedule_create'),
    path('group/<int:group_id>/board/new/', views.board_post_create, name='board_post_create'),
    path('group/<int:group_id>/finance/new/', views.finance_create, name='finance_create'),
    path('group/<int:group_id>/delete/', views.delete_group_view, name='group_delete'),

    path('auth/', views.AuthView.as_view(), name='auth'),
    path('logout/', views.user_logout, name='logout'),

    path('my/', views.my_page_view, name='my_page'),
    path('my/edit/', views.profile_edit_view, name='profile_edit'),
    path('create/', views.create_group_view, name='create_group'),
]
