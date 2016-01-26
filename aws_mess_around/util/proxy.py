from django.conf import settings
from aws_mess_around.util.ec2 import launch_base_image
from aws_mess_around.util.ansible import run_playbook_on_instances_by_ids


def create_proxy_instances(c, domain, count, security_groups, tags):
    tags["Role"] = "reverse-proxy"
    ec2_ids = launch_base_image(c, count, security_groups, tags)

    playbook = "aws_mess_around/playbooks/proxy/build_proxy.yml"

    run_playbook_on_instances_by_ids(c,
                                     playbook,
                                     ec2_ids,
                                     )

    set_app_servers_for_proxies_by_id(c, domain, ec2_ids, [])
    return ec2_ids


def set_app_servers_for_proxies_by_id(c, domain, proxy_ids, app_server_ids):
    session = c["session"]
    region_name = c["region_name"]

    ec2_client = session.client('ec2')
    ec2_region = session.resource('ec2', region_name=region_name)

    # XXX - make this configurable per service, at least
    url = "http://depts.washington.edu/sacg/news/static/catalyst_offline.html"
    data = {"app_servers": [], "domain": domain, "emergency_offline_url": url}

    for iid in app_server_ids:
        instance = ec2_region.Instance(iid)
        data["app_servers"].append(instance.private_ip_address)

    playbook = "aws_mess_around/playbooks/proxy/set_proxy_backends.yml"

    env = {}
    run_playbook_on_instances_by_ids(c,
                                     playbook,
                                     proxy_ids,
                                     data=data)
