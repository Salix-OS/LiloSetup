#!/usr/bin/env python

"""
Global variables

"""

# Monitor if a label is already in use
already_there = []
# Ensure at least one  partition has been configured
partition_set = []
# List of the temporary mountpoints that will need to be cleanly unmounted
temp_mount = []
# List of the temporary directories that will need to be cleanly deleted
temp_dir = []
# Key mountpoints value
temp_chroot_mnt = ''
chroot_mnt = ''
# Work directory
work_dir = "/tmp/lilosetup"
# Configuration file and its stub
configfile_location = work_dir + "/lilosetup.conf"
stub_location = work_dir + "/lilosetup.stub"
# Warning dialog default answer
response_to_warning = [None]