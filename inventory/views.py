from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AbstractUser
from django.contrib import messages
from .models import Medicine, StockTransaction, Sale, SaleItem, Notification, Attendance, Employee
from .forms import MedicineForm, StockTransactionForm, SaleForm, EmployeeForm
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Sum
from django.db import transaction
import logging, os
from django.http import JsonResponse
from django.db import models


logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'Admin':
                return redirect('admin_dashboard')
            else:
                return redirect('employee_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'inventory/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def check_expirations():
    threshold_date = timezone.now().date() + timedelta(days=30)
    expiring_medicines = Medicine.objects.filter(
        expiration_date__lte=threshold_date,
        quantity__gt=0
    )
    print(f"Expiring medicines: {expiring_medicines.count()} - {list(expiring_medicines.values('name', 'expiration_date', 'quantity'))}")
    
    for medicine in expiring_medicines:
        if not Notification.objects.filter(
            medicine=medicine,
            message__contains=f"{medicine.name} expires on {medicine.expiration_date}"
        ).exists():
            exact_message = f"{medicine.name} expires on {medicine.expiration_date} - {medicine.quantity} left"
            Notification.objects.create(
                medicine=medicine,
                message=exact_message
            )
            print(f"Created expiration notification for {medicine.name} - {exact_message}")
    
    low_stock_threshold = 10
    low_stock_medicines = Medicine.objects.filter(quantity__lte=low_stock_threshold, quantity__gt=0)
    print(f"Low stock medicines: {low_stock_medicines.count()} - {list(low_stock_medicines.values('name', 'quantity'))}")
    
    for medicine in low_stock_medicines:
        if not Notification.objects.filter(
            medicine=medicine,
            message__contains=f"{medicine.name} is low on stock"
        ).exists():
            exact_low_message = f"{medicine.name} is low on stock - {medicine.quantity} left"
            Notification.objects.create(
                medicine=medicine,
                message=exact_low_message
            )
            print(f"Created low stock notification for {medicine.name} - {exact_low_message}")

    medicines_above_threshold = Medicine.objects.filter(quantity__gt=low_stock_threshold)
    for medicine in medicines_above_threshold:
        outdated_low_notifications = Notification.objects.filter(
            medicine=medicine,
            message__contains=f"{medicine.name} is low on stock",
            acknowledged=False
        )
        if outdated_low_notifications.exists():
            outdated_low_notifications.update(acknowledged=True)
            print(f"Cleared outdated low stock notification for {medicine.name} - now {medicine.quantity}")
def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'Admin':
        return redirect('login')
    
    check_expirations()
    notifications = Notification.objects.filter(acknowledged=False)
    
    today = timezone.now().date()
    today_sales = Sale.objects.filter(
        sale_date__date=today
    ).aggregate(
        total_sales=Sum('total_amount')
    )['total_sales'] or 0
    logger.debug(f"Admin Dashboard - Today: {today}, Today Sales: USh {today_sales}")
    
    medicines_count = Medicine.objects.count()
    employees_count = Employee.objects.count()
    low_stock_medicines = Medicine.objects.filter(quantity__lt=10)
    
    context = {
        'notifications': notifications,
        'medicines_count': medicines_count,
        'today_sales': today_sales,
        'employees_count': employees_count,
        'low_stock_medicines': low_stock_medicines,
    }
    return render(request, 'inventory/admin_dashboard.html', context)

def employee_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'Employee':
        return redirect('login')
    
    today = timezone.now().date()
    employee = request.user.employee

    # Get or create today's attendance record
    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today,
        defaults={'check_in': None}  # No check-in until button clicked
    )
    logger.debug(f"Attendance - Today: {today}, Employee: {employee.name}, Created: {created}, Check In: {attendance.check_in}, Check Out: {attendance.check_out}")

    if request.method == "POST":
        if "check_in" in request.POST and not attendance.check_in:
            attendance.check_in = timezone.now()
            attendance.save()
            messages.success(request, "Checked in successfully!")
        elif "check_out" in request.POST and attendance.check_in and not attendance.check_out:
            attendance.check_out = timezone.now()
            attendance.save()
            messages.success(request, "Checked out successfully!")

    # Today's employee-specific sales and items
    employee_transactions = StockTransaction.objects.filter(
        employee=employee,
        transaction_type='Sale',
        transaction_date__date=today
    )
    employee_items_sold = employee_transactions.aggregate(total_items=Sum('quantity'))['total_items'] or 0
    employee_sales = sum(
        t.sale_item.subtotal if t.sale_item else t.medicine.selling_price * t.quantity
        for t in employee_transactions
    )
    logger.debug(f"Employee Dashboard - Today: {today}, Employee Sales: USh {employee_sales}, Items Sold: {employee_items_sold}")

    # Clinic-wide today’s sales and items
    today_sales = Sale.objects.filter(sale_date__date=today).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    items_sold = SaleItem.objects.filter(sale__sale_date__date=today).aggregate(
        total=Sum('quantity')
    )['total'] or 0

    context = {
        'employee': employee,
        'attendance': attendance,
        'today_sales': today_sales,
        'items_sold': items_sold,
        'employee_sales': employee_sales,
        'employee_items_sold': employee_items_sold,
        'notifications': Notification.objects.filter(acknowledged=False),
    }
    return render(request, 'inventory/employee_dashboard.html', context)


