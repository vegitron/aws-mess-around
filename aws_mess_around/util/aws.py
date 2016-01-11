from django.conf import settings
from boto3.session import Session


def get_context():
    """
    A structure that holds objects needed for AWS connections.

    contains:
        session - boto3.session.Session. use this to get clients and resources,
                  e.g. session.client('ec2')
                  session.resource('ec2', region_name=region_name)
        region_name - string.  e.g. us-west-2
        ssh_key_name - string.  Name of the ssh key that should be given access
                       to new EC2 instances.
    """
    c = {}

    region_name = getattr(settings, 'AWS_REGION_NAME', 'us-west-2')

    # Use Session, so we control aws access through django settings
    session = Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.AWS_ACCESS_KEY_SECRET,
                      region_name=region_name)

    c["session"] = session
    c["region_name"] = region_name
    c["ssh_key_name"] = settings.AWS_KEY_NAME

    return c
