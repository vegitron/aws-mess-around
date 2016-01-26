import os
import time
import json
import random
from django.conf import settings
import subprocess


def run_playbook_on_instances_by_ids(c, playbook, instance_ids, env={},
                                     data=None):

    data_path = None
    ansible_cmd = "ansible-playbook -i '%s,' -u  ubuntu %s"
    if data:
        tmp_path = getattr(settings, "TEMP_PATH", "/tmp/")

        # This is somewhat overboard, but i want to make sure we don't have
        # collisions, or a guessable path to inject data
        extra = ''.join([random.choice("0123456789") for i in range(20)])
        file_name = "ansible_vars-%s" % (extra)
        data_path = os.path.join(tmp_path, file_name)

        f = open(data_path, "w")
        f.write(json.dumps(data))
        f.close()

        ansible_cmd += " --extra-vars @%s" % data_path

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

    if data_path:
        os.unlink(data_path)


def wait_for_ssh(ec2_instance):
    """
    Tries to ssh in to a host.  Loops until success.
    """
    ssh_test_cmd = ("ssh -o UserKnownHostsFile=/dev/null -o "
                    "StrictHostKeyChecking=no ubuntu@%s -C 'ls /'")

    counter = 0
    while True:
        counter += 1
        c1 = ssh_test_cmd % ec2_instance.public_dns_name
        try:
            output = subprocess.check_output(c1, shell=True)
            break
        except subprocess.CalledProcessError as ex:
            print ex.output

        time.sleep(5)
    print "Took %s tries: " % counter
