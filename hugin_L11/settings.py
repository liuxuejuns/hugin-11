"""
Django settings for hugin_L11 project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os
import logging
import time

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'tcu)nwove6g_wuf2eznt=cq@563&4d)mtm^jlgdu3e!dse5w%v'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
# 跨域
# ALLOWED_HOSTS = ['*']
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = '*'
CORS_ORIGIN_WHITELIST = ()
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)
CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'connection',
    'cookie',
)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',  # channels
    'testapp',
    'history',  # history testrecord
    'area',
    'rack',
    'component',
    'testrecord',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'public.middleware.APIMiddleware',
]
# 跨域
# ALLOWED_HOSTS = ['*']
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = '*'
CORS_ORIGIN_WHITELIST = ()
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)
CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'connection',
    'cookie',
)
ROOT_URLCONF = 'hugin_L11.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Channels
# WSGI_APPLICATION = 'hugin_L11.asgi.application'
ASGI_APPLICATION = 'hugin_L11.asgi.application'

# default channel layer (test)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {},
    # 主数据库
    'l11_test_primary': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'l11_test_primary',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': 'l11-test-primary',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_l11_test',
            'CHARSET': 'utf8',
        },
    },
    # 从数据库
    'l11_test_replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'l11_test_primary',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': 'l11-test-replica',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_l11_test_history',
            'CHARSET': 'utf8',
        },
    },
}

DATABASE_ROUTERS = ['hugin_L11.database_router.DatabaseAppsRouter']


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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

# redis settings
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": "redis://10.41.95.85:8909/1",
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#     }
# }
# 服务器
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://l11-redis-service:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.mkdir(os.path.join(BASE_DIR, 'logs'))
# log setting

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        "standard": {
            "format": "[%(asctime)s] [%(filename)s:%(lineno)d] [%(module)s:%(funcName)s] [%(levelname)s]- %(message)s",
        },
        "simple": {"format": "%(asctime)s %(levelname)s - %(message)s"},
    },
    'filters': {},
    'handlers': {
        'default': {
            'level': logging.INFO,
            'class': 'logging.handlers.RotatingFileHandler',
            # 'filename': os.path.join(BASE_DIR,'logs','info_%s.log'%time.strftime('%Y-%m-%d', time.localtime())),
            'filename': os.path.join(BASE_DIR, 'logs/L11_debug.log'),
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 3,  # 备份数
            'formatter': 'simple',
            'encoding': 'utf-8',
        },
        'error': {
            'level': logging.ERROR,
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            # 'filename': os.path.join(BASE_DIR,'logs','error_%s.log'%time.strftime('%Y-%m-%d', time.localtime())),
            'filename': os.path.join(BASE_DIR, 'logs/L11_error.log'),
            'encoding': 'utf-8',
            'maxBytes': 1024 * 1024 * 5,  # 日志大小 5M
            'backupCount': 7,
        },
        'api': {
            'level': logging.INFO,
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'simple',
            # 'filename': os.path.join(BASE_DIR,'logs','api_%s.log'%time.strftime('%Y-%m-%d', time.localtime())),
            'filename': os.path.join(BASE_DIR, 'logs/L11_api.log'),
            'encoding': 'utf-8',
            'maxBytes': 1024 * 1024 * 5,  # 日志大小 5M
            'backupCount': 3,
        },
        # 控制台输出
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'default': {
            'handlers': ['default', 'error'],
            'level': logging.INFO,
        },
        'api': {
            'handlers': ['api'],
            'level': logging.INFO,
        },
        'debug': {
            'handlers': ['console'],
            'level': logging.DEBUG,
        },
    },
}
