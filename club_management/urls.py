from django.urls import path
from . import views

# 앱 이름을 'club_management'으로 지정
app_name = 'club_management'

urlpatterns = [
    # 'http://127.0.0.1:8000/club-list/' 경로에 연결됩니다.
    path('club-list/', views.club_discovery_view, name='discovery'), 
    
    # [TODO] 모임 상세 페이지 path('club/<int:pk>/', views.club_detail_view, name='detail'),
    # [TODO] 모임 가입 신청 API path('club/<int:pk>/apply/', views.club_apply_api, name='apply'),
]