from aws_mess_around.util.ec2 import launch_base_image
from aws_mess_around.util.ansible import run_playbook_on_instances_by_ids


def create_proxy_instances(c, domain, count, security_groups, tags):
    tags["service-role"] = "reverse-proxy"
    ec2_ids = launch_base_image(c, count, security_groups, tags)

    playbook = "aws_mess_around/playbooks/proxy/build_proxy.yml"

    env = {}
    run_playbook_on_instances_by_ids(c,
                                     playbook,
                                     ec2_ids,
                                     env)

    return ec2_ids


def set_app_servers_for_proxies_by_id(c, proxy_id, app_server_ids):
    pass
