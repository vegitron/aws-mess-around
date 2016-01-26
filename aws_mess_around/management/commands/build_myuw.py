from aws_mess_around.util.aws import get_context
from aws_mess_around.util.db import create_new_db_cluster, generate_password
from aws_mess_around.util.db import add_database_to_host_id
from aws_mess_around.util.db import add_user_to_database
from aws_mess_around.models import BuildData
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = ("Builds an AMI for the master branch of MyUW.  Brings up DB "
            "servers, if needed, brings up a reverse proxy, if needed. "
            "Registers a DNS name, if needed.  Does shibboleth registration, "
            " guess what - if needed.  Then brings up new EC2 instances, "
            " swaps the reverse proxy config, and takes down any old EC2 "
            "instances")

    def handle(self, *args, **kwargs):
        c = get_context()
        db_settings = get_database_config_for_project(c,
                                                      "myuw",
                                                      "aws_mess_around")
        print "DB settings: ", db_settings


def get_database_config_for_project(c, project, use):
    existing_data = BuildData.objects.filter(project="myuw",
                                             use="aws_mess_around")

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

        session = c["session"]
        region_name = c["region_name"]

        ec2_client = session.client('ec2')
        ec2_region = session.resource('ec2', region_name=region_name)

        instance = ec2_region.Instance(data["master"]["id"])

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
