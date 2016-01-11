from aws_mess_around.util import get_tag_structure

UBUNTU_LTS = 'ami-e54f5f84'

WEB_ACCESS = [
    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
     "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 80,
     "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 443,
     "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
]


def manage_web_security_group(c, group_name):
    """
    Creates a security group if doesn't exist.

    XXX - if it does exist, this will delete it, and recreate it!  This should
    be changed to just manage the rules in this case.

    This security group will grant access to ports 22, 80 and 443.
    """
    session = c["session"]
    ec2_client = session.client("ec2")
    security_groups = ec2_client.describe_security_groups()
    my_group = None

    for group in security_groups["SecurityGroups"]:
        name = group["GroupName"]
        if name == group_name:
            ec2_client.delete_security_group(GroupName=group_name)

    desc = "Security group for testing"
    my_group = ec2_client.create_security_group(GroupName=group_name,
                                                Description=desc)

    ec2_client.authorize_security_group_ingress(GroupName=group_name,
                                                IpPermissions=WEB_ACCESS)


def launch_base_image(c, count, security_groups, tags):
    return launch_ami(c, UBUNTU_LTS, count, security_groups, tags)


def launch_ami(c, ami_id, count, security_groups, tags):
    """
    Launches and tags count instances of the given ami_id.  Applies
    security groups and tags.  Only returns after the instances are running.

    Does not wait for services on the host to start.
    """
    session = c["session"]
    region_name = c["region_name"]
    ec2_client = session.client("ec2")
    ec2_region = session.resource('ec2', region_name=region_name)

    response = ec2_client.run_instances(ImageId=ami_id,
                                        MinCount=count,
                                        KeyName=c["ssh_key_name"],
                                        MaxCount=count,
                                        SecurityGroups=security_groups,
                                        )

    ids = []
    new_id = None
    for instance in response["Instances"]:
        new_id = instance["InstanceId"]
        i_obj = ec2_region.Instance(new_id)
        i_obj.create_tags(Tags=get_tag_structure(tags))

        ids.append(new_id)

    # Wait for it to be running...
    waiter = ec2_client.get_waiter('instance_running')
    print "Waiting on IDs: ", ids
    waiter.wait(InstanceIds=ids)
    print "Done waiting!"

    return ids


def create_ami_from_instance(c, instance_id, ami_name, tags):
    """
    Given a running instance, this will create a new AMI.

    Note - this will stop your running instance.
    """
    session = c["session"]
    region_name = c["region_name"]
    ec2_client = session.client('ec2')
    ec2_region = session.resource('ec2', region_name=region_name)
    ec2_client.stop_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=[instance_id])

    # Remove any ami that already exists with our name.
    try:
        name_filter = [{'Name': 'name',
                        'Values': [ami_name]}]

        images = ec2_client.describe_images(Filters=name_filter)
        image_id = images["Images"][0]["ImageId"]
        print "Deregistering AMI: ", image_id
        ec2_client.deregister_image(ImageId=image_id)
    except Exception as ex:
        print "Error deregistring ami: ", ex

    instance = ec2_region.Instance(instance_id)
    image = instance.create_image(Name=ami_name)
    new_ami_id = image.id
    ami = ec2_region.Image(new_ami_id)

    tags = get_tag_structure(tags)
    ami.create_tags(Tags=tags)

    print "Waiting on AMI..."
    waiter = ec2_client.get_waiter('image_available')
    waiter.wait(ImageIds=[new_ami_id])
    print "Done"

    return new_ami_id
