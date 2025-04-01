from django.contrib import admin
from django.urls import path
from inventory import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('employee_dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.add_medicine, name='add_medicine'),
    path('inventory/edit/<int:medicine_id>/', views.edit_medicine, name='edit_medicine'),
    path('inventory/adjust/', views.adjust_stock, name='adjust_stock'),  # Added
    path('inventory/history/', views.stock_history, name='stock_history'),  # Added
    path('sale/add/', views.add_sale, name='add_sale'),
    path('sales/', views.sales_list, name='sales_list'),
    path('receipt/<int:sale_id>/', views.receipt, name='receipt'),
    path('notification/acknowledge/<int:notification_id>/', views.acknowledge_notification, name='acknowledge_notification'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('profile/', views.profile, name='profile'),  
]