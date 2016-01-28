AWS Mess Around
===============

This is a repository for scripts that will eventually become the ACA AWS management app.  It follows a normal aca django install process, but you'll also need to have an ansible environment configured.

You'll need some configuration in your settings:

  * AWS_ACCESS_KEY_ID
  * AWS_ACCESS_KEY_SECRET

Get those settings by creating a user for yourself: https://console.aws.amazon.com/iam/home?region=us-west-2#users

  AWS_SECURITY_GROUP_NAME

This will probably be deprecated/replaced soon, but it should be something like { your netid }_testing_security_group.

  AWS_KEY_NAME

This is the name of your ssh key, as managed at https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=us-west-2#KeyPairs:sort=keyName

  AWS_FILES_PATH

This is a path on your local machine that has host-specific data, like x509 certs.
