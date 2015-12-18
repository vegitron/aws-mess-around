import boto3
import time
import os
from boto3.session import Session
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess

# A test run of this took 7 minutes, 14 seconds.  And Apache wasn't yet running
# on the 2 final hosts.


MY_AMI_NAME = getattr(settings, "AWS_CUSTOM_AMI_NAME", "pmichaud test image")
UBUNTU_LTS = 'ami-e54f5f84'
ansible_files_path = getattr(settings, "AWS_DEPLOY_ANSIBLE_FILES_PATH",
                             "~/ansible/aca-aws-files")
NEW_DOMAIN_NAME = "ami-test3.aca-aws.s.uw.edu"

TESTING_ACCESS = [
    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
     "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 80,
     "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 443,
     "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
]


class Command(BaseCommand):
    help = "Make a new ec2 ami based on an existing one"

    def handle(self, *args, **kwargs):
        region_name = getattr(settings, 'AWS_REGION_NAME', 'us-west-2')

        # Use Session, so we control aws access through django settings
        session = Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_ACCESS_KEY_SECRET,
                          region_name=region_name)

        try:
            launch_ec2(session, region_name)
        except Exception as ex:
            print ex
            print "Failed to launch"
        take_down_ec2(session, region_name)


def launch_ec2(session, region_name):
    ec2_client = session.client('ec2')
    ec2_region = session.resource('ec2', region_name=region_name)

    my_security_group = settings.AWS_SECURITY_GROUP_NAME
    security_groups = ec2_client.describe_security_groups()
    my_group = None

    # Build, or rebuild my testing security group.
    for group in security_groups["SecurityGroups"]:
        name = group["GroupName"]
        if name == my_security_group:
            ec2_client.delete_security_group(GroupName=my_security_group)

    gname = my_security_group
    desc = "Security group for testing"
    my_group = ec2_client.create_security_group(GroupName=gname,
                                                Description=desc)

    ec2_client.authorize_security_group_ingress(GroupName=gname,
                                                IpPermissions=TESTING_ACCESS)

    # Launch a vanilla amazon linux ami
    response = ec2_client.run_instances(ImageId=UBUNTU_LTS,
                                        MinCount=1,
                                        KeyName=settings.AWS_KEY_NAME,
                                        MaxCount=1,
                                        SecurityGroups=[my_security_group],
                                        )

    ids = []
    new_id = None
    for instance in response["Instances"]:
        new_id = instance["InstanceId"]
        i_obj = ec2_region.Instance(new_id)
        i_obj.create_tags(Tags=[{'Key': 'project',
                                 'Value': 'aws-initial-testing',
                                 },
                                {'Key': 'service-level',
                                 'Value': 'messing-around',
                                 }])
        ids.append(new_id)

    # Wait for it to be running...
    print "Waiting for run...", ids
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=ids)
    print "Done waiting"

    ansible_cmd = ("ansible-playbook -i '%s,' -u  ubuntu "
                   "aws_mess_around/playbooks/basics.yml -vvvvv")
    ssh_test_cmd = ("ssh -o UserKnownHostsFile=/dev/null -o "
                    "StrictHostKeyChecking=no ubuntu@%s -C 'ls /'")

    insecure_env = dict(os.environ,
                        ANSIBLE_HOST_KEY_CHECKING='False',
                        ANSIBLE_FILES=ansible_files_path,
                        ANSIBLE_SERVICE_DOMAIN=NEW_DOMAIN_NAME)

    new_ami_id = None
    for instance in ec2_region.instances.all():
        instance_id = instance.id

        if instance_id == new_id:
            print "ID: ", instance_id
            print instance.public_dns_name
            print instance.key_name

            # Boto reported the instance is up before we can ssh in.  This
            # tends to take ~10 tries.  So almost a minute after "Running"
            print "Sleeping, waiting for ssh"
            counter = 0
            while True:
                counter += 1
                time.sleep(5)
                print "Giving it a try"
                c1 = ssh_test_cmd % instance.public_dns_name
                try:
                    output = subprocess.check_output(c1,
                                                     shell=True,
                                                     env=insecure_env,
                                                     )
                    print "O: ", output
                    break
                except subprocess.CalledProcessError as ex:
                    print ex.output

            print "Took %s tries: " % counter

            # Use ansible to configure the host.  In this case. just installing
            # apache, getting it to run on boot, and changing the index page.
            cmd = ansible_cmd % instance.public_dns_name
            print "Running command: ", cmd
            try:
                output = subprocess.check_output(cmd,
                                                 shell=True,
                                                 env=insecure_env,
                                                 )
            except subprocess.CalledProcessError as ex:
                print ex.output
                return
            print "O: ", output

            print "CMD: ", cmd
            return

            print "Stopping the existing instance, to image it"
            ec2_client.stop_instances(InstanceIds=[new_id])
            waiter = ec2_client.get_waiter("instance_stopped")
            waiter.wait(InstanceIds=[new_id])

            print "Done waiting.  Building an image"

            # Remove any ami that already exists with our name.
            try:
                name_filter = [{'Name': 'name',
                                'Values': [MY_AMI_NAME]}]

                images = ec2_client.describe_images(Filters=name_filter)
                image_id = images["Images"][0]["ImageId"]
                ec2_client.deregister_image(ImageId=image_id)
            except Exception as ex:
                print "Error deregistring ami: ", ex

            image = instance.create_image(Name=MY_AMI_NAME)
            new_ami_id = image.id
            ami = ec2_region.Image(new_ami_id)
            ami.create_tags(Tags=[{'Key': 'project',
                                   'Value': 'aws-initial-testing',
                                   },
                                  {'Key': 'service-level',
                                   'Value': 'messing-around',
                                   }])

            print "I (waiting...): ", image
            waiter = ec2_client.get_waiter('image_available')
            waiter.wait(ImageIds=[new_ami_id])

            print "Done waiting for image"

    print "Launching 2 new instances with our AMI"
    response = ec2_client.run_instances(ImageId=new_ami_id,
                                        MinCount=2,
                                        KeyName=settings.AWS_KEY_NAME,
                                        MaxCount=2,
                                        SecurityGroups=[my_security_group],
                                        )

    fresh_ami_instance_ids = []
    for instance in response["Instances"]:
        new_id = instance["InstanceId"]
        i_obj = ec2_region.Instance(new_id)
        i_obj.create_tags(Tags=[{'Key': 'project',
                                 'Value': 'aws-initial-testing',
                                 },
                                {'Key': 'service-level',
                                 'Value': 'messing-around',
                                 }])

        fresh_ami_instance_ids.append(new_id)

    print "Waiting for run...", ids
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=fresh_ami_instance_ids)
    print "Done waiting"

    print "All running instances: "
    for instance in ec2_region.instances.all():
        instance_id = instance.id
        print "ID: ", instance_id
        print instance.public_dns_name
        print instance.key_name


def take_down_ec2(session, region_name):
    print('My region:')
    my_security_group = settings.AWS_SECURITY_GROUP_NAME
    ec2_region = session.resource('ec2', region_name=region_name)
    ec2_client = session.client('ec2')
    terminate_ids = []
    for instance in ec2_region.instances.all():
        print(instance.id)
        print instance.security_groups
        for group in instance.security_groups:
            name = group["GroupName"]
            if name == my_security_group:
                terminate_ids.append(instance.id)
                ec2_client.terminate_instances(InstanceIds=[instance.id])

    print "Waiting for termination...", terminate_ids
    waiter = ec2_client.get_waiter('instance_terminated')
    waiter.wait(InstanceIds=terminate_ids)
    print "Done waiting"
