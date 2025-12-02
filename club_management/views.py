from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model 
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import (
    User, 
    Group,      
    GroupMember,
    ActivitySchedule,
    RSVP,
    FinancialTransaction,
    BoardPost,
)


def _group_to_card_dict(group: Group):
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
        "title": group.name,                         
        "description": getattr(group, "description", ""),
        "region": group.region,
        "members": members_count,
        "badge_class": category_badge_classes.get(group.category, "bg-gray-100 text-gray-700"),
    }


def discovery_page(request):
    groups = Group.objects.filter(status__in=[Group.GroupStatus.RECRUITING, Group.GroupStatus.OPERATING])

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

def group_detail_page(request, group_id: int):
    """모임 상세 페이지: DB 기반으로 모임/멤버/일정/재정 정보 조회"""
    group = get_object_or_404(Group, pk=group_id)
    user = request.user if request.user.is_authenticated else None
    member_qs = GroupMember.objects.filter(group=group).select_related("user")
    is_leader = bool(user and group.leader_id == user.id)
    membership = member_qs.filter(user=user).first() if user else None
    is_member = bool(
        membership
        and membership.member_role
        in [
            GroupMember.MemberRole.LEADER,
            GroupMember.MemberRole.ADMIN,
            GroupMember.MemberRole.MEMBER,
        ]
    )
    is_treasurer = bool(
        membership and membership.member_role == GroupMember.MemberRole.ADMIN
    )

    active_members = member_qs.exclude(member_role=GroupMember.MemberRole.PENDING)
    member_count = active_members.count()

    # 가입 대기중 멤버(리더만 볼 수 있음)
    pending_members = (
        member_qs.filter(member_role=GroupMember.MemberRole.PENDING)
        if is_leader
        else GroupMember.objects.none()
    )

    # 일정/재정
    schedules = (
        ActivitySchedule.objects.filter(group=group)
        .select_related("creator")
        .order_by("date_time")
    )
    transactions = (
        FinancialTransaction.objects.filter(group=group)
        .select_related("user")
        .order_by("-transaction_date")
    )

    club = {
        "id": group.id,
        "name": group.name,
        "category": group.get_category_display(),
        "region": group.region,
        "members": member_count,
        "leader_nickname": group.leader.nickname if group.leader else "알 수 없음",
        "leader_id": group.leader.email if group.leader else "",
        "description": group.description,
        "activities": [
            {
                "id": s.id,
                "title": s.title,
                "date": s.date_time.strftime("%Y-%m-%d %H:%M"),
                "fee": f"{s.participation_fee:,}원",
                "status": "예정",
                "attendees": RSVP.objects.filter(
                    schedule=s, attendance_status=RSVP.AttendanceStatus.ATTENDING
                ).count(),
            }
            for s in schedules
        ],
        # 게시판은 아직 DB 모델이 없으니 일단 빈 리스트
        "board_posts": [],
        # 재정 탭 - 간단 버전 (모든 금액을 더해서 현재 잔액처럼 표시)
        "finance": {
            "current_balance": sum(t.amount for t in transactions),
            "last_updated": transactions[0].transaction_date if transactions else None,
            "dues_status": [],  # 추후 회비 모델 만들면 채우기
        },
        # 멤버 탭
        "members_detail": [
            {
                "id": m.id,
                "nickname": m.user.nickname,
                "role": {
                    GroupMember.MemberRole.LEADER: "리더",
                    GroupMember.MemberRole.ADMIN: "운영진",
                    GroupMember.MemberRole.MEMBER: "일반 멤버",
                    GroupMember.MemberRole.PENDING: "가입 대기 중",
                }[m.member_role],
            }
            for m in active_members
        ],
        # 리더 전용: 가입 대기 멤버 목록
        "pending_members": [
            {
                "id": m.id,
                "nickname": m.user.nickname,
                "joined_date": m.joined_date,
            }
            for m in pending_members
        ],
    }

    context = {
        "club": club,
        "group": group,
        "is_member": bool(is_member or is_leader),
        "is_leader": is_leader,
        "is_treasurer": is_treasurer,
    }
    return render(request, "group_detail.html", context)


