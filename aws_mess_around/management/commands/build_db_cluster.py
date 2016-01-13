from aws_mess_around.util.aws import get_context
from aws_mess_around.util.db import create_db_instance
from aws_mess_around.util.db import add_slave_to_master_by_ids
from aws_mess_around.management.commands import take_down_ec2
from django.core.management.base import BaseCommand
from django.conf import settings


MASTER_SERVER_ID = 200
SLAVE1_SERVER_ID = 201
SLAVE2_SERVER_ID = 202

class Command(BaseCommand):
    help = "Makes a 3 node mysql cluster w/ statement level replication"

    def handle(self, *args, **kwargs):
        c = get_context()
        take_down_ec2(c)

        tags = {"project": "aws-initial-testing",
                "service-level": "messing-around",
                }

        my_security_group = settings.AWS_SECURITY_GROUP_NAME

        # Create a master db...
        print "Bringing up master..."
        instance_id, pwd = create_db_instance(c, [my_security_group], tags,
                                              MASTER_SERVER_ID)
        master_pwd = pwd
        master_id = instance_id

        # Create 2 slave dbs...
        print "Bringing up slave #1..."
        instance_id, pwd = create_db_instance(c, [my_security_group], tags,
                                              SLAVE1_SERVER_ID)
        s1_pwd = pwd
        s1_id = instance_id

        print "Bringing up slave #2..."
        instance_id, pwd = create_db_instance(c, [my_security_group], tags,
                                              SLAVE2_SERVER_ID)
        s2_pwd = pwd
        s2_id = instance_id

        print master_id, master_pwd
        print s1_id, s1_pwd
        print s2_id, s2_pwd

        # Connect the slavces to the master
        add_slave_to_master_by_ids(c, master_id, master_pwd, s1_id, s1_pwd)
        add_slave_to_master_by_ids(c, master_id, master_pwd, s2_id, s2_pwd)

