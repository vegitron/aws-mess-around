from django.conf import settings


def take_down_ec2(c):
    session = c["session"]
    region_name = c["region_name"]
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
    if terminate_ids:
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=terminate_ids)
    print "Done waiting"
