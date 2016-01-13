import os
import time
from django.conf import settings
import subprocess


def run_playbook_on_instances_by_ids(c, playbook, instance_ids, env={}):
    ansible_cmd = "ansible-playbook -i '%s,' -u  ubuntu %s -vvvvvv"

    ansible_files_path = getattr(settings, "AWS_DEPLOY_ANSIBLE_FILES_PATH",
                                 "~/ansible/aca-aws-files")
    insecure_env = dict(os.environ,
                        ANSIBLE_HOST_KEY_CHECKING='False',
                        ANSIBLE_FILES=ansible_files_path,
                        )

    # This is a not-awesome method of passing values down into ansible.
    for key in env:
        insecure_env[key] = env[key]

    new_id_map = {}
    for id in instance_ids:
        new_id_map[id] = True

    session = c["session"]
    region_name = c["region_name"]
    ec2_region = session.resource('ec2', region_name=region_name)

    for instance in ec2_region.instances.all():
        instance_id = instance.id

        if new_id_map.get(instance_id, False):
            print "ID: ", instance_id
            print "Instance: ", instance
            print instance.public_dns_name
            print instance.key_name

            # Boto reported the instance is up before we can ssh in.  This
            # tends to take ~10 tries.  So almost a minute after "Running"
            wait_for_ssh(instance)

            # Use ansible to configure the host.  In this case. just installing
            # apache, getting it to run on boot, and changing the index page.
            cmd = ansible_cmd % (instance.public_dns_name, playbook)
            try:
                output = subprocess.check_output(cmd,
                                                 shell=True,
                                                 stderr=subprocess.PIPE,
                                                 env=insecure_env,
                                                 )
                print "O: ", output
            except subprocess.CalledProcessError as exc:
                print "Failed: ", exc.output.replace("\\n", "\n")


def wait_for_ssh(ec2_instance):
    """
    Tries to ssh in to a host.  Loops until success.
    """
    ssh_test_cmd = ("ssh -o UserKnownHostsFile=/dev/null -o "
                    "StrictHostKeyChecking=no ubuntu@%s -C 'ls /'")

    counter = 0
    while True:
        counter += 1
        time.sleep(5)
        c1 = ssh_test_cmd % ec2_instance.public_dns_name
        try:
            output = subprocess.check_output(c1, shell=True)
            break
        except subprocess.CalledProcessError as ex:
            print ex.output

    print "Took %s tries: " % counter
