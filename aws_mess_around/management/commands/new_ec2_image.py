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
from aws_mess_around.util.ec2 import launch_base_image, launch_ami
from aws_mess_around.util.ec2 import create_ami_from_instance
from aws_mess_around.util.ansible import run_playbook_on_instances_by_ids
from aws_mess_around.util.r53 import set_v4_ips_for_domain

# A test run of this took 7 minutes, 14 seconds.  And Apache wasn't yet running
# on the 2 final hosts.


MY_AMI_NAME = getattr(settings, "AWS_CUSTOM_AMI_NAME", "pmichaud test image")
NEW_DOMAIN_NAME = "ami-test3.aca-aws.s.uw.edu."


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

    # Launch a vanilla amazon linux ami

    tags = {"project": "aws-initial-testing",
            "service-level": "messing-around"}
    ec2_ids = launch_base_image(c, 1, [my_security_group], tags)

    print "New ID: ", ec2_ids

    new_id = ec2_ids[0]

    new_ami_id = None

    extra_env = {"ANSIBLE_SERVICE_DOMAIN": NEW_DOMAIN_NAME}
    run_playbook_on_instances_by_ids(c,
                                     "aws_mess_around/playbooks/basics.yml",
                                     [new_id],
                                     extra_env)

    new_ami_id = create_ami_from_instance(c, new_id, MY_AMI_NAME, tags)
    print "New ami id: ", new_ami_id

    new_ids = launch_ami(c, new_ami_id, 2, [my_security_group], tags)

    public_ips = []
    for new_id in new_ids:
        instance = ec2_region.Instance(new_id)
        public_ips.append(instance.public_ip_address)

    set_v4_ips_for_domain(c, NEW_DOMAIN_NAME, public_ips)

    print "All running instances: "
    for instance in ec2_region.instances.all():
        instance_id = instance.id
        print "ID: ", instance_id
        print instance.public_dns_name
        print instance.key_name
