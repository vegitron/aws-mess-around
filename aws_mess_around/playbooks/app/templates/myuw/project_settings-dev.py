# Settings for MyUWMobile project.
TIME_ZONE = 'America/Los_Angeles'

INSTALLED_APPS += (
    'south',
    'restclients',
    'templatetag_handlebars',
    'myuw_mobile',
    'userservice',
    'supporttools',
    'django_client_logger'
)

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'myuw_mobile': {
            'format': '%(levelname)-4s %(asctime)s %(message)s [%(name)s]',
            'datefmt': '%d %H:%M:%S',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'myuw_mobile': {
            'level': 'INFO',
            'class': 'permissions_logging.DateNameFileHandler',
            'filename': '{{ base_dir }}/logs/myuw-%Y-%m-%d',
            'permissions': 0o664,
            'formatter': 'myuw_mobile',
        },
        'card': {
            'level': 'INFO',
            'class': 'permissions_logging.DateNameFileHandler',
            'filename': '{{ base_dir }}/logs/card-%Y-%m-%d',
            'permissions': 0o664,
            'formatter': 'myuw_mobile',
        },
        'link': {
            'level': 'INFO',
            'class': 'permissions_logging.DateNameFileHandler',
            'filename': '{{ base_dir }}/logs/link-%Y-%m-%d',
            'permissions': 0o664,
            'formatter': 'myuw_mobile',
        },
        'session': {
            'level': 'INFO',
            'class': 'permissions_logging.DateNameFileHandler',
            'filename': '{{ base_dir }}/logs/session-%Y-%m-%d',
            'permissions': 0o664,
            'formatter': 'myuw_mobile',
        },
        'console':{
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'restclients': {
            'handlers': ['myuw_mobile'],
            'level': 'INFO',
            'propagate': True,
        },
        'myuw_mobile': {
            'handlers': ['myuw_mobile'],
            'level': 'INFO',
            'propagate': True,
        },
        'card': {
            'handlers': ['card'],
            'level': 'INFO',
            'propagate': True,
        },
        'link': {
            'handlers': ['link'],
            'level': 'INFO',
            'propagate': True,
        },
        'session': {
            'handlers': ['session'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}


USERSERVICE_VALIDATION_MODULE = "myuw_mobile.userservice_validation.validate"
USERSERVICE_ADMIN_GROUP='{{ userservice_admin_group }}'
RESTCLIENTS_ADMIN_GROUP='{{ restclients_admin_group }}'
RESTCLIENTS_DAO_CACHE_CLASS='{{restclients_dao_cache_class}}'
AUTHZ_GROUP_BACKEND = 'authz_group.authz_implementation.uw_group_service.UWGroupService'

SUPPORTTOOLS_PARENT_APP = "MyUW"
SUPPORTTOOLS_PARENT_APP_URL = "/mobile/landing/"

TEMPLATE_CONTEXT_PROCESSORS = (
'django.contrib.auth.context_processors.auth',
'django.core.context_processors.debug',
'django.core.context_processors.i18n',
'django.core.context_processors.media',
'django.core.context_processors.static',
'django.core.context_processors.tz',
'django.contrib.messages.context_processors.messages',
'django.core.context_processors.request',
'myuw_mobile.context_processors.has_less_compiled',
'myuw_mobile.context_processors.has_google_analytics',
'supporttools.context_processors.supportools_globals',
)

from django_mobileesp.detector import agent

MIDDLEWARE_CLASSES += (
    'django_mobileesp.middleware.UserAgentDetectionMiddleware',
)

DETECT_USER_AGENTS = {
    'is_tablet': agent.detectTierTablet,
    'is_mobile': agent.detectMobileQuick,
}

GOOGLE_ANALYTICS_KEY = "{{ ga_tracker_key }}"

