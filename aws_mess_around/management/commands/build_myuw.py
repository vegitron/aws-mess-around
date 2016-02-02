from aws_mess_around.management.commands import take_down_ec2
from aws_mess_around.util.aws import get_context
from aws_mess_around.util.web_app import create_webapp_instances
from aws_mess_around.util.web_app import get_next_build_for_project
from aws_mess_around.util.db import create_new_db_cluster, generate_password
from aws_mess_around.util.db import add_database_to_host_id
from aws_mess_around.util.db import add_user_to_database
from aws_mess_around.util.ansible import run_playbook_on_instances_by_ids
from aws_mess_around.util.proxy import create_proxy_instances
from aws_mess_around.util.proxy import set_app_servers_for_proxies_by_id
from aws_mess_around.util.r53 import set_v4_ips_for_domain
from aws_mess_around.util.shib import register_sp
from aws_mess_around.models import BuildData
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.crypto import get_random_string

DEMO_DOMAIN = settings.AWS_DEMO_MYUW_DOMAIN


class Command(BaseCommand):
    help = ("Builds an AMI for the master branch of MyUW.  Brings up DB "
            "servers, if needed, brings up a reverse proxy, if needed. "
            "Registers a DNS name, if needed.  Does shibboleth registration, "
            " guess what - if needed.  Then brings up new EC2 instances, "
            " swaps the reverse proxy config, and takes down any old EC2 "
            "instances")

    def handle(self, *args, **kwargs):
        c = get_context()
        if False:
            cleanup_all(c)

        # Find or create a DB cluster to use.
        db_settings = get_database_config_for_project(c,
                                                      "myuw",
                                                      "aws_mess_around")
        print "DB settings: ", db_settings

        # Find or create the proxies the app servers will live behind.
        proxy_settings = get_proxy_config_for_project(c,
                                                      "myuw",
                                                      "aws_mess_around")

        print "Proxy settings: ", proxy_settings

        # Get a base image to do build a MyUW AMI off of
        my_security_group = settings.AWS_SECURITY_GROUP_NAME
        tags = {"Project": "myuw",
                "Use": "messing-around"}

        # instance_ids = create_webapp_instances(c, 1, DEMO_DOMAIN,
        #                                        [my_security_group], tags)

        # instance_id = instance_ids[0]
        instance_id = 'i-d7d3370f'

        print "Our base instance ID: ", instance_id

        # Get the host ready to be a MyUW app server
        playbook = "aws_mess_around/playbooks/app/prep_host.yml"

        urls = ["url(r'^support', include('userservice.urls'))",
                "url(r'^restclients/', include('restclients.urls'))",
                "url(r'^logging/', include('django_client_logger.urls'))",
                "url(r'^', include('myuw.urls'))"
                ]

        # XXX - this should change when the memcached work is implemented.
        cache = "myuw.util.cache_implementation.MyUWCache"
        secret_key = get_secret_key_for_project("myuw", "aws_mess_around")
        extra_settings = "templates/myuw/project_settings.py"
        data = {"files_dir": settings.AWS_FILES_PATH,
                "file_group": "ubuntu",
                "webservice_client_cert_name": "myuw-uwca.cert",
                "webservice_client_key_name": "myuw-uwca.key",
                # "build_number": get_next_build_for_project("myuw"),
                "build_number": 8,
                "git_repository": "https://github.com/uw-it-aca/myuw.git",
                "git_version": "feature/aws-shibboleth",
                "pip_requirements_files": ["requirements.txt"],
                "project_url_definitions": urls,
                "database_name": "myuw",
                "database_user": db_settings["username"],
                "database_password": db_settings["password"],
                "database_host": db_settings["host"],
                "allowed_hosts": [DEMO_DOMAIN],
                "secret_key": secret_key,
                "digitlib_client_redirect": False,
                "userservice_admin_group": "u_pmichaud_myuwdevtesters",
                "restclients_admin_group": "u_pmichaud_myuwdevtesters",
                "restclients_dao_cache_class": cache,
                "project_settings_template": extra_settings,
                "migrate_apps": ["myuw"],
                "shib_required_url": "/",
                "restclients": {"test": [],
                                "production": ["gws", "sws", "pws", "hfs",
                                               "book", "uwnetid",
                                               "canvas",
                                               "libraries", "trumba_calendar",
                                               "digit_lib",
                                               "iasystem",
                                               "grad"],
                                },

                }
        run_playbook_on_instances_by_ids(c,
                                         playbook,
                                         [instance_id],
                                         data=data,
                                         vars_file="aws/myuw/production.json")

        # Add our instances to the proxy
        proxy_ids = [proxy_settings["instance_id"]]
        # set_app_servers_for_proxies_by_id(c, DEMO_DOMAIN, proxy_ids,
        #                                   [instance_id])

        instance = get_instance(c, instance_id)

        print "IP: ", instance.public_ip_address

        # register_sp(DEMO_DOMAIN)


