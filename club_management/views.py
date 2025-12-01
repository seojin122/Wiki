from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required
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
    groups = Group.objects.filter(status__in=[Group.GroupStatus.RECRUITING, Group.GroupStatus.OPERATING])

    # GET 파라미터에서 필터 값 가져오기
    query = request.GET.get('q', '')
    selected_category = request.GET.get("category", "")
    selected_region = request.GET.get("region", "")

    # 필터링
    if query:
        groups = groups.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )

    if selected_category:
        groups = groups.filter(category=selected_category)

    if selected_region:
        groups = groups.filter(region__icontains=selected_region)
    groups = groups.order_by('-created_at')

    # 카테고리 선택 옵션을 모델의 choices에서 가져오기
    categories = Group.GroupCategory.choices
    regions = Group.objects.values_list('region', flat=True).distinct()

    context = {
        "clubs": groups,       
        "categories": categories,  
        "regions": regions,
        "selected_category": selected_category,
        "selected_region": selected_region,
        "query": query,
    }

    return render(request, "discovery.html", context)

def group_detail_page(request, group_id):
    group = get_object_or_404(
        Group.objects.annotate(member_count=Count("groupmember")),
        pk=group_id,
    )

    if group.leader:
        leader_nickname = group.leader.nickname
        leader_id = group.leader.email
    else:
        leader_nickname = "리더 미지정"
        leader_id = "-"

    group_members = (
        GroupMember.objects.filter(group=group)
        .select_related("user")
        .order_by("joined_date")
    )

    members_detail = []
    for gm in group_members:
        if gm.member_role == GroupMember.MemberRole.LEADER:
            role = "리더"
        elif gm.member_role == GroupMember.MemberRole.ADMIN:
            role = "총무/운영진"
        elif gm.member_role == GroupMember.MemberRole.MEMBER:
            role = "일반 멤버"
        elif gm.member_role == GroupMember.MemberRole.PENDING:
            role = "가입 대기 중"
        else:
            role = gm.get_member_role_display()

        members_detail.append(
            {
                "nickname": gm.user.nickname if gm.user else "(탈퇴 회원)",
                "role": role,
            }
        )

    schedules = ActivitySchedule.objects.filter(group=group).order_by("date_time")
    activities = []
    for s in schedules:
        activities.append(
            {
                "title": s.title,
                "date": s.date_time.strftime("%m월 %d일 %H:%M"),
                "fee": f"{s.participation_fee:,}원",
                "status": "예정",
                "attendees": RSVP.objects.filter(
                    schedule=s,
                    attendance_status=RSVP.AttendanceStatus.ATTENDING,
                ).count(),
            }
        )

    transactions = FinancialTransaction.objects.filter(group=group)
    balance = transactions.aggregate(total=Sum("amount"))["total"] or 0
    last_tx = transactions.order_by("-transaction_date").first()
    last_updated = (
        last_tx.transaction_date.strftime("%Y-%m-%d") if last_tx else "-"
    )

    finance = {
        "current_balance": balance,
        "last_updated": last_updated,
        "dues_status": [],  
    }

    club_context = {
        "id": group.id,
        "name": group.name,
        "category": group.get_category_display(),
        "region": group.region,
        "members": group.member_count,
        "description": group.description,
        "leader_nickname": leader_nickname,
        "leader_id": leader_id,
        "activities": activities,
        "board_posts": [],      
        "members_detail": members_detail,
        "finance": finance,
    }

    is_member = False
    is_leader = False
    is_treasurer = False

    if request.user.is_authenticated:
        membership = GroupMember.objects.filter(
            group=group, user=request.user
        ).first()
        if membership:
            if membership.member_role in [
                GroupMember.MemberRole.LEADER,
                GroupMember.MemberRole.ADMIN,
                GroupMember.MemberRole.MEMBER,
            ]:
                is_member = True
            if membership.member_role == GroupMember.MemberRole.LEADER:
                is_leader = True
            if membership.member_role == GroupMember.MemberRole.ADMIN:
                is_treasurer = True

    context = {
        "club": club_context,
        "is_member": is_member,
        "is_leader": is_leader,
        "is_treasurer": is_treasurer,
    }
    return render(request, "group_detail.html", context)

def my_page_view(request):
    """마이페이지를 렌더링합니다."""

    return render(request, 'mypage.html')

@login_required # 로그인이 필요함
def create_group_view(request):
    if request.method == 'POST':
        # 1. 폼 데이터 가져오기
        name = request.POST.get('name')
        category = request.POST.get('category')
        region = request.POST.get('region')
        description = request.POST.get('description')
        max_members = request.POST.get('max_members')

        # 2. 유효성 검사 (간단하게)
        if name and category and max_members:
            # 3. Group 모델 생성 및 저장
            new_group = Group.objects.create(
                name=name,
                category=category,
                region=region,
                description=description,
                max_members=int(max_members),
                leader=request.user  # 현재 로그인한 사용자를 리더로
            )
            
            # 4. 개설자를 자동으로 멤버(리더)로 추가
            GroupMember.objects.create(
                group=new_group,
                user=request.user,
                member_role=GroupMember.MemberRole.LEADER
            )

            # 5. 생성 후 메인 페이지 등으로 이동
            return redirect('Wiki:discovery') # 혹은 상세 페이지로 redirect
        else:
            # 필수 항목 누락 시 처리 (여기선 간단히 다시 렌더링)
            pass

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

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'{user.nickname}님 환영합니다! 👋')
            return redirect(next_url)
        else:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, self.template_name, {'next': next_url})

class SignupView(View):
    template_name = 'login_signup.html'

    def post(self, request):
        email = request.POST.get('signup-email')
        password = request.POST.get('signup-password')
        nickname = request.POST.get('signup-nickname')

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



