from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-g&y$h1w_y6s1&_0kknb)!$q-hqm!zb_d#*+)$tv!55yatv7l&5' # احتفظ بهذا المفتاح سريًا في الإنتاج

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory', # تطبيق المخزون الخاص بك
     'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls' # تأكد أن هذا يشير إلى ملف urls.py الصحيح للمشروع الرئيسي

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR /'templates'], # تم تحديث هذا السطر ليشير إلى مجلد القوالب الرئيسي
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', # أضف هذا إذا كنت تريده في وضع DEBUG
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'ar-sa' # تم التعديل إلى ar-sa للغة العربية السعودية
TIME_ZONE = 'Asia/Riyadh' # تم التعديل إلى المنطقة الزمنية للرياض

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] # تأكد أن هذا المسار صحيح لمجلد static في جذر المشروع
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # تأكد أن هذا المسار صحيح لمجلد media في جذر المشروع


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# إعدادات البريد الإلكتروني (لاستخدام Gmail كمثال)
# ستحتاج إلى تمكين "Less secure app access" في حساب Gmail الخاص بك
# أو استخدام "App Passwords" إذا كنت تستخدم التحقق بخطوتين.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com' # استبدل ببريدك الإلكتروني
EMAIL_HOST_PASSWORD = 'your_email_password' # استبدل بكلمة مرور بريدك الإلكتروني أو كلمة مرور التطبيق

# مسار إعادة التوجيه بعد تسجيل الدخول
LOGIN_REDIRECT_URL = 'user_dashboard' # تم التغيير إلى user_dashboard
# مسار صفحة تسجيل الدخول
LOGIN_URL = 'login'

# تحديد نموذج المستخدم المخصص
AUTH_USER_MODEL = 'inventory.CustomUser' # هذا السطر حاسم، تأكد من وجوده
