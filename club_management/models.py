from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings



# 관리자
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'MANAGER') 
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


# 사용자
class User(AbstractUser):

    class RoleStatus(models.TextChoices):
        # ERD의 role (ENUM)
        GENERAL = 'GENERAL', '일반 회원'
        ADMIN = 'ADMIN', '운영자'
        MANAGER = 'MANAGER', '총관리자'
    username = None
    email = models.EmailField(_('email address'), unique=True)
    nickname = models.CharField(max_length=50, unique=True, default='none', verbose_name = "닉네임")
    role = models.CharField( max_length=50, choices=RoleStatus.choices, default=RoleStatus.GENERAL, verbose_name='사용자 역할')

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname'] #email, password는 기본적으로 유구된다.

    def __str__(self):
        return self.nickname
    
    class Meta:
        verbose_name='사용자'
        verbose_name_plural = '사용자 목록'

# 모임
class Group(models.Model):
    class GroupCategory(models.TextChoices):
        SPORTS = 'SPORTS', '체육'
        ART = 'ART', '미술'
        MUSIC = 'MUSIC', '음악'
        COOKING = 'COOKING', '요리/베이커리'
        READING = 'READING', '독서'
        OTHER = 'OTHER', '기타'
    class GroupStatus(models.TextChoices):
        RECRUITING = 'RECRUITING', '모집 중'
        CLOSED = 'CLOSED', '모집 마감'
        OPERATING = 'OPERATING', '운영 중'

    name = models.CharField(max_length=100, verbose_name='모임 이름')
    category = models.CharField( max_length=50, choices=GroupCategory.choices,verbose_name='카테고리')
    region = models.CharField(max_length=50, verbose_name="활동 지역")
    status = models.CharField( max_length=50,choices=GroupStatus.choices,default=GroupStatus.RECRUITING, verbose_name='모임 상태')
    description = models.TextField(verbose_name='모임 소개')
    max_members = models.PositiveIntegerField(verbose_name='최대 인원')
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_groups', verbose_name='개설자')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

#모임 멤버
class GroupMember(models.Model):
    class MemberRole(models.TextChoices):
        LEADER = 'LEADER', '리더' 
        ADMIN = 'ADMIN', '총무/운영진' 
        MEMBER = 'MEMBER', '일반 회원'
        PENDING = 'PENDING', '가입 대기 중'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    member_role = models.CharField( max_length=50, choices=MemberRole.choices, default=MemberRole.PENDING, verbose_name='멤버 역할/권한')
    joined_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')
        verbose_name = '모임 멤버'
        verbose_name_plural = '모임 멤버 목록'

    def __str__(self):
        return f'{self.user.username} - {self.group.name} ({self.get_member_role_display()})'


# 활동 일정
class ActivitySchedule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='schedules')
    title = models.CharField(max_length=255, verbose_name='일정 제목')
    date_time = models.DateTimeField(verbose_name='날짜 및 시간')
    location = models.CharField(max_length=255, verbose_name='장소')
    content = models.TextField(verbose_name='활동 내용')
    participation_fee = models.PositiveIntegerField( default=0, verbose_name='참가 회비', help_text='이 일정에 참여하는 멤버가 납부해야 할 금액')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_schedules')

    def __str__(self):
        return f'{self.group.name} - {self.title} ({self.date_time.strftime("%Y-%m-%d %H:%M")})'

    class Meta:
        ordering = ['date_time']


# RSVP
class RSVP(models.Model):
    class AttendanceStatus(models.TextChoices):
        ATTENDING = 'ATTENDING', '참석'
        NOT_ATTENDING = 'NOT_ATTENDING', '불참'
        PENDING = 'PENDING', '미정/미응답' 
        PRESENT = 'PRESENT', '출석 (운영진 체크)' 
        ABSENT = 'ABSENT', '결석 (운영진 체크)'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.ForeignKey(ActivitySchedule, on_delete=models.CASCADE)
    attendance_status = models.CharField( max_length=50, choices=AttendanceStatus.choices, default=AttendanceStatus.PENDING, verbose_name='참석/출석 상태')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='응답 시각')

    class Meta:
        unique_together = ('user', 'schedule')
        verbose_name = '일정 참석 응답/출석'
        verbose_name_plural = '일정 참석 응답/출석 목록'

    def __str__(self):
        return f'{self.user.username} - {self.schedule.title}: {self.get_attendance_status_display()}'



# FINANCIAL_TRANSACTION)
class FinancialTransaction(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey( User, on_delete=models.SET_NULL,  null=True,  blank=True,related_name='financial_records',  verbose_name='관련 사용자 (납부자/지출 처리자)')
    amount = models.PositiveIntegerField(verbose_name='금액')
    description = models.CharField(max_length=255, verbose_name='내용')
    transaction_date = models.DateField(auto_now_add=True, verbose_name='거래 날짜')
    
    def __str__(self):
        return f'[{self.group.name}] {self.get_type_display()} {self.amount}원: {self.description}'

    class Meta:
        ordering = ['-transaction_date']


