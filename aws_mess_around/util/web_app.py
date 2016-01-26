from django.conf import settings
from aws_mess_around.util.ec2 import launch_base_image, launch_ami
from aws_mess_around.util.ec2 import create_ami_from_instance
from aws_mess_around.util.ansible import run_playbook_on_instances_by_ids

MY_AMI_NAME = getattr(settings, "AWS_CUSTOM_AMI_NAME", "pmichaud test image")


def create_webapp_instances(c, count, domain, security_groups, tags):
    tags["Role"] = "app-server"

    # Launch a vanilla amazon linux ami
    ec2_ids = launch_base_image(c, 1, security_groups, tags)

    print "New ID: ", ec2_ids

    new_id = ec2_ids[0]

    new_ami_id = None

    # Turn the EC2 instance into a viable app host
    extra_env = {"ANSIBLE_SERVICE_DOMAIN": domain}
    run_playbook_on_instances_by_ids(c,
                                     "aws_mess_around/playbooks/basics.yml",
                                     [new_id],
                                     extra_env)

    # XXX - this should be named based on the project/what-not!
    new_ami_id = create_ami_from_instance(c, new_id, MY_AMI_NAME, tags)

    # Launch webapp instances from the new ami we created.
    new_ids = launch_ami(c, new_ami_id, count, security_groups, tags)

    return new_ids
