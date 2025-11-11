from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib import messages
from django.http import Http404, HttpResponse

from .models import (
    User, 
    Group,      
    GroupMember,
    ActivitySchedule,
    RSVP,
    FinancialTransaction
)

from .mock_data import CLUBS_MOCK_DATA, GROUP_DETAIL_MOCK_DATA

def discovery_page(request):
    context = {
        'clubs': CLUBS_MOCK_DATA 
    }
    
    return render(request, 'discovery.html', context)

def group_detail_page(request, group_id):
    group_id = int(group_id)
    club_data = GROUP_DETAIL_MOCK_DATA.get(group_id)
    
    if club_data:
        context = {'club': club_data}
    else:
        context = {
            'error_message': '모임을 찾을 수 없습니다.',
            'group_id': group_id
        }

    return render(request, 'group_detail.html', context)


def my_page_view(request):
    """마이페이지를 렌더링합니다."""
    # 실제 구현 시, 로그인된 사용자의 데이터를 context로 전달해야 합니다.
    return render(request, 'mypage.html')


class AuthView(View):
    template_name = 'login_signup.html'

    def get(self, request):
        """로그인/회원가입 페이지를 렌더링합니다."""
        return render(request, self.template_name)

    def post(self, request):
        # ... 로그인 및 회원가입 POST 처리 로직 (이전과 동일) ...
        # 여기서는 생략합니다. 실제 구현 시 View를 분리하는 것이 좋습니다.
        return redirect('discovery')
    

    

class LoginView(View):
    template_name = 'login_signup.html' 

    def get(self, request):
        next_url = request.GET.get('next', '/')
        return render(request, self.template_name, {'next': next_url})

    def post(self, request):
        email = request.POST.get('login-email')
        password = request.POST.get('login-password')
        next_url = request.POST.get('next', '/') 

        # 이메일을 사용자 이름(username)으로 변환 (Django 기본 User 모델은 username 필드를 사용)
        try:
            user = authenticate(request, username=email, password=password) 
        except User.DoesNotExist:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, self.template_name)

        if user is not None:
            login(request, user)
            messages.success(request, f'{user.username}님 환영합니다! 👋')
            return redirect(next_url) 
        else:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, self.template_name)


# 회원가입 페이지 View
class SignupView(View):
    template_name = 'login_signup.html'

    def post(self, request):
        email = request.POST.get('signup-email')
        password = request.POST.get('signup-password')
        nickname = request.POST.get('signup-nickname')
        
        # 유효성 검사 
        if not all([email, password, nickname]):
            messages.error(request, '모든 필수 정보를 입력해주세요.')
            return render(request, self.template_name)

        # 비밀번호 길이 및 유효성 검사 
        if len(password) < 6:
            messages.error(request, '비밀번호는 6자 이상이어야 합니다.')
            return render(request, self.template_name)

        # 이메일 중복 확인
        if User.objects.filter(email=email).exists():
            messages.error(request, '이미 사용 중인 이메일입니다.')
            return render(request, self.template_name)

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                nickname=nickname,
            )
            user.save()
            
            messages.success(request, '🎉 회원가입이 성공적으로 완료되었습니다. 로그인해주세요.')
            return redirect('login_url_name') 
        except Exception as e:
            messages.error(request, f'회원가입 중 오류가 발생했습니다: {e}')
            return render(request, self.template_name)


def user_logout(request):
    logout(request)
    messages.info(request, '로그아웃되었습니다. 다시 만나요!')
    return redirect('discovery_url_name') 



