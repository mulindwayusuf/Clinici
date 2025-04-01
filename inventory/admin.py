from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Medicine, StockTransaction, Sale, SaleItem, Employee, Attendance, User, Notification

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('employee', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'employee', 'role', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(Medicine)
admin.site.register(StockTransaction)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(User, UserAdmin)
admin.site.register(Notification)