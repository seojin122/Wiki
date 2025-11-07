from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

# 장고 기본 사용자 모델 가져오기 (FR1.1, FR1.2)
User = get_user_model()

# 🧩 A. 유연한 모임 카테고리
class Category(models.Model):
    """
    모임 카테고리 모델 (예: 체육, 미술, 음악).
    """
    name = models.CharField(max_length=50, unique=True, verbose_name="카테고리 이름")
    description = models.TextField(blank=True, verbose_name="설명")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "카테고리"


class Club(models.Model):
    """
    모임/동호회 정보 모델 (FR2.1, FR2.2, FR2.4).
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="모임 이름")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="카테고리")
    region = models.CharField(max_length=50, verbose_name="활동 지역")
    description = models.TextField(verbose_name="모임 소개")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_clubs', verbose_name="생성자")
    is_active = models.BooleanField(default=True, verbose_name="활동 중 여부")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "모임"
        verbose_name_plural = "모임 목록"


# 🤝 B. 모임 운영 및 멤버 관리
class ClubMember(models.Model):
    """
    모임과 멤버를 연결하고 역할/상태를 관리하는 중간 모델 (FR1.3, FR2.3).
    """
    ROLE_CHOICES = (
        ('LEADER', '리더 (모임 생성자/최고 관리자)'),
        ('MANAGER', '총무/운영진'),
        ('MEMBER', '일반 멤버'),
    )
    STATUS_CHOICES = (
        ('PENDING', '가입 신청 대기'),
        ('APPROVED', '승인 완료'),
        ('REJECTED', '거절됨'),
    )

    club = models.ForeignKey(Club, on_delete=models.CASCADE, verbose_name="모임")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER', verbose_name="역할")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="가입 상태")
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.club.name} ({self.get_status_display()})'
    
    class Meta:
        unique_together = ('club', 'user') # 한 모임에 같은 멤버는 중복될 수 없음
        verbose_name = "모임 멤버"
        verbose_name_plural = "모임 멤버 관리"

# 🗓️ C. 일정 및 출석 관리
class Event(models.Model):
    """
    모임 활동 일정 모델 (FR4.1).
    """
    club = models.ForeignKey(Club, on_delete=models.CASCADE, verbose_name="모임")
    title = models.CharField(max_length=100, verbose_name="일정 제목")
    start_time = models.DateTimeField(verbose_name="시작 시간")
    end_time = models.DateTimeField(verbose_name="종료 시간")
    location = models.CharField(max_length=255, blank=True, verbose_name="장소")
    description = models.TextField(blank=True, verbose_name="세부 내용")
    required_fee = models.IntegerField(default=0, verbose_name="참석 시 회비(선택)")

    def __str__(self):
        return f'[{self.club.name}] {self.title} ({self.start_time.strftime("%m/%d %H:%M")})'
    
    class Meta:
        ordering = ['start_time']
        verbose_name = "모임 일정"
        verbose_name_plural = "일정 관리"


class Attendance(models.Model):
    """
    멤버의 일정 참석 여부 (RSVP) 및 실제 출석 기록 모델 (FR4.2, FR4.3).
    """
    RSVP_CHOICES = (
        ('ATTEND', '참석 예정'),
        ('ABSENT', '불참'),
        ('MAYBE', '미정'),
    )
    ACTUAL_CHOICES = (
        ('PRESENT', '출석'),
        ('ABSENT', '결석'),
        ('NOT_CHECKED', '미확인'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="일정")
    member = models.ForeignKey(ClubMember, on_delete=models.CASCADE, verbose_name="모임 멤버")
    
    rsvp_status = models.CharField(max_length=10, choices=RSVP_CHOICES, default='MAYBE', verbose_name="사전 참석 응답")
    actual_status = models.CharField(max_length=15, choices=ACTUAL_CHOICES, default='NOT_CHECKED', verbose_name="실제 출석 여부")
    
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_checker', verbose_name="출석 체크 담당자")
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name="출석 체크 시간")

    def __str__(self):
        return f'{self.member.user.username} - {self.event.title}'

    class Meta:
        unique_together = ('event', 'member')
        verbose_name = "출석/참석 기록"
        verbose_name_plural = "출석 기록"


# 💰 D. 재정 관리 (회비/재료비)
class FinancialRecord(models.Model):
    """
    모임의 수입/지출 내역 기록 모델 (FR5.1, FR5.3).
    """
    TYPE_CHOICES = (
        ('INCOME', '수입 (회비, 지원금 등)'),
        ('EXPENSE', '지출 (장소, 재료비 등)'),
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, verbose_name="모임")
    record_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="구분")
    amount = models.IntegerField(verbose_name="금액")
    description = models.CharField(max_length=255, verbose_name="내역")
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="기록자")
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.club.name} - {self.get_record_type_display()}: {self.amount}원'

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = "재정 기록"
        verbose_name_plural = "재정 장부"