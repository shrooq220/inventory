from django.urls import path
from . import views

app_name = 'inventory' # هذا هو السطر الجديد الذي يجب إضافته لتحديد الـ namespace

urlpatterns = [
    path('login/', views.login_view, name='login'), # صفحة تسجيل الدخول
    path('register/', views.register_view, name='register'), # صفحة تسجيل مستخدم جديد
    path('logout/', views.logout_view, name='logout'), # تسجيل الخروج

    # روابط لوحة تحكم المستخدم
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'), # لوحة تحكم المستخدم (تم تغيير الاسم)
    path('place_order/<int:product_id>/', views.place_order, name='place_order'), # تقديم طلب لمنتج
    path('cart/', views.cart_view, name='cart'), # صفحة السلة
    path('order_tracking/', views.order_tracking_view, name='order_tracking_view'), # صفحة تتبع الطلبات

    # روابط لوحة تحكم المدير
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'), # لوحة تحكم المدير
    path('admin/users/<int:user_id>/approve/', views.user_approve, name='user_approve'), # موافقة على مستخدم (تم تغيير الاسم)
    path('admin/users/<int:user_id>/reject/', views.user_reject, name='user_reject'), # رفض مستخدم (تم تغيير الاسم)
    path('admin/orders/<int:order_id>/approve/', views.approve_order, name='approve_order'), # موافقة على طلب (تم تغيير الاسم)
    path('admin/orders/<int:order_id>/reject/', views.reject_order, name='reject_order'), # رفض طلب (تم تغيير الاسم)
    path('admin/products/add/', views.add_product, name='add_product'), # إضافة منتج (تم تغيير الاسم)
    path('admin/products/edit/<int:product_id>/', views.edit_product, name='edit_product'), # تعديل منتج (تم تغيير الاسم)
    path('admin/products/delete/<int:product_id>/', views.delete_product, name='delete_product'), # حذف منتج (تم تغيير الاسم)

    # روابط الملف الشخصي الجديدة
    path('profile/', views.user_profile_view, name='user_profile_view'), # ملف شخصي للمستخدم العادي
    path('admin/profile/', views.admin_profile_view, name='admin_profile_view'), # ملف شخصي للمدير
]
