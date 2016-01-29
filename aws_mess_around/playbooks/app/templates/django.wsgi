import os
import sys
import site

sys.path.append('/data/app/{{ build_number }}/')

site.addsitedir('/data/app/{{ build_number }}/lib/{{ python_interpreter|default("python2.7") }}/site-packages/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
