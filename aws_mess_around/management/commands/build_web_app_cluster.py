import boto3
import time
import os
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
from aws_mess_around.management.commands import take_down_ec2
from aws_mess_around.util.aws import get_context
from aws_mess_around.util.vpc import manage_vpcs
from aws_mess_around.util.ec2 import manage_web_security_group
from aws_mess_around.util.web_app import create_webapp_instances
from aws_mess_around.util.r53 import set_v4_ips_for_domain
from aws_mess_around.util.proxy import create_proxy_instances
from aws_mess_around.util.proxy import set_app_servers_for_proxies_by_id

# A test run of this took 7 minutes, 14 seconds.  And Apache wasn't yet running
# on the 2 final hosts.


NEW_DOMAIN_NAME = getattr(settings, "AWS_NEW_DOMAIN_NAME",
                          "ami-test6.aca-aws.s.uw.edu")


class Command(BaseCommand):
    help = "Make a new ec2 ami based on an existing one"

    def handle(self, *args, **kwargs):
        c = get_context()
        region_name = getattr(settings, 'AWS_REGION_NAME', 'us-west-2')

        take_down_ec2(c)
        try:
            manage_vpcs(c)
            launch_ec2(c)
        except Exception as ex:
            print ex
            print "Failed to launch"
            raise


def launch_ec2(c):
    session = c["session"]
    region_name = c["region_name"]

    ec2_client = session.client('ec2')
    ec2_region = session.resource('ec2', region_name=region_name)

    my_security_group = settings.AWS_SECURITY_GROUP_NAME
    try:
        manage_web_security_group(c, my_security_group)
    except Exception as ex:
        print "Error managing security group: ", ex

    tags = {"Project": "aws-initial-testing",
            "Use": "messing-around",
            "ResponsibleParty": settings.AWS_RESPONSIBLE_PARTY}

    instance_ids = create_webapp_instances(c, 2, NEW_DOMAIN_NAME,
                                           [my_security_group], tags)

    proxy_ids = create_proxy_instances(c, NEW_DOMAIN_NAME, 1,
                                       [my_security_group], tags)

    set_app_servers_for_proxies_by_id(c, NEW_DOMAIN_NAME, proxy_ids,
                                      instance_ids)

    public_ips = []
    for new_id in proxy_ids:
        instance = ec2_region.Instance(new_id)
        public_ips.append(instance.public_ip_address)

    set_v4_ips_for_domain(c, NEW_DOMAIN_NAME, public_ips)

    print "All running instances: "
    for instance in ec2_region.instances.all():
        instance_id = instance.id
        print "ID: ", instance_id
        print instance.public_dns_name
        print instance.key_name
