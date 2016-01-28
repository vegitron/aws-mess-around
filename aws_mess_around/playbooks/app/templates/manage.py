#!/usr/bin/env python
import os
import sys
import site

sys.path.append('/data/app/{{ build_number }}/')
{% for path in manage_paths|default([]) %}
sys.path.append('/data/app/{{ build_number }}/{{ path }}')
{% endfor %}

site.addsitedir('/data/app/{{ build_number }}/lib/{{ python_interpreter|default("python2.7") }}/site-packages/')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
