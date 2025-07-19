from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    نموذج مستخدم مخصص يوسع AbstractUser لإضافة حقول is_admin و is_approved.
    يحل محل UserProfile لتبسيط إدارة المستخدمين.
    """
    is_admin = models.BooleanField(default=False, verbose_name="هل هو مدير؟")
    is_approved = models.BooleanField(default=False, verbose_name="هل تمت الموافقة عليه؟")

    # إضافة related_name لتجنب التعارض مع نموذج المستخدم الافتراضي
    # هذه الحقول ضرورية عند استخدام نموذج مستخدم مخصص
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_groups",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_permissions",
        related_query_name="custom_user",
    )

    def __str__(self):
        return self.username

class Product(models.Model):
    """
    نموذج المنتج لتخزين معلومات المنتجات المتاحة في المخزون.
    """
    name = models.CharField(max_length=100, verbose_name="اسم المنتج")
    description = models.TextField(blank=True, verbose_name="الوصف")
    quantity = models.IntegerField(default=0, verbose_name="الكمية المتاحة")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="صورة المنتج")
    category = models.CharField(max_length=50, default='medical_tools', verbose_name="الفئة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"

    def __str__(self):
        return self.name

class Cart(models.Model):
    """
    نموذج سلة التسوق لتخزين المنتجات التي أضافها المستخدم إلى سلة التسوق.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="المستخدم")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(verbose_name="الكمية في السلة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة للسلة")

    class Meta:
        verbose_name = "سلة تسوق"
        verbose_name_plural = "سلة التسوق"
        unique_together = ('user', 'product') # يضمن أن المستخدم لا يضيف نفس المنتج مرتين في السلة

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"

class Order(models.Model):
    """
    نموذج الطلب لتتبع الطلبات المقدمة من قبل المستخدمين.
    """
    STATUS_CHOICES = [
        ('Pending', 'معلق'),
        ('Approved', 'موافق عليه'),
        ('Rejected', 'مرفوض'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="المستخدم")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(verbose_name="الكمية المطلوبة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="حالة الطلب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الموافقة")

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ['-created_at'] # ترتيب الطلبات من الأحدث للأقدم

    def __str__(self):
        return f"طلب #{self.id} من {self.user.username} لـ {self.product.name}"

class Report(models.Model):
    """
    نموذج التقرير لتخزين التقارير الشهرية للاستهلاك.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="المستخدم")
    month = models.CharField(max_length=7, verbose_name="الشهر")  # Format: YYYY-MM
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    consumed = models.PositiveIntegerField(verbose_name="الكمية المستهلكة")
    remaining = models.IntegerField(verbose_name="الكمية المتبقية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التقرير")

    class Meta:
        verbose_name = "تقرير"
        verbose_name_plural = "التقارير"
        unique_together = ('user', 'month', 'product')

    def __str__(self):
        return f"تقرير {self.month} لـ {self.product.name} بواسطة {self.user.username}"

class ConsumptionRecord(models.Model):
    """
    نموذج لتسجيل كل عملية استهلاك لمنتج.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="المستخدم")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="المنتج")
    quantity = models.PositiveIntegerField(verbose_name="الكمية المستهلكة")
    consumed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الاستهلاك")

    class Meta:
        verbose_name = "سجل استهلاك"
        verbose_name_plural = "سجلات الاستهلاك"
        ordering = ['-consumed_at']

    def __str__(self):
        return f"{self.user.username} استهلك {self.quantity} من {self.product.name}"