def inventory_list(request):
    if not request.user.is_authenticated or request.user.role != 'Admin':
        return redirect('login')
    medicines = Medicine.objects.all()
    return render(request, 'inventory/inventory_list.html', {'medicines': medicines})

def add_medicine(request):
    if not request.user.is_authenticated or request.user.role != 'Admin':
        return redirect('login')
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save()
            StockTransaction.objects.create(
                medicine=medicine,
                transaction_type='Intake',
                quantity=medicine.quantity,
                employee=request.user.employee
            )
            messages.success(request, 'Medicine added successfully!')
            return redirect('inventory_list')
    else:
        form = MedicineForm()
    return render(request, 'inventory/add_medicine.html', {'form': form})

def edit_medicine(request, medicine_id):
    if not request.user.is_authenticated or request.user.role != 'Admin':
        return redirect('login')
    medicine = get_object_or_404(Medicine, id=medicine_id)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        stock_form = StockTransactionForm(request.POST) if 'transaction_type' in request.POST else None
        
        if form.is_valid():
            old_quantity = medicine.quantity
            form.save()
            new_quantity = form.instance.quantity
            
            if new_quantity != old_quantity and stock_form:
                if stock_form.is_valid():
                    quantity_diff = new_quantity - old_quantity
                    transaction_type = stock_form.cleaned_data['transaction_type']
                    StockTransaction.objects.create(
                        medicine=medicine,
                        transaction_type=transaction_type,
                        quantity=abs(quantity_diff),
                        employee=request.user.employee
                    )
            messages.success(request, 'Medicine updated successfully!')
            return redirect('inventory_list')
    else:
        form = MedicineForm(instance=medicine)
        stock_form = StockTransactionForm(initial={'medicine': medicine})
    
    return render(request, 'inventory/edit_medicine.html', {
        'form': form,
        'stock_form': stock_form,
        'medicine': medicine,
    })

def adjust_stock(request):
    if not request.user.is_authenticated or request.user.role != 'Admin':
        return redirect('login')
    if request.method == 'POST':
        medicine_id = request.POST.get('medicine')
        quantity = request.POST.get('quantity')
        medicine = get_object_or_404(Medicine, id=medicine_id)
        
        if quantity and quantity.isdigit():
            quantity = int(quantity)
            old_quantity = medicine.quantity
            medicine.quantity = quantity
            medicine.save()
            
            StockTransaction.objects.create(
                medicine=medicine,
                transaction_type='Adjust',
                quantity=abs(quantity - old_quantity),
                employee=request.user.employee
            )
            messages.success(request, f"Stock for {medicine.name} adjusted to {quantity}.")
            return redirect('inventory_list')
        else:
            messages.error(request, 'Please enter a valid quantity.')
    
    medicines = Medicine.objects.all()
    return render(request, 'inventory/adjust_stock.html', {'medicines': medicines})

