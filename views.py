from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum
from datetime import datetime, timedelta
import calendar
from django.contrib import messages

# استيراد CustomUser والنماذج الأخرى
from .models import Product, Order, ConsumptionRecord, CustomUser, Cart, Report
from .forms import RegisterForm, ProductForm

# دالة مساعدة للتحقق مما إذا كان المستخدم أدمن
def is_admin(user):
    """يتحقق مما إذا كان المستخدم لديه صلاحيات المدير."""
    return user.is_admin

# 👤 عرض صفحة تسجيل الدخول
def login_view(request):
    """
    يعالج تسجيل دخول المستخدمين (المديرين والمستخدمين العاديين).
    يوجه المستخدمين بناءً على دورهم وحالة الموافقة.
    """
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace
        return redirect('inventory:user_dashboard') # تم التحديث لاستخدام الـ namespace

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_admin:
                login(request, user)
                messages.success(request, f'مرحباً بك يا مدير {user.username}!')
                return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace
            # إذا كان مستخدم عادي، تحقق من الموافقة
            if user.is_approved:
                login(request, user)
                messages.success(request, f'مرحباً بك {user.username}!')
                return redirect('inventory:user_dashboard') # تم التحديث لاستخدام الـ namespace
            else:
                messages.error(request, 'حسابك بانتظار موافقة المدير.')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
    return render(request, 'login.html')

# 👤 عرض صفحة تسجيل مستخدم جديد
def register_view(request):
    """
    يعالج طلبات تسجيل المستخدمين الجدد.
    ينشئ حساب CustomUser ويضع is_approved و is_active على False حتى تتم الموافقة.
    """
    if request.user.is_authenticated:
        return redirect('inventory:user_dashboard') # تم التحديث لاستخدام الـ namespace

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # إنشاء المستخدم مباشرة وتعيين is_approved=False و is_active=False
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                is_approved=False, # بانتظار موافقة المدير
                is_active=False # غير نشط حتى تتم الموافقة
            )
            messages.success(request, 'تم إرسال طلب التسجيل بنجاح. حسابك بانتظار موافقة المدير.')
            return redirect('inventory:login') # تم التحديث لاستخدام الـ namespace
        else:
            # رسائل الخطأ من النموذج ستظهر تلقائياً في القالب
            messages.error(request, 'حدث خطأ أثناء التسجيل. يرجى التحقق من البيانات المدخلة.')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# 👤 تسجيل الخروج
@login_required
def logout_view(request):
    """يسجل خروج المستخدم الحالي ويعيد توجيهه إلى صفحة تسجيل الدخول."""
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح.')
    return redirect('inventory:login') # تم التحديث لاستخدام الـ namespace

