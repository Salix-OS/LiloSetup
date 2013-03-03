#!/usr/bin/env python

"""
Functions related to bootable partitions

"""

import commands
import glob
import os
import subprocess
from config import * 

def check_and_mount(partition):
    """
    Check if a partition is mounted and mount it if necessary.
    
    """
    partition_mountpoint = ''
    mount_info = commands.getoutput("mount").splitlines()
    while mount_info:
        if partition in mount_info[0]:
            # The partition is mounted
            partition_mountpoint = mount_info[0].split()[2]
            break
        mount_info.remove(mount_info[0])
    if mount_info == [] :
        # The partition is not mounted, we need to do it.
        # Except if it is a swap or an extended partition

        # Then we create the temporary mountpoint
        temporary_montpoint = work_dir + partition.replace('dev', 'mnt')
        partition_mountpoint = temporary_montpoint
        try :
            os.makedirs(temporary_montpoint)
            temp_dir.append(temporary_montpoint)# allows clean deleting of temporary directories later
        except OSError :
            pass
        # Then we mount the partition on it
        subprocess.call("mount " + partition + " " + temporary_montpoint + " 2>/dev/null", shell=True)
        temp_mount.append(temporary_montpoint) # allows clean unmounting of temporary mounting later
    return partition_mountpoint

def check_and_unmount(partition):
    """
    Check if a partition is unmounted and unmounts if necessary
    (only if it was mounted by LiloSetup).
    
    """
    mount_info=commands.getoutput("mount").splitlines()
    while mount_info:
        if partition in mount_info[0] :
            # The partition is mounted, we need to unmount it and remove the temporary mountpoint.
            # First we unmount the device but only if if was mounted by LiloSetup
            temporary_montpoint = work_dir + partition.replace('dev', 'mnt')
            subprocess.call("umount " + temporary_montpoint + " 2>/dev/null", shell=True)
            try :
                temp_mount.remove(temporary_montpoint)
            except ValueError :
                pass # Not there since it wasn't mounted by LiloSetup
            # Then we remove the temporary mountpoint
            try:
                os.removedirs(temporary_montpoint)
            except OSError:
                pass # The directory doesn't exist since it wasn't created by LiloSetup
            try :
                temp_dir.remove(temporary_montpoint)
            except ValueError :
                pass # Not there since it wasn't created by LiloSetup
        mount_info.remove(mount_info[0])

def check_if_bootable(partition):
    """
    Check if a partition is bootable and if so, retrieve basic info from it.
    (basic substitute for os-prober)
    
    """
    partition_device = ''
    file_system = ''
    operating_system = ''
    kernel_check = []
    win_boot_flag = []
    partition_mountpoint = check_and_mount(partition)
    # check for a Linux kernel
    kernel_check = glob.glob(partition_mountpoint + "/boot/vmlinuz*")
    win_boot_flag = commands.getoutput('fdisk -l | grep "\*" | grep ' + partition )
    # Check for Linux partition
    if kernel_check != [] :
        # This is probably a Linux bootable partititon, let's check it out a bit more
        if os.path.isdir(partition_mountpoint + '/proc') is True and os.path.isdir(partition_mountpoint + '/sys') is True:
            # Define the partition device
            partition_device = partition
            # Get the file system
            string_output = 'blkid ' + partition + ' | grep -m 1 TYPE'
            file_system = commands.getoutput(string_output).split()[-1].split('"')[1]
            # Define the operating system.
            try :
                version_file_path = (partition_mountpoint + "/etc/lsb-release")
                version_file = open(version_file_path, "r")
                version_file_lines = version_file.read().splitlines()
                for line in version_file_lines :
                    if "DISTRIB_ID" in line :
                        operating_system = line.split("=")[1]
                        version_file.close()
                        break
            except :
                try :
                    version_file_path = glob.glob(partition_mountpoint + "/etc/*release*")[0]
                    version_file = open(version_file_path, "r")
                    version_file_content = version_file.read()
                    distrib_name = version_file_content.split()[0].split('=')[1]
                    distrib_version = version_file_content.split()[1].split('=')[1].strip('"')
                    operating_system = distrib_name + ' ' + distrib_version
                    version_file.close()
                except :
                    try :
                        version_file_path = glob.glob(partition_mountpoint + "/etc/*version*")[0]
                        version_file = open(version_file_path, "r")
                        operating_system = version_file.read().split()[0]
                        version_file.close()
                    except:
                        version_file.close()
                        operating_system = "Unknown"
            return partition_device, file_system, operating_system
    # else check for Windows boot partitions
    elif partition in win_boot_flag :
        # This could be a Windows bootable system, let's check it out a bit more
        win_path =["/Windows/System32", "/WINDOWS/system32", "/WINDOWS/SYSTEM32", "/windows/system32"]
        win_file =["/IO.SYS", "/io.sys", "/MSDOS.SYS", "/msdos.sys", "/KERNEL.SYS", "/kernel.sys", "/COMMAND.COM", "/command.com", "/CONFIG.SYS", "/config.sys", "/autoexec.bat", "/AUTOEXEC.BAT", "bootmgr"]
        for i in win_path :
            winboot_dir_path = os.path.isdir(partition_mountpoint + i)
            if winboot_dir_path is True :
                for i in win_file :
                    winboot_file_path = os.path.isfile(partition_mountpoint + i)
                    if winboot_file_path is True :
                        # Define the partition device
                        partition_device = partition
                        # Get the file system
                        string_output = 'blkid ' + partition + ' | grep -m 1 TYPE'
                        file_system = commands.getoutput(string_output).split()[-1].split('"')[1]
                        # Define the operating system.
                        operating_system = "Windows"
                        return partition_device, file_system, operating_system
                        break
    check_and_unmount(partition)

   