from django.contrib import admin
from .models import Category, Club, ClubMember, Event, Attendance, FinancialRecord

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'region', 'creator', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'region')
    search_fields = ('name', 'description', 'region')

@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ('club', 'user', 'role', 'status', 'joined_at')
    list_filter = ('club', 'role', 'status')
    search_fields = ('club__name', 'user__username')
    raw_id_fields = ('club', 'user') # 사용자/모임이 많아질 경우 효율적

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'start_time', 'end_time', 'required_fee')
    list_filter = ('club', 'start_time')
    search_fields = ('title', 'location', 'club__name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('event', 'member', 'rsvp_status', 'actual_status', 'checked_by')
    list_filter = ('event__club', 'rsvp_status', 'actual_status')
    search_fields = ('event__title', 'member__user__username')

@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ('club', 'record_type', 'amount', 'description', 'recorded_by', 'recorded_at')
    list_filter = ('club', 'record_type')
    search_fields = ('description', 'club__name')