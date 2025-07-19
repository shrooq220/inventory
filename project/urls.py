# project/urls.py
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls), # لوحة تحكم Django الإدارية
    # تم تغيير إعادة التوجيه لتوجه إلى اسم الـ URL الصحيح لصفحة تسجيل الدخول في تطبيق inventory
    path('', RedirectView.as_view(url=reverse_lazy('inventory:login'), permanent=False)), # تم تحديث reverse_lazy لاستخدام الـ namespace
    # هذا السطر هو الأهم، تأكد من وجوده بالضبط هكذا مع تحديد الـ namespace
    path('inventory/', include('inventory.urls', namespace='inventory')), 
]

# لخدمة ملفات الميديا والملفات الثابتة في وضع التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

