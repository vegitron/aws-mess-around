def manage_vpcs(c):
    """
    This method enforces our VPCs.  We have 4 that we use:
    1) Production
    2) Test
    3) Builds
    4) Default

    This needs to be updated with some actual networking rules.
    """
    session = c["session"]
    region_name = c["region_name"]
    ec2_client = session.client('ec2')
    ec2_region = session.resource('ec2', region_name=region_name)

    valid_service_levels = {"production": True,
                            "test": True,
                            "build": True
                            }

    existing_service_levels = {}
    # Get VPCs without a tag.  Delete any VPC without a tag that isn't default.
    for vpc in ec2_region.vpcs.all():
        if vpc.is_default:
            continue

        if vpc.tags is None:
            vpc.delete()

        service_level = None
        for tag in vpc.tags:
            if "service-level" == tag["Key"]:
                service_level = tag["Value"]

        # If it has tags, but doesn't have a service level, or the service
        # level isn't one of our defined service levels, remove it.
        is_valid = valid_service_levels.get(service_level, False)

        if not is_valid:
            vpc.delete()

        existing_service_levels[service_level] = True

    # Now, create any VPCs that are missing
    for level in valid_service_levels:

        if existing_service_levels.get(level, False):
            continue

        res = ec2_client.create_vpc(CidrBlock='10.0.0.0/24')
        vpc_id = res["Vpc"]["VpcId"]
        waiter = ec2_client.get_waiter('vpc_available')
        waiter.wait(VpcIds=[vpc_id])

        vpc = ec2_region.Vpc(vpc_id)
        # Tag the new VPC with the service level.
        vpc.create_tags(Tags=[{'Key': 'service-level',
                               'Value': level,
                               }])


