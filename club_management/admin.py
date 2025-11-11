# yourapp/admin.py
from django.contrib import admin
from .models import User, Group, GroupMember, ActivitySchedule, RSVP, FinancialTransaction

admin.site.register(User)
admin.site.register(Group)
admin.site.register(GroupMember)
admin.site.register(ActivitySchedule)
admin.site.register(RSVP)
admin.site.register(FinancialTransaction)