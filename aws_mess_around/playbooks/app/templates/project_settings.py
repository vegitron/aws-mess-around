DEBUG = {{ debug|default(False) }}
TEMPLATE_DEBUG = DEBUG

{% if not skip_compress_statics|default(False) %}
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_ROOT = '/data/statics/{{ build_number}}'

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)
{% endif %}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
{% for admin in admins|default([]) %}
    ('{{ admin.name }}', '{{ admin.email }}'),
{% endfor %}
)

MANAGERS = ADMINS

{% if not skip_central_db_config|default(False) %}
DATABASES = {
    'default': {
        'ENGINE': '{{ database_backend|default("django.db.backends.mysql") }}',
        'NAME': '{{ database_name }}',
        'USER': '{{ database_user }}',
        'PASSWORD': '{{ database_password|default("") }}',
        'HOST': '{{ database_host }}',
        'PORT': '{{ database_port|default("") }}',
    }
}
{% endif %}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# # See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = (
{% for host in allowed_hosts|default([]) %}
    '{{ host }}',
{% endfor %}
)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/data/statics/{{ build_number }}'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
{% if aca_cdn_path | default(false) %}
STATIC_URL = 'https://aca-cdn.uw.edu/cdn/{{ aca_cdn_path }}/{{ current_build_value }}/'
{% else %}
STATIC_URL = '/statics/{{ build_number }}/'
{% endif %}

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static"
    # Don't forget to use absolute paths, not relative paths.
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    {% if not skip_compress_statics|default(False) %}'compressor.finders.CompressorFinder',{% endif %}
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '{{ secret_key }}'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    {% if include_userservice|default(True) %}'userservice.user.UserServiceMiddleware',{% endif %}
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    '{{ authentication_backend|default('django.contrib.auth.backends.RemoteUserBackend')}}',
)

ROOT_URLCONF = 'project.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'project.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    {% if not skip_compress_statics|default(False) %}'compressor',{% endif %}
    'null_command',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

{% for key, value in restclients|default({})|dictsort %}
{% for client in value %}

{% include "templates/restclients/%s.tmpl"|format(client) %}

{% endfor %}
{% endfor %}

{% if project_settings_template|default(None) %}
{% include project_settings_template %}
{% endif %}