@login_required(login_url="/auth/")
def group_join(request, group_id: int):
    """모임 가입 신청: GroupMember 를 PENDING 상태로 생성/유지"""
    group = get_object_or_404(Group, pk=group_id)
    user = request.user

    member, created = GroupMember.objects.get_or_create(
        group=group,
        user=user,
        defaults={"member_role": GroupMember.MemberRole.PENDING},
    )

    # 이미 멤버인 경우
    if not created and member.member_role != GroupMember.MemberRole.PENDING:
        messages.info(request, "이미 이 모임의 멤버입니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    if not created and member.member_role == GroupMember.MemberRole.PENDING:
        messages.info(request, "이미 가입 신청이 접수되어 리더 승인 대기 중입니다.")
    else:
        messages.success(request, "가입 신청이 완료되었습니다. 리더의 승인 후 멤버로 참여할 수 있어요.")

    return redirect("Wiki:group_detail", group_id=group.id)



@login_required(login_url="/auth/")
def member_approve(request, group_id: int, member_id: int):
    """리더가 가입 대기 멤버를 승인 → 일반 멤버로 전환"""
    group = get_object_or_404(Group, pk=group_id)
    user = request.user

    if group.leader_id != user.id:
        messages.error(request, "가입 승인은 모임 리더만 가능합니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    member = get_object_or_404(GroupMember, pk=member_id, group=group)

    if member.member_role != GroupMember.MemberRole.PENDING:
        messages.info(request, "이미 처리된 신청입니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    member.member_role = GroupMember.MemberRole.MEMBER
    member.save()
    messages.success(request, f"{member.user.nickname} 님을 멤버로 승인했습니다.")
    return redirect("Wiki:group_detail", group_id=group.id)


@login_required(login_url="/auth/")
def member_reject(request, group_id: int, member_id: int):
    """리더가 가입 대기 멤버를 거절 → 레코드 삭제"""
    group = get_object_or_404(Group, pk=group_id)
    user = request.user

    if group.leader_id != user.id:
        messages.error(request, "가입 거절은 모임 리더만 가능합니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    member = get_object_or_404(GroupMember, pk=member_id, group=group)

    if member.member_role != GroupMember.MemberRole.PENDING:
        messages.info(request, "이미 처리된 신청입니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    nickname = member.user.nickname
    member.delete()
    messages.info(request, f"{nickname} 님의 가입 신청을 거절했습니다.")
    return redirect("Wiki:group_detail", group_id=group.id)


@login_required(login_url='/auth/')
def schedule_create(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    user = request.user

    # 리더 / 총무만 가능
    member = GroupMember.objects.filter(group=group, user=user).first()
    allowed_roles = [GroupMember.MemberRole.LEADER, GroupMember.MemberRole.ADMIN]
    if not member or member.member_role not in allowed_roles:
        messages.error(request, "일정 등록은 리더 또는 총무만 가능합니다.")
        return redirect('Wiki:group_detail', group_id=group.id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        date_time_str = request.POST.get("date_time", "").strip()  # datetime-local
        location = request.POST.get("location", "").strip()
        participation_fee_str = request.POST.get("participation_fee", "0").strip()
        content = request.POST.get("content", "").strip()

        if not (title and date_time_str and location):
            messages.error(request, "제목, 일시, 장소는 꼭 입력해야 합니다.")
            return render(request, "schedule_form.html", {"group": group})

        try:
            dt = datetime.fromisoformat(date_time_str)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
        except Exception:
            messages.error(request, "일시 형식이 올바르지 않습니다.")
            return render(request, "schedule_form.html", {"group": group})

        try:
            participation_fee = int(participation_fee_str or 0)
        except ValueError:
            participation_fee = 0

        ActivitySchedule.objects.create(
            group=group,
            title=title,
            date_time=dt,
            location=location,
            content=content,
            participation_fee=participation_fee,
        )
        messages.success(request, "새 일정이 등록되었습니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    # GET
    return render(request, "schedule_form.html", {"group": group})


@login_required(login_url='/auth/')
def board_post_create(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    user = request.user

    # 멤버(리더/총무/일반)만 가능, 가입 대기(PENDING)는 안 됨
    member = GroupMember.objects.filter(group=group, user=user).first()
    if not member or member.member_role == GroupMember.MemberRole.PENDING:
        messages.error(request, "게시글 작성은 모임 멤버만 가능합니다.")
        return redirect('Wiki:group_detail', group_id=group.id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        is_notice = bool(request.POST.get("is_notice"))

        if not title or not content:
            messages.error(request, "제목과 내용을 입력해주세요.")
            return render(request, "board_post_form.html", {"group": group})

        BoardPost.objects.create(
            group=group,
            author=user,
            title=title,
            content=content,
            is_notice=is_notice,
        )
        messages.success(request, "게시글이 등록되었습니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    return render(request, "board_post_form.html", {"group": group})

@login_required(login_url='/auth/')
def finance_create(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    user = request.user

    # 리더 / 총무만 가능
    member = GroupMember.objects.filter(group=group, user=user).first()
    allowed_roles = [GroupMember.MemberRole.LEADER, GroupMember.MemberRole.ADMIN]
    if not member or member.member_role not in allowed_roles:
        messages.error(request, "재정 기록 관리는 리더 또는 총무만 가능합니다.")
        return redirect('Wiki:group_detail', group_id=group.id)

    if request.method == "POST":
        amount_str = request.POST.get("amount", "").strip()
        description = request.POST.get("description", "").strip()

        if not amount_str or not description:
            messages.error(request, "금액과 내용을 입력해주세요.")
            return render(request, "finance_form.html", {"group": group})

        try:
            amount = int(amount_str)
        except ValueError:
            messages.error(request, "금액은 숫자로 입력해주세요.")
            return render(request, "finance_form.html", {"group": group})

        FinancialTransaction.objects.create(
            group=group,
            user=user,
            amount=amount,
            description=description,
        )
        messages.success(request, "재정 기록이 추가되었습니다.")
        return redirect("Wiki:group_detail", group_id=group.id)

    return render(request, "finance_form.html", {"group": group})




@login_required(login_url='/auth/')
def my_page_view(request):
    user = request.user 

    leading_groups = (
        Group.objects.filter(leader=user)
        .annotate(member_count=Count("groupmember"))
        .order_by("-created_at")
    )

    joined_groups = (
        Group.objects.filter(
            groupmember__user=user,
            groupmember__member_role__in=[
                GroupMember.MemberRole.LEADER,
                GroupMember.MemberRole.ADMIN,
                GroupMember.MemberRole.MEMBER,
            ],
        )
        .exclude(leader=user)
        .annotate(member_count=Count("groupmember"))
        .distinct()
        .order_by("-created_at")
    )

    context = {
        "leading_groups": leading_groups,
        "joined_groups": joined_groups,
    }
    return render(request, "mypage.html", context)

@login_required(login_url='/auth/')
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
            new_group = Group.objects.create(
                name=name,
                category=category,
                region=region,
                description=description,
                max_members=int(max_members),
                leader=request.user  # 개설자를 리더 필드에도 저장
            )

            # 3. 핵심: 멤버 테이블(GroupMember)에도 '리더'로 등재하기!
            GroupMember.objects.create(
                group=new_group,
                user=request.user,
                member_role=GroupMember.MemberRole.LEADER # 리더 역할 부여
            )
            
            return redirect('Wiki:group_detail', group_id=new_group.id)

    return render(request, 'create_group.html')

@login_required(login_url='/auth/')
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    # 이미 가입했는지 확인 (중복 가입 방지)
    if GroupMember.objects.filter(group=group, user=request.user).exists():
        messages.warning(request, "이미 가입한 모임입니다.")
        return redirect('Wiki:group_detail', group_id=group.id)

    # 멤버로 추가 (기본값: 승인 대기 PENDING 또는 바로 가입 MEMBER)
    GroupMember.objects.create(
        group=group,
        user=request.user,
        member_role=GroupMember.MemberRole.PENDING # 또는 MEMBER
    )
    
    messages.success(request, "가입 신청이 완료되었습니다!")
    return redirect('Wiki:group_detail', group_id=group.id)

@login_required(login_url='/auth/')
def profile_edit_view(request):
    context = {}
    return render(request, 'profile_edit.html', context)

# === 로그인 / 회원가입 뷰 ===
class AuthView(View):
    template_name = "login_signup.html"

    def get(self, request):
        # 로그인 여부와 상관없이 항상 로그인/회원가입 페이지 보여주기
        active_tab = request.GET.get("tab", "login")
        if active_tab not in ("login", "signup"):
            active_tab = "login"
        return render(request, self.template_name, {"active_tab": active_tab})

    def post(self, request):
        mode = request.POST.get("mode")

        if mode == "login":
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "")

            if not email or not password:
                messages.error(request, "이메일과 비밀번호를 모두 입력해주세요.")
                return render(
                    request,
                    self.template_name,
                    {"active_tab": "login", "login_email": email},
                )

            user = authenticate(request, username=email, password=password)

            if user is None:
                messages.error(request, "이메일 또는 비밀번호가 올바르지 않습니다.")
                return render(
                    request,
                    self.template_name,
                    {"active_tab": "login", "login_email": email},
                )

            # 로그인 성공
            login(request, user)
            messages.success(request, f"{user.nickname}님, 환영합니다! 👋")
            return redirect("Wiki:discovery")

        elif mode == "signup":
            email = request.POST.get("email", "").strip()
            nickname = request.POST.get("nickname", "").strip()
            password1 = request.POST.get("password1", "")
            password2 = request.POST.get("password2", "")

            # 기본 검증
            if not email or not nickname or not password1 or not password2:
                messages.error(request, "모든 필드를 입력해주세요.")
                return render(
                    request,
                    self.template_name,
                    {
                        "active_tab": "signup",
                        "signup_email": email,
                        "signup_nickname": nickname,
                    },
                )

            if password1 != password2:
                messages.error(request, "비밀번호와 비밀번호 확인이 일치하지 않습니다.")
                return render(
                    request,
                    self.template_name,
                    {
                        "active_tab": "signup",
                        "signup_email": email,
                        "signup_nickname": nickname,
                    },
                )

            if User.objects.filter(email=email).exists():
                messages.error(request, "이미 사용 중인 이메일입니다.")
                return render(
                    request,
                    self.template_name,
                    {
                        "active_tab": "signup",
                        "signup_email": email,
                        "signup_nickname": nickname,
                    },
                )

            # 실제 유저 생성
            user = User.objects.create_user(
                email=email,
                password=password1,
                nickname=nickname,
            )

            messages.success(request, "회원가입이 완료되었습니다. 이제 로그인해주세요.")
            return render(
                request,
                self.template_name,
                {"active_tab": "login", "login_email": email},
            )

        messages.error(request, "잘못된 요청입니다.")
        return redirect("Wiki:auth")


def user_logout(request):
    logout(request)
    messages.info(request, "로그아웃되었습니다. 다시 만나요! 👋")
    return redirect("Wiki:discovery")
