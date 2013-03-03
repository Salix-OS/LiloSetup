#!/usr/bin/env python

"""
Functions related to LILO configuration file

"""

import os
from gettext import gettext as _

def purge_old_stub(stub_location):
    """
    Purge eventual stub remnant from previous use of LiloSetup
    
    """
    try:
        os.remove(stub_location)
    except OSError:
        pass

def generate_new_stub(stub_location, boot_partition):
    """
    Generate a new LILO configuration file stub with defaults that reflect 
    Salix' customizations for LILO.
    
    """
    stub = open(stub_location, "w")
    stub.write(_("# LILO configuration file\n\
# Generated by LiloSetup\n"))
    stub.write("#\n")
    stub.write(_("# Start LILO global section\n\
# Append any additional kernel parameters:\n"))
    stub.write('append = "vt.default_utf8=1 "\n')
    stub.write("boot = " + boot_partition + "\n")
    stub.write("lba32\n")
    stub.write("compact\n")
    stub.write("\n")
    stub.write(_("# Boot BMP Image.\n\
# Bitmap in BMP format: 640x480x8\n"))
    stub.write("bitmap = /boot/salix.bmp\n")
    stub.write(_("# Menu colors (foreground, background, shadow, highlighted\n\
# foreground, highlighted background, highlighted shadow):\n"))
    stub.write("bmp-colors = 255,20,255,20,255,20\n")
    stub.write(_('# Location of the option table: location x, location y, number of\n\
# columns, lines per column (max 15), "spill" this is how many\n\
# entries must be in the first column before the next begins to\n\
# be used.  We do not specify it here, as there is just one column.\n'))
    stub.write("bmp-table = 60,6,1,16\n")
    stub.write(_("# Timer location x, timer location y, foreground color,\n\
# background color, shadow color.\n"))
    stub.write("bmp-timer = 65,29,0,255\n")
    stub.write("\n")
    stub.write(_("# Standard menu.\n\
# Or, you can comment out the bitmap menu above and \n\
# use a boot message with the standard menu:\n"))
    stub.write("# message = /boot/boot_message.txt\n")
    stub.write("\n")
    stub.write(_("# Wait until the timeout to boot (if commented out, boot the\n\
# first entry immediately):\n"))
    stub.write("prompt\n")
    stub.write(_("# Timeout before the first entry boots.\n\
# This is given in tenths of a second, so 600 for every minute:\n"))
    stub.write("timeout = 50\n")
    stub.write(_("# Override dangerous defaults that rewrite the partition table:\n"))
    stub.write("change-rules\n")
    stub.write("reset\n")
    stub.write("\n")
    stub.write(_("# Normal VGA console\n"))
    stub.write("# vga = normal\n")
    stub.write(_("# VESA framebuffer console @ 1600x1200x16m\n"))
    stub.write("# vga=799\n")
    stub.write(_("# VESA framebuffer console @ 1600x1200x64k\n"))
    stub.write("# vga=798\n")
    stub.write(_("# VESA framebuffer console @ 1600x1200x32k\n"))
    stub.write("# vga=797\n")
    stub.write(_("# VESA framebuffer console @ 1600x1200x256\n"))
    stub.write("# vga=796\n")
    stub.write(_("# VESA framebuffer console @ 1280x1024x16m\n"))
    stub.write("# vga=795\n")
    stub.write(_("# VESA framebuffer console @ 1280x1024x64k\n"))
    stub.write("# vga=794\n")
    stub.write(_("# VESA framebuffer console @ 1280x1024x32k\n"))
    stub.write("# vga=793\n")
    stub.write(_("# VESA framebuffer console @ 1280x1024x256\n"))
    stub.write("# vga=775\n")
    stub.write(_("# VESA framebuffer console @ 1024x768x16m\n"))
    stub.write("# vga=792\n")
    stub.write(_("# VESA framebuffer console @ 1024x768x64k\n"))
    stub.write("# vga=791\n")
    stub.write(_("# VESA framebuffer console @ 1024x768x32k\n"))
    stub.write("# vga=790\n")
    stub.write(_("# VESA framebuffer console @ 1024x768x256\n"))
    stub.write("# vga=773\n")
    stub.write(_("# VESA framebuffer console @ 800x600x16m\n"))
    stub.write("# vga=789\n")
    stub.write(_("# VESA framebuffer console @ 800x600x64k\n"))
    stub.write("# vga=788\n")
    stub.write(_("# VESA framebuffer console @ 800x600x32k\n"))
    stub.write("# vga=787\n")
    stub.write(_("# VESA framebuffer console @ 800x600x256\n"))
    stub.write("# vga=771\n")
    stub.write(_("# VESA framebuffer console @ 640x480x16m\n"))
    stub.write("# vga=786\n")
    stub.write(_("# VESA framebuffer console @ 640x480x64k\n"))
    stub.write("# vga=785\n")
    stub.write(_("# VESA framebuffer console @ 640x480x32k\n"))
    stub.write("# vga=784\n")
    stub.write(_("# VESA framebuffer console @ 640x480x256\n"))
    stub.write("# vga=769\n")
    stub.write(_("# End LILO global section\n"))
    stub.write("#\n")
    stub.write(_("# LiloSetup can be executed from a LiveCD. This means that lilo\n\
# could be issued from a 'chrooted' Linux partition, which would\n\
# happen to be the first Linux partition listed below.\n\
# Therefore the following paths are relevant only when viewed\n\
# from that 'chrooted' partition's perspective. Please take this\n\
# constraint into consideration if you must modify this file\n\
# or else LiloSetup will fail.\n"))
    stub.write("#\n")
    stub.write(_('# If later on you want to use this configuration file directly\n\
# with lilo in a command line, use the following syntax:\n\
# "lilo -v -C /etc/lilosetup/conf" instead of the traditional\n\
# "lilo -v" command. You must of course issue that command from\n\
# the operating system holding /etc/lilosetup.conf & ensure that\n\
# all partitions referenced in it are mounted on the appropriate\n\
# mountpoints.\n'))
    stub.close()