@transaction.atomic
def add_sale(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    if request.method == 'POST':
        medicine_ids = request.POST.getlist('medicine_ids')
        quantities = request.POST.getlist('quantities')
        
        sale = Sale.objects.create(
            total_amount=0,
            sale_date=timezone.now()
        )
        total = 0
        for med_id, qty in zip(medicine_ids, quantities):
            qty = int(qty)
            if qty <= 0:
                continue
                
            medicine = Medicine.objects.get(id=med_id)
            if medicine.quantity < qty:
                sale.delete()
                messages.error(request, f"Insufficient stock for {medicine.name}")
                return redirect('add_sale')
            
            subtotal = medicine.selling_price * qty
            sale_item = SaleItem.objects.create(
                sale=sale,
                medicine=medicine,
                quantity=qty,
                subtotal=subtotal
            )
            medicine.quantity -= qty
            medicine.save()
            
            StockTransaction.objects.create(
                medicine=medicine,
                transaction_type='Sale',
                quantity=qty,
                employee=request.user.employee,
                sale_item=sale_item,
                transaction_date=timezone.now()
            )
            total += subtotal
        
        sale.total_amount = total
        sale.save()
        messages.success(request, 'Sale recorded successfully!')
        return redirect('receipt', sale_id=sale.id)
    
    medicines = Medicine.objects.filter(quantity__gt=0)
    return render(request, 'inventory/add_sale.html', {'medicines': medicines})

def sales_list(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    today = timezone.now().date()
    sales = Sale.objects.all().order_by('-sale_date')  # Default: all sales, newest first
    
    day = request.GET.get('day')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    employee_id = request.GET.get('employee')
    
    if day:
        sales = sales.filter(sale_date__date=day)
    elif start_date or end_date:
        if start_date:
            sales = sales.filter(sale_date__date__gte=start_date)
        if end_date:
            sales = sales.filter(sale_date__date__lte=end_date)
    # Removed: else: sales = sales.filter(sale_date__date=today)
    
    if employee_id:
        sales = sales.filter(saleitem__stocktransaction__employee_id=employee_id).distinct()
    
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    daily_revenue = Sale.objects.filter(sale_date__date=today).aggregate(total=Sum('total_amount'))['total'] or 0  # Always today’s revenue
    top_medicines = SaleItem.objects.filter(sale__in=sales).values('medicine__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]
    
    employees = Employee.objects.all()
    return render(request, 'inventory/sales_list.html', {
        'sales': sales,
        'employees': employees,
        'day': day,
        'start_date': start_date,
        'end_date': end_date,
        'selected_employee': employee_id,
        'total_sales': total_sales,
        'daily_revenue': daily_revenue,
        'top_medicines': top_medicines,
    })
def medicine_autocomplete(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    search_term = request.GET.get('term', '')
    details = request.GET.get('details', False)
    
    if details:
        # Return full details for selected medicine
        medicine = get_object_or_404(Medicine, name=search_term)
        data = [{
            'id': medicine.id,
            'name': medicine.name,
            'quantity': medicine.quantity,
            'selling_price': medicine.selling_price,
            'purchase_price': medicine.purchase_price,
            'expiration_date': medicine.expiration_date.strftime('%Y-%m-%d')
        }]
        return JsonResponse(data, safe=False)
    else:
        # Return autocomplete suggestions
        medicines = Medicine.objects.filter(
            Q(name__icontains=search_term) | 
            Q(name__istartswith=search_term)
        ).distinct()
        
        if 'id' in request.GET:
            # For stock history search that needs both id and name
            results = [{'id': med.id, 'value': med.name} for med in medicines[:10]]
        else:
            # For simple autocomplete
            results = list(medicines.values_list('name', flat=True)[:10])
        
        return JsonResponse(results, safe=False)

def receipt(request, sale_id):
    if not request.user.is_authenticated:
        return redirect('login')
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, 'inventory/receipt.html', {'sale': sale})

def acknowledge_notification(request, notification_id):
    if not request.user.is_authenticated:
        return redirect('login')
    notification = get_object_or_404(Notification, id=notification_id)
    notification.acknowledged = True
    notification.save()
    messages.success(request, 'Notification acknowledged!')
    dashboard = 'admin_dashboard' if request.user.role == 'Admin' else 'employee_dashboard'
    response = redirect(dashboard)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

def attendance_list(request):
    if not request.user.is_authenticated or request.user.role != 'Admin':
        return redirect('login')
    today = timezone.now().date()
    attendances = Attendance.objects.filter(date=today).order_by('-check_in')
    return render(request, 'inventory/attendance_list.html', {'attendances': attendances})

def stock_history(request):
    if not request.user.is_authenticated or request.user.role != 'Admin':
        return redirect('login')
    
    medicine_id = request.GET.get('medicine')
    medicines = Medicine.objects.all()
    transactions = None
    
    if medicine_id:
        transactions = StockTransaction.objects.filter(medicine_id=medicine_id).order_by('-transaction_date')
    
    return render(request, 'inventory/stock_history.html', {
        'medicines': medicines,
        'transactions': transactions,
        'selected_medicine': medicine_id,
    })
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import EmployeeForm, CustomPasswordChangeForm
from django.core.files.storage import FileSystemStorage
import os

@login_required
def profile(request):
    employee = request.user.employee
    
    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            form = EmployeeForm(request.POST, request.FILES, instance=employee)
            if form.is_valid():
                # Handle profile picture upload
                if 'profile_picture' in request.FILES:
                    # Delete old profile picture if it exists
                    old_pic = employee.profile_picture
                    if old_pic:
                        fs = FileSystemStorage()
                        if fs.exists(old_pic.name):
                            fs.delete(old_pic.name)
                    # Save new profile picture
                    form.save()
                else:
                    # Save without changing the profile picture
                    form.save()
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
        
        elif 'change_password_submit' in request.POST:
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important to keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile')
            else:
                # Add error messages for password change form
                for field, errors in password_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = EmployeeForm(instance=employee)
        password_form = CustomPasswordChangeForm(user=request.user)
    
    context = {
        'form': form,
        'password_form': password_form,
    }
    return render(request, 'inventory/profile.html', context)
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.conf import settings

def request_password_change(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = request.user.__class__.objects.get(employee__email=email)
            
            # Generate token and send email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            mail_subject = 'Password Change Request'
            message = render_to_string('inventory/password_reset_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': uid,
                'token': token,
            })
            
            send_mail(
                mail_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'We have sent you an email with instructions to reset your password.')
            return redirect('login')
        except request.user.__class__.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
    
    return render(request, 'inventory/request_password_change.html')

from django.core.files.storage import FileSystemStorage

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    employee = request.user.employee
    form = EmployeeForm(instance=employee)
    password_form = CustomPasswordChangeForm(user=request.user)

    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            form = EmployeeForm(request.POST, request.FILES, instance=employee)
            if form.is_valid():
                # Handle profile picture removal
                if 'remove_picture' in request.POST:
                    if employee.profile_picture:
                        # Delete the file from storage
                        fs = FileSystemStorage()
                        if fs.exists(employee.profile_picture.name):
                            fs.delete(employee.profile_picture.name)
                        # Clear the field in the database
                        employee.profile_picture = None
                        employee.save()
                
                # Handle new profile picture upload
                elif 'profile_picture' in request.FILES:
                    # Delete old picture if it exists
                    if employee.profile_picture:
                        fs = FileSystemStorage()
                        if fs.exists(employee.profile_picture.name):
                            fs.delete(employee.profile_picture.name)
                    # Save the form with new picture
                    form.save()
                else:
                    # Save without changing the picture
                    form.save()
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')

        elif 'change_password_submit' in request.POST:
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile')

    context = {
        'form': form,
        'password_form': password_form,
    }
    return render(request, 'inventory/profile.html', context)

from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.conf import settings

def request_password_change(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = request.user.__class__.objects.get(employee__email=email)
            
            # Generate token and send email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            mail_subject = 'Password Change Request'
            message = render_to_string('inventory/password_reset_email.html', {
                'user': user,
                'domain': request.get_host(),
                'uid': uid,
                'token': token,
            })
            
            send_mail(
                mail_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'We have sent you an email with instructions to reset your password.')
            return redirect('login')
        except request.user.__class__.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
    
    return render(request, 'inventory/request_password_change.html')

def confirm_password_change(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = request.user.__class__.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, request.user.__class__.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomPasswordChangeForm(user=user, data=request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                messages.success(request, 'Your password has been changed successfully!')
                return redirect('login')
        else:
            form = CustomPasswordChangeForm(user=user)
        
        return render(request, 'inventory/confirm_password_change.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('login')


