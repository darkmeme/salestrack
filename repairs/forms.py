from django import forms
from .models import Repair, Technician


class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ['name', 'phone', 'email', 'branch', 'specialization', 'notes', 'is_active']
        widgets = {
            'name':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'phone':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 9999-9999'}),
            'email':          forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'branch':         forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pantallas, baterías, placa...'}),
            'notes':          forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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
        qs = Technician.objects.filter(is_active=True)
        if branch:
            qs = qs.filter(branch=branch)
        self.fields['technician'].queryset = qs
        self.fields['technician'].empty_label = '— Seleccione un técnico —'
        self.fields['technician'].required = True
        # Ensure these filter fields are explicitly required
        for f in ('customer_name', 'brand', 'model', 'diagnosis'):
            self.fields[f].required = True


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
        queryset=Technician.objects.filter(is_active=True),
        required=False,
        empty_label='Todos los técnicos',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
