from django import forms
from .models import Repair
from core.models import UserProfile


class RepairForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = [
            'customer_name', 'customer_phone',
            'brand', 'model', 'imei', 'color',
            'diagnosis', 'comments',
            'estimated_cost', 'technician', 'estimated_delivery',
        ]
        widgets = {
            'customer_name':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'customer_phone':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 9999-9999'}),
            'brand':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Samsung, Apple, Xiaomi...'}),
            'model':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Galaxy A54, iPhone 13...'}),
            'imei':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15 dígitos'}),
            'color':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Negro, Blanco...'}),
            'diagnosis':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                      'placeholder': 'Describe la falla reportada por el cliente'}),
            'comments':         forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                      'placeholder': 'Notas internas del técnico (no se imprimen)'}),
            'estimated_cost':   forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'technician':       forms.Select(attrs={'class': 'form-select'}),
            'estimated_delivery': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter technicians to branch staff if branch provided
        tech_qs = UserProfile.objects.filter(is_active=True).exclude(role='superadmin')
        if branch:
            tech_qs = tech_qs.filter(branch=branch)
        self.fields['technician'].queryset = tech_qs
        self.fields['technician'].empty_label = '— Sin asignar —'


class RepairStatusForm(forms.ModelForm):
    class Meta:
        model = Repair
        fields = ['status', 'comments', 'final_cost']
        widgets = {
            'status':     forms.Select(attrs={'class': 'form-select'}),
            'comments':   forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'final_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class RepairFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-sm', 'placeholder': 'N° orden...'}
    ))
    customer_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-sm', 'placeholder': 'Nombre cliente...'}
    ))
    imei = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-sm', 'placeholder': 'IMEI / Serie...'}
    ))
    model = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control form-control-sm', 'placeholder': 'Modelo...'}
    ))
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + Repair.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})
    )
    technician = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(is_active=True).exclude(role='superadmin'),
        required=False,
        empty_label='Todos los técnicos',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
