from django import forms
from .models import Medicine, StockTransaction, Sale, Employee
from django.utils import timezone

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'quantity', 'purchase_price', 'selling_price', 'expiration_date', 'date_added']
        labels = {
            'name': 'Medicine Name',
            'quantity': 'Quantity',
            'purchase_price': 'Purchase Price (USh)',
            'selling_price': 'Selling Price (USh)',
            'expiration_date': 'Expiration Date',
            'date_added': 'Date Added',
        }
        help_texts = {
            'purchase_price': 'Enter the purchase price in Ugandan Shillings (USh).',
            'selling_price': 'Enter the selling price in Ugandan Shillings (USh).',
        }
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'date_added': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['transaction_type', 'quantity']
        labels = {
            'transaction_type': 'Transaction Type',
            'quantity': 'Quantity',
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['total_amount']
        labels = {
            'total_amount': 'Total Amount (USh)',
        }
        help_texts = {
            'total_amount': 'Enter the total sale amount in Ugandan Shillings (USh).',
        }

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'contact_info']
        labels = {
            'name': 'Employee Name',
            'contact_info': 'Contact Information',
        }