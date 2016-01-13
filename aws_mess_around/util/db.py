import string
import random
from aws_mess_around.util.ec2 import launch_base_image
from aws_mess_around.util.ansible import run_playbook_on_instances_by_ids


def create_db_instance(c, security_groups, tags, server_id):
    tags["service-role"] = "database"
    ec2_ids = launch_base_image(c, 1, security_groups, tags)
    print "IDs: ", ec2_ids
    playbook = "aws_mess_around/playbooks/db/build_database.yml"

    password = generate_password()
    print "Setting root password: ", password

    env = {"ANSIBLE_MYSQL_ROOT": password,
           "ANSIBLE_MYSQL_SERVER_ID": "%s" % server_id}

    run_playbook_on_instances_by_ids(c,
                                     playbook,
                                     ec2_ids,
                                     env)

    return ec2_ids[0], password

def add_slave_to_master_by_ids(c, master_id, master_pwd, slave_id, slave_pwd):
    """
    Add the mysql host at host slave_id as a replication slave to the mysql
    host at host master_id.

    Username for both is assumed to be root.

    This *only* works for initial setup.
    """
    session = c["session"]
    region_name = c["region_name"]
    ec2_client = session.client("ec2")
    ec2_region = session.resource('ec2', region_name=region_name)

    master = ec2_region.Instance(master_id)
    print master.private_ip_address

    slave = ec2_region.Instance(slave_id)
    print slave.private_ip_address

    repl_pwd = generate_password(10)

    print "Replication password: ", repl_pwd

    env = {"ANSIBLE_MYSQL_MASTER_PASSWORD": master_pwd,
           "ANSIBLE_MYSQL_REPL_PASSWORD": repl_pwd,
           "ANSIBLE_MYSQL_SLAVE_IP": slave.private_ip_address,
           }

    # Grant access to the slave...
    master_playbook = "aws_mess_around/playbooks/db/add_slave_access.yml"

    run_playbook_on_instances_by_ids(c,
                                     master_playbook,
                                     [master_id],
                                     env)

    env = {"ANSIBLE_MYSQL_SLAVE_PASSWORD": slave_pwd,
           "ANSIBLE_MYSQL_REPL_PASSWORD": repl_pwd,
           "ANSIBLE_MYSQL_MASTER_IP": master.private_ip_address,
           }


    # Read the master status, and connect
    slave_playbook = "aws_mess_around/playbooks/db/join_master.yml"
    run_playbook_on_instances_by_ids(c,
                                     slave_playbook,
                                     [slave_id],
                                     env)

def generate_password(length=50):
    chars = "".join([string.digits,
                     string.ascii_letters,
                     "#$%&()*+,-./:;<=>?@[]^_{|}~"])

    l = length
    password = ''.join([random.SystemRandom().choice(chars) for i in range(l)])

    return password

