#!/usr/bin/env python

"""
Functions cleaning up LiloSetup temporary files and mountpoints.

"""

import commands
import os
import subprocess
import gtk

from config import *

def initial_cleanup():
    """
    Preventively delete previous work directory and configuration files
    that might have been left from earlier use of LiloSetup, before creating
    a new work directory.

    """
    try :
        os.remove(stub_location)
    except OSError:
        pass
    try :
        os.remove(configfile_location)
    except OSError:
        pass
    try :
        # We are using os.rmdir instead of os.rmtree in case some partitions would still
        # be mounted on a work directory created by a previous use of LiloSetup
        os.rmdir(work_dir)
    except OSError:
        pass
    try :
        os.mkdir(work_dir)
    except OSError:
        pass


def lilosetup_undo():
    """
    Purge customizations and revert to initial defaults.
    In other words, unmount temporary mountpoints and cleanup some temporary files.

    """
    # Reset verification that ensures that at least one partition was set
    global partition_set
    del partition_set[:]
    # First we unmount the various temporary mountpoints
    while temp_mount :
        subprocess.call("umount " + temp_mount[0] + " 2>/dev/null", shell=True)
        temp_mount.remove(temp_mount[0])
    # Then we remove the temporary mountpoints created by LiloSetup
    while temp_dir :
        try:
            os.removedirs(temp_dir[0])
        except OSError:
            pass
        temp_dir.remove(temp_dir[0])
    # Last we unmount & remove the temporary mountpoint for the temporary chrooted partition
    if temp_chroot_mnt:
        subprocess.call("umount " + temp_chroot_mnt + " 2>/dev/null", shell=True)
    try:
        os.removedirs(temp_chroot_mnt)
    except OSError:
        pass
    # Removal of the temporary configuration file
    try:
        os.remove(configfile_location)
    except OSError:
        pass


def lilosetup_quit():
    """
    Clean up all temporary files and directories when exiting.
    Unmount temporary mountpoints, cleanup temporary files and close LiloSetup window.

    """
    lilosetup_undo()
    # Removal of the configuration stub file
    try:
        os.remove(stub_location)
    except OSError:
        pass
    # Removal of the temporary work directory
    try :
        # We are using os.rmdir instead of os.rmtree in case some partitions would still be mounted on the workdirectory
        os.rmdir(work_dir)
    except OSError:
        pass
    # Quit LiloSetup GUI
    gtk.main_quit()

