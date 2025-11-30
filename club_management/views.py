from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.utils import timezone

from .models import (
    User, 
    Group,      
    GroupMember,
    ActivitySchedule,
    RSVP,
    FinancialTransaction
)


def _group_to_card_dict(group: Group):
    # 카테고리별 뱃지 색상 (대충 보기 좋게)
    category_badge_classes = {
        "SPORTS": "bg-green-100 text-green-700",
        "ART": "bg-pink-100 text-pink-700",
        "MUSIC": "bg-purple-100 text-purple-700",
        "COOKING": "bg-orange-100 text-orange-700",
        "READING": "bg-blue-100 text-blue-700",
        "OTHER": "bg-gray-100 text-gray-700",
    }

    members_count = GroupMember.objects.filter(group=group).count()
    if members_count == 0:
        # 아직 멤버 테이블 안 쓰고 있으면 리더 한 명 있다고 가정
        members_count = 1

    return {
        "id": group.id,
        "category": group.get_category_display() if hasattr(group, "get_category_display") else group.category,
        "title": group.name,                          # 템플릿에서 club.title 쓰고 있어서 name → title로 매핑
        "description": getattr(group, "description", ""),
        "region": group.region,
        "members": members_count,
        "badge_class": category_badge_classes.get(group.category, "bg-gray-100 text-gray-700"),
    }


def discovery_page(request):
    # groups = Group.objects.all()
    groups = Group.objects.all().select_related('leader')

    category_badge_map = {
        Group.GroupCategory.SPORTS: "bg-green-100 text-green-800",
        Group.GroupCategory.ART: "bg-purple-100 text-purple-800",
        Group.GroupCategory.MUSIC: "bg-pink-100 text-pink-800",
        Group.GroupCategory.COOKING: "bg-orange-100 text-orange-800",
        Group.GroupCategory.READING: "bg-indigo-100 text-indigo-800",
        Group.GroupCategory.OTHER: "bg-gray-100 text-gray-800",
    }

    clubs = []
    for g in groups:
        member_count = GroupMember.objects.filter(
            group=g,
            member_role__in=[
                GroupMember.MemberRole.LEADER,
                GroupMember.MemberRole.ADMIN,
                GroupMember.MemberRole.MEMBER,
            ]
        ).count()

        clubs.append({
            "id": g.id,
            "title": g.name,
            "category": g.get_category_display(),
            "description": g.description,
            "region": g.region,
            "members": member_count,
            "badge_class": category_badge_map.get(g.category, "bg-gray-100 text-gray-800"),
        })

    context = {"clubs": clubs}
    return render(request, "discovery.html", context)


def group_detail_page(request, group_id):
    group = get_object_or_404(
        Group.objects.select_related('leader'),
        pk=group_id
    )

    # 로그인 한 유저의 멤버십 상태 확인
    is_member = False
    is_leader = False
    is_treasurer = False

    if request.user.is_authenticated:
        try:
            gm = GroupMember.objects.get(user=request.user, group=group)
            if gm.member_role in [
                GroupMember.MemberRole.LEADER,
                GroupMember.MemberRole.ADMIN,
                GroupMember.MemberRole.MEMBER,
            ]:
                is_member = True
            if gm.member_role == GroupMember.MemberRole.LEADER:
                is_leader = True
            if gm.member_role == GroupMember.MemberRole.ADMIN:
                is_treasurer = True
        except GroupMember.DoesNotExist:
            pass

    # 멤버 리스트 & 멤버 수
    member_qs = GroupMember.objects.filter(
        group=group,
        member_role__in=[
            GroupMember.MemberRole.LEADER,
            GroupMember.MemberRole.ADMIN,
            GroupMember.MemberRole.MEMBER,
        ]
    ).select_related('user')

    members_count = member_qs.count()
    members_detail = [
        {
            "nickname": gm.user.nickname,
            "role": gm.get_member_role_display(),
        }
        for gm in member_qs
    ]

    # 일정 / 재정은 아직 DB 로직 안 넣고 기본값만
    activities = []  # 나중에 ActivitySchedule 연동해서 채우면 됨
    finance = {
        "current_balance": 0,
        "last_updated": timezone.now().strftime("%Y-%m-%d"),
        "dues_status": [],
    }

    club = {
        "id": group.id,
        "name": group.name,
        "category": group.get_category_display(),
        "region": group.region,
        "members": members_count,
        "description": group.description,
        "leader_nickname": group.leader.nickname if group.leader else "미지정",
        "leader_id": group.leader.email if group.leader else "",
        "activities": activities,
        "board_posts": [],      # 게시판 모델 만들면 여기에 채우기
        "members_detail": members_detail,
        "finance": finance,
    }

    context = {
        "club": club,
        "is_member": is_member,
        "is_leader": is_leader,
        "is_treasurer": is_treasurer,
    }
    return render(request, "group_detail.html", context)


def my_page_view(request):
    """마이페이지를 렌더링합니다."""

    return render(request, 'mypage.html')

def create_group_view(request):
    """모임생성을 렌더링합니다."""

    return render(request, 'create_group.html')

def profile_edit_view(request):
    context = {}
    return render(request, 'profile_edit.html', context)


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

        # 커스텀 유저: USERNAME_FIELD = 'email' 이라 username 자리에 email 넣어줌
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'{user.nickname}님 환영합니다! 👋')
            return redirect(next_url)
        else:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, self.template_name, {'next': next_url})

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

        if len(password) < 6:
            messages.error(request, '비밀번호는 6자 이상이어야 합니다.')
            return render(request, self.template_name)

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
            return redirect('Wiki:login_page')
        except Exception as e:
            messages.error(request, f'회원가입 중 오류가 발생했습니다: {e}')
            return render(request, self.template_name)

def user_logout(request):
    logout(request)
    messages.info(request, '로그아웃되었습니다. 다음에 또 만나요!')
    return redirect('discovery')



