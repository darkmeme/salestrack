from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Branch, UserProfile, SystemSettings


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'code', 'address', 'phone', 'email', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserProfileForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'branch', 'phone', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'currency_symbol', 'currency_name', 'tax_name', 'tax_rate',
            'store_name', 'store_logo', 'store_address', 'store_phone', 'store_email',
            'invoice_header', 'invoice_footer', 'invoice_show_logo', 'invoice_show_tax_detail',
        ]
        widgets = {
            'currency_symbol':         forms.TextInput(attrs={'class': 'form-control', 'maxlength': 10}),
            'currency_name':           forms.TextInput(attrs={'class': 'form-control'}),
            'tax_name':                forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate':                forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'store_name':              forms.TextInput(attrs={'class': 'form-control'}),
            'store_logo':              forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'store_address':           forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'store_phone':             forms.TextInput(attrs={'class': 'form-control'}),
            'store_email':             forms.EmailInput(attrs={'class': 'form-control'}),
            'invoice_header':          forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                             'placeholder': 'Texto en la parte superior de la factura'}),
            'invoice_footer':          forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                             'placeholder': 'Texto al pie de la factura'}),
            'invoice_show_logo':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invoice_show_tax_detail': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'currency_symbol':         'Símbolo de moneda',
            'currency_name':           'Nombre de la moneda',
            'tax_name':                'Nombre del impuesto',
            'tax_rate':                'Porcentaje del impuesto (%)',
            'store_name':              'Nombre de la tienda',
            'store_logo':              'Logo',
            'store_address':           'Dirección',
            'store_phone':             'Teléfono',
            'store_email':             'Correo electrónico',
            'invoice_header':          'Encabezado de factura',
            'invoice_footer':          'Pie de factura',
            'invoice_show_logo':       'Mostrar logo en factura',
            'invoice_show_tax_detail': 'Mostrar desglose de impuesto',
        }
