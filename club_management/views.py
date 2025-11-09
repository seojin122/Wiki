from django.shortcuts import render
from django.db.models import Count # 멤버 수 카운트를 위해 Count 임포트
from .models import Club, Category, ClubMember # 필요한 모델 임포트
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User # Django 기본 User 모델 사용 가정
from django.contrib import messages

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
    return render(request, 'club_discovery.html', context)

class LoginView(View):
    template_name = 'login_signup.html' # HTML 파일 이름

    def get(self, request):
        """로그인/회원가입 페이지를 렌더링합니다."""
        # 로그인 성공 후 리다이렉트될 경로를 next 파라미터로 받을 수 있습니다.
        next_url = request.GET.get('next', '/')
        return render(request, self.template_name, {'next': next_url})

    def post(self, request):
        """로그인 폼 데이터를 처리합니다."""
        email = request.POST.get('login-email')
        password = request.POST.get('login-password')
        next_url = request.POST.get('next', '/') # hidden 필드로 next 경로 받기

        # 1. 이메일을 사용자 이름(username)으로 변환 (Django 기본 User 모델은 username 필드를 사용)
        try:
            # 이메일로 User 인스턴스 찾기 (실제로는 Custom User Model을 사용하여 email을 username으로 설정하는 것이 일반적입니다)
            # 여기서는 편의상 email을 username처럼 사용한다고 가정하고 User를 찾아봅니다.
            # 실제 구현 시, 이메일을 username으로 쓰거나, 별도 인증 백엔드가 필요합니다.
            user = User.objects.get(email=email)
            username = user.username # 찾은 사용자의 username을 사용
        except User.DoesNotExist:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, self.template_name)

        # 2. Django의 authenticate 함수로 사용자 인증
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 인증 성공: login 처리
            login(request, user)
            messages.success(request, f'{user.username}님 환영합니다! 👋')
            return redirect(next_url) # 성공 시 지정된 페이지로 이동
        else:
            # 인증 실패
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, self.template_name)


# 회원가입 페이지 View
class SignupView(View):
    template_name = 'login_signup.html'

    def post(self, request):
        """회원가입 폼 데이터를 처리합니다."""
        email = request.POST.get('signup-email')
        password = request.POST.get('signup-password')
        nickname = request.POST.get('signup-nickname')
        
        # 유효성 검사 (필수 필드 확인)
        if not all([email, password, nickname]):
            messages.error(request, '모든 필수 정보를 입력해주세요.')
            return render(request, self.template_name)

        # 비밀번호 길이 및 유효성 검사 (추가 필요)
        if len(password) < 6:
            messages.error(request, '비밀번호는 6자 이상이어야 합니다.')
            return render(request, self.template_name)

        # 이메일 중복 확인
        if User.objects.filter(email=email).exists():
            messages.error(request, '이미 사용 중인 이메일입니다.')
            return render(request, self.template_name)

        try:
            # 사용자 생성 (Django의 기본 User 모델 가정)
            # 닉네임을 username으로 사용한다고 가정합니다.
            user = User.objects.create_user(
                username=nickname, # 닉네임을 사용자 이름으로 설정
                email=email,
                password=password
            )
            user.first_name = nickname # 필요시 닉네임을 first_name에 저장
            user.save()
            
            messages.success(request, '🎉 회원가입이 성공적으로 완료되었습니다. 로그인해주세요.')
            return redirect('login_url_name') # 회원가입 성공 후 로그인 페이지로 리다이렉트
        except Exception as e:
            # 기타 예외 처리
            messages.error(request, f'회원가입 중 오류가 발생했습니다: {e}')
            return render(request, self.template_name)

# 로그아웃 함수
def user_logout(request):
    logout(request)
    messages.info(request, '로그아웃되었습니다. 다시 만나요!')
    return redirect('discovery_url_name') # 모임 찾기 페이지로 리다이렉트