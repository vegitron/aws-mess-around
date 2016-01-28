from django.conf.urls import patterns, include, url
{% if extra_urls_head_section|default(None) %}
{% include extra_urls_head_section %}
{% endif %}

urlpatterns = patterns('',
    {% for definition in project_url_definitions %}
    {{ definition }},
    {% endfor %}
)