# 🛒 لوحة تحكم المستخدم
@login_required
# التحقق من is_approved مباشرة من request.user لغير المديرين
@user_passes_test(lambda u: u.is_approved if not u.is_admin else True, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def user_dashboard(request): # تم تغيير اسم الدالة من dashboard إلى user_dashboard
    """
    يعرض لوحة تحكم المستخدم مع المنتجات المتاحة،
    ويعالج إضافة المنتجات إلى السلة.
    """
    # إضافة منطق تصفية المنتجات حسب الفئة والبحث
    category = request.GET.get('category', 'all')
    query = request.GET.get('q', '')
    products = Product.objects.all()
    if category != 'all':
        products = products.filter(category=category)
    if query:
        products = products.filter(name__icontains=query)
    
    if request.method == 'POST':
        product_id = request.POST['product_id']
        quantity = int(request.POST['quantity'])
        product = get_object_or_404(Product, id=product_id)
        
        if quantity > 0 and quantity <= product.quantity:
            # إضافة المنتج إلى سلة التسوق (Cart) أو تحديث الكمية إذا كان موجودًا
            cart_item, created = Cart.objects.get_or_create(
                user=request.user, 
                product=product,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            messages.success(request, 'تمت إضافة المنتج إلى السلة.')
        else:
            messages.error(request, 'الكمية غير متوفرة أو غير صالحة.')
        return redirect('inventory:user_dashboard') # تم التحديث لاستخدام الـ namespace

    return render(request, 'inventory/user_dashboard.html', {'products': products, 'category': category, 'query': query})

# 🛒 عرض صفحة السلة
@login_required
def cart_view(request):
    """
    يعرض سلة التسوق للمستخدم، ويتيح تحديث الكميات، إزالة المنتجات، وتأكيد الطلب.
    """
    if request.user.is_admin: # منع المديرين من الوصول إلى سلة التسوق
        return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace
    
    cart_items = Cart.objects.filter(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_cart':
            for item in cart_items:
                quantity_key = f'quantity_{item.id}'
                if quantity_key in request.POST:
                    new_quantity = int(request.POST[quantity_key])
                    if new_quantity > 0 and new_quantity <= item.product.quantity:
                        item.quantity = new_quantity
                        item.save()
                    elif new_quantity <= 0: # إذا كانت الكمية 0 أو أقل، احذف العنصر من السلة
                        item.delete()
                    else:
                        messages.error(request, f'الكمية المطلوبة لـ {item.product.name} غير متوفرة ({item.product.quantity} متاح).')
            messages.success(request, 'تم تحديث السلة.')
        
        elif action == 'confirm_order':
            if not cart_items.exists(): # منع تأكيد طلب سلة فارغة
                messages.error(request, 'لا يمكن تأكيد طلب من سلة فارغة.')
                return redirect('inventory:cart_view') # تم التحديث لاستخدام الـ namespace

            for item in cart_items:
                # التحقق مرة أخرى من الكمية المتاحة قبل إنشاء الطلب
                product = item.product
                if item.quantity > product.quantity:
                    messages.error(request, f'الكمية المطلوبة لـ {product.name} ({item.quantity}) أكبر من المتاح ({product.quantity}). يرجى تعديل السلة.')
                    return redirect('inventory:cart_view') # العودة للسلة إذا كانت الكمية غير متوفرة

                # إنشاء طلب جديد لكل عنصر في السلة وتعيين الحالة إلى 'Pending'
                Order.objects.create(user=request.user, product=product, quantity=item.quantity, status='Pending') # تم إضافة status='Pending'
                # لا تقم بخصم الكمية من هنا، سيتم خصمها عند الموافقة عليها من قبل المدير
                item.delete() # حذف العنصر من السلة بعد تأكيد الطلب
            messages.success(request, 'تم تأكيد الطلب وإرساله إلى الإدارة. حالته قيد الانتظار.')
            return redirect('inventory:order_tracking_view') # التوجيه إلى صفحة تتبع الطلبات باستخدام الـ namespace
        
        elif action and action.startswith('remove_item_'): # معالجة زر الإزالة الفردي
            item_id = action.split('_')[2]
            item_to_remove = get_object_or_404(Cart, id=item_id, user=request.user)
            item_to_remove.delete()
            messages.success(request, f'تمت إزالة {item_to_remove.product.name} من السلة.')
            return redirect('inventory:cart_view') # تم التحديث لاستخدام الـ namespace
        
        return redirect('inventory:cart_view') # تم التحديث لاستخدام الـ namespace
    
    return render(request, 'cart.html', {'cart_items': cart_items})

# 🛒 عرض صفحة تتبع الطلبات
@login_required
def order_tracking_view(request):
    """يعرض الطلبات السابقة للمستخدم وحالتها."""
    if request.user.is_admin: # منع المديرين من الوصول إلى تتبع الطلبات الخاص بالمستخدمين
        return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_tracking.html', {'orders': orders})

# 🛠️ لوحة تحكم المدير
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def admin_dashboard(request):
    """
    يعرض لوحة تحكم المدير مع طلبات تسجيل المستخدمين المعلقة،
    إدارة المنتجات، إدارة الطلبات، وتقارير الاستهلاك.
    ويعالج جميع إجراءات POST المتعلقة بهذه الأقسام.
    """
    users = CustomUser.objects.filter(is_admin=False) # المستخدمون العاديون
    products = Product.objects.all()
    orders = Order.objects.all().order_by('-created_at')
    reports = Report.objects.all().order_by('-created_at') # جلب جميع التقارير
    consumption_records = ConsumptionRecord.objects.all().order_by('-consumed_at') # جلب جميع سجلات الاستهلاك
    
    # حساب إجمالي الاستهلاك لكل منتج (للوحة تحكم المدير)
    consumption_data = ConsumptionRecord.objects.values('product__name', 'user__username').annotate(total_consumed=Sum('quantity')).order_by('-total_consumed')

    # تم نقل منطق معالجة الـ POST إلى دوال منفصلة
    # هذه الدالة الآن تعرض البيانات فقط
    return render(request, 'inventory/admin_dashboard.html', {
        'users': users,
        'products': products,
        'orders': orders,
        'reports': reports,
        'consumption_records': consumption_records,
        'admin_monthly_consumption': consumption_data,
        'current_month': datetime.now().strftime('%B %Y')
    })

# ➕ إضافة منتج جديد (للمدير)
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def add_product(request): # تم تغيير اسم الدالة من product_add إلى add_product
    """يعالج إضافة منتج جديد."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES) # إضافة request.FILES لدعم رفع الصور
        if form.is_valid():
            form.save()
            messages.success(request, 'تمت إضافة المنتج بنجاح.')
            return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"خطأ في حقل {field}: {error}")
            messages.error(request, 'حدث خطأ أثناء إضافة المنتج. يرجى التحقق من البيانات المدخلة.')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

# ✏️ تعديل منتج موجود (للمدير)
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def edit_product(request, product_id): # تم تغيير اسم الدالة من product_edit إلى edit_product
    """يعالج تعديل منتج موجود."""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product) # إضافة request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل المنتج بنجاح.')
            return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"خطأ في حقل {field}: {error}")
            messages.error(request, 'حدث خطأ أثناء تعديل المنتج. يرجى التحقق من البيانات المدخلة.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'edit_product.html', {'form': form, 'product': product})

# 🗑️ حذف منتج (للمدير)
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def delete_product(request, product_id): # تم تغيير اسم الدالة من product_delete إلى delete_product
    """يعالج حذف منتج."""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'تم حذف المنتج بنجاح.')
        return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace
    return render(request, 'delete_product_confirm.html', {'product': product})

# ✅ موافقة المدير على طلب تسجيل مستخدم
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def user_approve(request, user_id):
    """يوافق على طلب تسجيل مستخدم جديد."""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_approved = True
    user.is_active = True
    user.save()

    # send_mail(
    #     'تمت الموافقة على حسابك ✅',
    #     f"مرحباً {user.username},\n\nتهانينا، تمت الموافقة على حسابك في نظام إدارة المخزون. يمكنك الآن تسجيل الدخول والبدء في استخدام النظام.\n\nمع خالص التقدير,\nفريق إدارة المخزون",
    #     settings.EMAIL_HOST_USER,
    #     [user.email],
    #     fail_silently=False,
    # )
    messages.success(request, f'تمت الموافقة على المستخدم {user.username}.')
    return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace

# ❌ رفض المدير لطلب تسجيل مستخدم
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def user_reject(request, user_id):
    """يرفض طلب تسجيل مستخدم جديد ويحذف المستخدم."""
    user = get_object_or_404(CustomUser, id=user_id)
    username = user.username
    user_email = user.email
    user.delete()

    # send_mail(
    #     'طلب حسابك مرفوض ❌',
    #     f"مرحباً {username},\n\nنأسف لإبلاغك أن طلب حسابك في نظام إدارة المخزون قد تم رفضه.\n\nمع خالص التقدير,\nفريق إدارة المخزون",
    #     settings.EMAIL_HOST_USER,
    #     [user_email],
    #     fail_silently=False,
    # )
    messages.info(request, f'تم رفض حساب المستخدم {username} وحذفه.')
    return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace

# ✅ موافقة المدير على الطلب
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def approve_order(request, order_id): # تم تغيير اسم الدالة من order_approve إلى approve_order
    """يوافق على طلب منتج."""
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'Pending':
        # التحقق من الكمية المتاحة قبل الموافقة
        if order.quantity > order.product.quantity:
            messages.error(request, f'لا يمكن الموافقة على الطلب #{order.id} لمنتج {order.product.name} لأن الكمية المطلوبة ({order.quantity}) أكبر من المتاح ({order.product.quantity}).')
            return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace

        order.status = 'Approved'
        order.approved_at = datetime.now()
        order.product.quantity -= order.quantity # خصم الكمية من المخزون
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

        # send_mail(
        #     'طلبك تمت الموافقة عليه ✅',
        #     f"مرحباً {order.user.username},\n\nتمت الموافقة على طلبك لمنتج '{order.product.name}' بكمية {order.quantity}.\n\nيمكنك الآن استلام طلبك من المخزن. يرجى التنسيق مع إدارة المخزن لتحديد موعد الاستلام.\n\nمع خالص التقدير,\nفريق إدارة المخزون",
        #     settings.EMAIL_HOST_USER,
        #     [order.user.email],
        #     fail_silently=False,
        # )
        messages.success(request, f'تمت الموافقة على الطلب #{order.id}.')
    else:
        messages.warning(request, f'لا يمكن الموافقة على الطلب #{order.id} لأنه ليس في حالة "معلق".')
    return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace

# ❌ رفض المدير للطلب
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def reject_order(request, order_id): # تم تغيير اسم الدالة من order_reject إلى reject_order
    """يرفض طلب منتج."""
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'Pending':
        order.status = 'Rejected'
        order.save()

        # send_mail(
        #     'طلبك مرفوض ❌',
        #     f"مرحباً {order.user.username},\n\nنأسف لإبلاغك أن طلبك لمنتج '{order.product.name}' بكمية {order.quantity} قد تم رفضه.\n\nلأي استفسارات، يرجى التواصل مع إدارة المخزون.\n\nمع خالص التقدير,\nفريق إدارة المخزون",
        #     settings.EMAIL_HOST_USER,
        #     [order.user.email],
        #     fail_silently=False,
        # )
        messages.info(request, f'تم رفض الطلب #{order.id}.')
    else:
        messages.warning(request, f'لا يمكن رفض الطلب #{order.id} لأنه ليس في حالة "معلق".')
    return redirect('inventory:admin_dashboard') # تم التحديث لاستخدام الـ namespace

# 🛒 تقديم طلب جديد (صفحة منفصلة لطلب منتج واحد)
@login_required
@user_passes_test(lambda u: u.is_approved if not u.is_admin else True, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def place_order(request, product_id):
    """
    يعالج طلب المستخدم لمنتج واحد من صفحة المنتجات.
    """
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        try:
            qty = int(request.POST['quantity'])
            if qty > 0 and qty <= product.quantity:
                # إضافة المنتج إلى سلة التسوق (Cart)
                cart_item, created = Cart.objects.get_or_create(
                    user=request.user, 
                    product=product,
                    defaults={'quantity': qty}
                )
                if not created:
                    cart_item.quantity += qty
                    cart_item.save()
                messages.success(request, 'تمت إضافة المنتج إلى السلة.')
                return redirect('inventory:user_dashboard') # تم التحديث لاستخدام الـ namespace
            else:
                messages.error(request, 'الكمية المطلوبة غير صالحة أو أكبر من المتاح.')
        except ValueError:
            messages.error(request, 'الكمية يجب أن تكون رقمًا صحيحًا.')
    return render(request, 'place_order.html', {'product': product})


# 👤 صفحة الملف الشخصي للمستخدم العادي
@login_required
@user_passes_test(lambda u: u.is_approved if not u.is_admin else True, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def user_profile_view(request):
    """يعرض تفاصيل الملف الشخصي للمستخدم العادي."""
    context = {
        'user_obj': request.user,
    }
    return render(request, 'user_profile.html', context)

# 👤 صفحة الملف الشخصي للمدير
@login_required
@user_passes_test(is_admin, login_url='inventory:login') # تم التحديث لاستخدام الـ namespace
def admin_profile_view(request):
    """يعرض تفاصيل الملف الشخصي للمدير."""
    context = {
        'user_obj': request.user,
    }
    return render(request, 'admin_profile.html', context)
