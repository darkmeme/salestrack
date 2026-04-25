from django import forms
from .models import Category, Supplier, Product, BranchStock, StockTransfer, StockTransferItem


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'supplier', 'description',
                  'price', 'cost', 'min_stock', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StockAdjustForm(forms.Form):
    branch = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        from core.models import Branch
        super().__init__(*args, **kwargs)
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True)


class StockTransferForm(forms.ModelForm):
    class Meta:
        model = StockTransfer
        fields = ['origin_branch', 'destination_branch', 'notes']
        widgets = {
            'origin_branch': forms.Select(attrs={'class': 'form-select'}),
            'destination_branch': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        from core.models import Branch
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        active_branches = Branch.objects.filter(is_active=True)
        self.fields['origin_branch'].queryset = active_branches
        self.fields['destination_branch'].queryset = active_branches
        if user and not user.is_superadmin:
            self.fields['origin_branch'].initial = user.branch
            self.fields['origin_branch'].queryset = Branch.objects.filter(pk=user.branch.pk)

    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin_branch')
        destination = cleaned_data.get('destination_branch')
        if origin and destination and origin == destination:
            raise forms.ValidationError('La sucursal de origen y destino no pueden ser la misma.')
        return cleaned_data
