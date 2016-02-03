from aws_mess_around.util.aws import get_context
from aws_mess_around.util.db import create_new_db_cluster
from aws_mess_around.management.commands import take_down_ec2
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Makes a 3 node mysql cluster w/ statement level replication"

    def handle(self, *args, **kwargs):
        c = get_context()
        take_down_ec2(c)

        tags = {"Project": "aws-initial-testing",
                "Use": "messing-around",
                "ResponsibleParty": settings.AWS_RESPONSIBLE_PARTY,
                }

        my_security_group = settings.AWS_SECURITY_GROUP_NAME

        print create_new_db_cluster(c, [my_security_group], tags)
