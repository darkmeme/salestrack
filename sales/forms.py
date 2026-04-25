from django import forms
from .models import Customer, Sale, Payment


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SaleFilterForm(forms.Form):
    branch = forms.ModelChoiceField(
        queryset=None, required=False, empty_label='Todas las sucursales',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    date_from = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Todos')] + Sale.STATUS_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    def __init__(self, *args, **kwargs):
        from core.models import Branch
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True)
