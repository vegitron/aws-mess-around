#!/usr/bin/env python

from distutils.core import setup
import setuptools

setup(name='AWS-Mess-Around',
      version='1.0.4',
      license = "Apache 2.0",
      author = "UW-IT ACA",
      author_email = "pmichaud@uw.edu",
      packages=setuptools.find_packages(exclude=["project"]),
      include_package_data=True,  # use MANIFEST.in during install
      url='https://github.com/vegitron/aws-mess-around',
      description='Test scripts.  Maybe stuff that could hit production',
      install_requires=['boto3', 'Django==1.8',],
     )
