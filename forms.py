"""
تعريف نماذج (Forms) لتسهيل التعامل مع بيانات المستخدمين والمنتجات.
"""

from django import forms
from .models import CustomUser, Product # تم استيراد CustomUser و Product

# نموذج تسجيل مستخدم جديد
class RegisterForm(forms.Form): # تم التغيير إلى forms.Form لأنه لا يتصل مباشرة بنموذج
    username = forms.CharField(max_length=150, label="اسم المستخدم")
    email = forms.EmailField(label="البريد الإلكتروني")
    password = forms.CharField(widget=forms.PasswordInput, label="كلمة المرور")
    password2 = forms.CharField(widget=forms.PasswordInput, label="تأكيد كلمة المرور")

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("اسم المستخدم هذا موجود بالفعل.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("البريد الإلكتروني هذا مستخدم بالفعل.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2 and password != password2:
            self.add_error('password2', "كلمتا المرور غير متطابقتين.")
        return cleaned_data

# نموذج إضافة/تعديل منتج (للمدير)
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'quantity', 'image', 'category'] # إضافة image و category
        labels = {
            'name': 'اسم المنتج',
            'description': 'الوصف',
            'quantity': 'الكمية المتاحة',
            'image': 'صورة المنتج',
            'category': 'الفئة',
        }