def cleanup_all(c):
    BuildData.objects.all().delete()
    take_down_ec2(c)


def get_proxy_config_for_project(c, project, use):
    existing_data = BuildData.objects.filter(project="myuw",
                                             use="aws_mess_around")

    proxy_instance_id = None
    for data in existing_data:
        if "proxy" == data.role and "instance_id" == data.data_field:
            proxy_instance_id = data.value

    if not proxy_instance_id:
        tags = {"Project": "myuw",
                "Use": "messing-around"}

        my_security_group = settings.AWS_SECURITY_GROUP_NAME
        new_ids = create_proxy_instances(c, DEMO_DOMAIN, 1,
                                         [my_security_group], tags)

        instance = get_instance(c, new_ids[0])
        ip = instance.public_ip_address
        set_v4_ips_for_domain(c, DEMO_DOMAIN, [ip])

        BuildData.objects.get_or_create(project="myuw", use="aws_mess_around",
                                        role="proxy", data_field="instance_id",
                                        defaults={"value": new_ids[0]})

        proxy_instance_id = new_ids[0]

    return {"instance_id": proxy_instance_id}


def get_secret_key_for_project(project, use):
    existing_data = BuildData.objects.filter(project=project,
                                             use=use,
                                             role="app",
                                             data_field="secret_key")

    if existing_data:
        return existing_data[0].value

    # From https://github.com/django/django/blob/master/
    #        django/core/management/commands/startproject.py
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    secret_key = get_random_string(50, chars)

    BuildData.objects.get_or_create(project=project, use=use,
                                    role="app", data_field="secret_key",
                                    defaults={"value": secret_key})

    return secret_key


def get_database_config_for_project(c, project, use):
    existing_data = BuildData.objects.filter(project=project,
                                             use=use)

    db_host = db_user = db_pass = None

    for data in existing_data:
        if "database" == data.role and "hostname" == data.data_field:
            db_host = data.value

        if "database" == data.role and "username" == data.data_field:
            db_user = data.value

        if "database" == data.role and "password" == data.data_field:
            db_pass = data.value

    if not db_host or not db_user or not db_pass:
        tags = {"Project": project,
                "Use": use,
                }

        my_security_group = settings.AWS_SECURITY_GROUP_NAME

        # Create the db cluster
        data = create_new_db_cluster(c, [my_security_group], tags)

        # Create the myuw db - tables will be created later
        add_database_to_host_id(c, "myuw", data["master"]["id"],
                                data["master"]["password"])

        myuw_password = generate_password()

        # Create the user our app will use to connect to the db
        add_user_to_database(c, "myuw_user", "%", myuw_password, "myuw",
                             data["master"]["id"], data["master"]["password"])

        instance = get_instance(c, data["master"]["id"])

        ip_address = instance.private_ip_address

        BuildData.objects.get_or_create(project="myuw", use="aws_mess_around",
                                        role="database", data_field="username",
                                        defaults={"value": "myuw_user"})

        BuildData.objects.get_or_create(project="myuw", use="aws_mess_around",
                                        role="database", data_field="password",
                                        defaults={"value": myuw_password})

        BuildData.objects.get_or_create(project="myuw", use="aws_mess_around",
                                        role="database", data_field="hostname",
                                        defaults={"value": ip_address})

        db_host = ip_address
        db_user = "myuw"
        db_pass = myuw_password

    return {"host": db_host, "username": db_user, "password": db_pass}


def get_instance(c, iid):
    session = c["session"]
    region_name = c["region_name"]

    ec2_client = session.client('ec2')
    ec2_region = session.resource('ec2', region_name=region_name)

    instance = ec2_region.Instance(iid)

    return instance
