from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Product, Cart, Order, Report, ConsumptionRecord
from datetime import datetime

# تخصيص لوحة تحكم CustomUser
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_approved', 'is_admin')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'is_approved', 'is_admin')
    fieldsets = BaseUserAdmin.fieldsets + (
        (('Custom Fields'), {'fields': ('is_admin', 'is_approved',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (('Custom Fields'), {'fields': ('is_admin', 'is_approved',)}),
    )

# تسجيل Product في لوحة تحكم المدير
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'category', 'created_at', 'image')
    search_fields = ('name', 'description', 'category')
    list_filter = ('category', 'created_at')

# تسجيل Cart في لوحة تحكم المدير
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)

# تسجيل Order في لوحة تحكم المدير
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'status', 'created_at', 'approved_at')
    list_filter = ('status', 'created_at', 'user')
    search_fields = ('user__username', 'product__name')
    raw_id_fields = ('user', 'product')
    actions = ['approve_orders', 'reject_orders']

    def approve_orders(self, request, queryset):
        for order in queryset:
            if order.status == 'Pending':
                if order.quantity > order.product.quantity:
                    self.message_user(request, f'لا يمكن الموافقة على الطلب #{order.id} لمنتج {order.product.name} لأن الكمية المطلوبة ({order.quantity}) أكبر من المتاح ({order.product.quantity}).', level='error')
                    continue

                order.status = 'Approved'
                order.approved_at = datetime.now()
                order.product.quantity -= order.quantity
                order.product.save()
                order.save()
                Report.objects.create(
                    user=order.user,
                    month=datetime.now().strftime('%Y-%m'),
                    product=order.product,
                    consumed=order.quantity,
                    remaining=order.product.quantity
                )
                ConsumptionRecord.objects.create(
                    user=order.user,
                    product=order.product,
                    quantity=order.quantity
                )
        self.message_user(request, "تمت الموافقة على الطلبات المحددة (مع التحقق من المخزون).")
    approve_orders.short_description = "الموافقة على الطلبات المحددة"

    def reject_orders(self, request, queryset):
        for order in queryset:
            if order.status == 'Pending':
                order.status = 'Rejected'
                order.save()
        self.message_user(request, "تم رفض الطلبات المحددة.")
    reject_orders.short_description = "رفض الطلبات المحددة"

# تسجيل Report في لوحة تحكم المدير
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'product', 'consumed', 'remaining', 'created_at')
    search_fields = ('user__username', 'product__name', 'month')
    list_filter = ('month', 'created_at')

# تسجيل ConsumptionRecord في لوحة تحكم المدير
@admin.register(ConsumptionRecord)
class ConsumptionRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'consumed_at')
    list_filter = ('consumed_at', 'user', 'product')
    search_fields = ('user__username', 'product__name')