from django.shortcuts import render
from django.db.models import Count # 멤버 수 카운트를 위해 Count 임포트
from .models import Club, Category, ClubMember # 필요한 모델 임포트

# 모임 탐색 및 목록 페이지 (FR3.2)
def club_discovery_view(request):
    """
    모임 목록 및 검색 페이지를 렌더링하고, 실제 모임 데이터를 템플릿에 전달합니다.
    """
    # 실제 데이터 로직
    clubs = Club.objects.filter(is_active=True).select_related('category').annotate(
        member_count=Count('clubmember', distinct=True) # 중복 카운트 방지
    ).order_by('-created_at') 

    categories = Category.objects.all()
    
    context = {
        'page_title': '모임 찾기',
        'clubs': clubs,
        'categories': categories,
    }
    
    # templates/club_management/club_discovery.html 파일을 렌더링합니다. (경로 확인)
    return render(request, 'club_management/club_discovery.html', context)