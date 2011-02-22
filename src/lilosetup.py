#!/usr/bin/env python

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#                                                                             #
# LiloSetup - GTK frontend to setup lilo, from a LiveCD or a standard system. #
#                                                                             #
# Copyright Pierrick Le Brun <akuna~at~salixos~dot~org>.                      #
#                                                                             #
# This program is free software; you can redistribute it and/or               #
# modify it under the terms of the GNU General Public License                 #
# as published by the Free Software Foundation; either version 2              #
# of the License, or (at your option) any later version.                      #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program; if not, write to the Free Software                 #
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. #
#                                                                             #
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

# version = '0.2.7'

import shutil
import subprocess
import os
import sys
import commands
import glob
import gtk

# Internationalization
import locale
import gettext
import gtk.glade
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("lilosetup", "/usr/share/locale")
gettext.textdomain("lilosetup")
gettext.install("lilosetup", "/usr/share/locale", unicode=1)
gtk.glade.bindtextdomain("lilosetup", "/usr/share/locale")
gtk.glade.textdomain("lilosetup")

# The following 4 functions were borrowed from ndisgtk 
# The study of ndisgtk code taught me a lot when I first explored python/glade3 ;)

# Info window skeleton:
def info_dialog(message, parent = None):
    """
    Display an information message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK, flags = gtk.DIALOG_MODAL)
    dialog.set_markup(message)
    global result_info
    result_info = dialog.run()
    dialog.destroy()

# Warning window skeleton:
def warning_dialog(message, parent = None):
    """
    Display a warning message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_WARNING, flags = gtk.DIALOG_MODAL)
    dialog.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES)
    dialog.add_buttons(gtk.STOCK_NO, gtk.RESPONSE_NO)
    dialog.set_default_response(gtk.RESPONSE_NO)
    dialog.set_markup(message)
    global result_warning
    result_warning = dialog.run()
    dialog.destroy()

# Error window skeleton:
def error_dialog(message, parent = None):
    """
    Display an error message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_CLOSE, flags = gtk.DIALOG_MODAL)
    dialog.set_markup(message)
    global result_error
    result_error = dialog.run()
    dialog.destroy()

# Output of bash commands :
def run_bash(cmd):
    """
    Take a bash command and return the output.

    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read().strip()
    return out  #This is the stdout from the shell command

# This will help us monitor whether the configuration file is succesfully created or not
config_creation = []
# This will help us to ensure at least one  partition has been configured
partition_set = []
# Initialize the temporary mountpoint lists
temp_mount = []
temp_dir = []
# Initialize key mountpoints value
temp_chroot_mnt = ''
chroot_mnt = ''
# Cleanup/Setup LiloSetup temporary work directory & configuration file
work_dir = "/tmp/lilosetup"
try :
     # We are using os.rmdir instead of os.rmtree in case some partitions would still be mounted on the workdirectory
    os.rmdir(work_dir)
except OSError:
    pass
try :
    os.mkdir(work_dir)
except OSError:
    pass
config_location = work_dir + "/lilosetup.conf"
try :
    os.remove(config_location)
except OSError:
    pass
# Build LiloSetup configuration file stub:
# Get the booting device, should be the first hard drive
boot_partition = commands.getoutput('fdisk -l | grep "dev" -m 1 | cut -f2 -d " "').strip(':')
# Create the configuration file stub
stub_location = work_dir + "/lilosetup.stub"
# Delete any old stub if present
try:
    os.remove(stub_location)
except OSError:
    pass
# The following defaults reflect Salix' customisations for Lilo
stub = open(stub_location, "w")
stub.write(_("# LILO configuration file\n\
# Generated by LiloSetup\n"))
stub.write("#\n")
stub.write(_("# Start LILO global section\n\
# Append any additional kernel parameters:\n"))
stub.write('append = "quiet vt.default_utf8=1 "\n')
stub.write("boot = " + boot_partition + "\n")
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
stub.write(_("# VESA framebuffer console @ 1600x1200x64k\n"))
stub.write("# vga=798\n")
stub.write(_("# VESA framebuffer console @ 1600x1200x32k\n"))
stub.write("# vga=797\n")
stub.write(_("# VESA framebuffer console @ 1600x1200x256\n"))
stub.write("# vga=796\n")
stub.write(_("# VESA framebuffer console @ 1280x1024x64k\n"))
stub.write("# vga=794\n")
stub.write(_("# VESA framebuffer console @ 1280x1024x32k\n"))
stub.write("# vga=793\n")
stub.write(_("# VESA framebuffer console @ 1280x1024x256\n"))
stub.write("# vga=775\n")
stub.write(_("# VESA framebuffer console @ 1024x768x64k\n"))
stub.write("# vga=791\n")
stub.write(_("# VESA framebuffer console @ 1024x768x32k\n"))
stub.write("# vga=790\n")
stub.write(_("# VESA framebuffer console @ 1024x768x256\n"))
stub.write("# vga=773\n")
stub.write(_("# VESA framebuffer console @ 800x600x64k\n"))
stub.write("# vga=788\n")
stub.write(_("# VESA framebuffer console @ 800x600x32k\n"))
stub.write("# vga=787\n")
stub.write(_("# VESA framebuffer console @ 800x600x256\n"))
stub.write("# vga=771\n")
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

# Let's now set the appropriate framebuffer...
# Setting bash environment variable
os.putenv("stubfile", stub_location)

# This function gives a failsafe option in case of trouble with framebuffer:
def failsafe_fb():
    FBLINE= """
    cat $stubfile | grep "vga = normal" -m 1 -n | cut -f1 -d :
    """
    fbline = run_bash(FBLINE)
    os.putenv("editline", fbline)
    set_framebuffer = "sed $editline's/# //' -i $stubfile"
    subprocess.call(set_framebuffer, shell=True)

# We first check if framebuffer is available

USEDFB = """
fbset | grep -w mode | cut -f2 -d " " | cut -f1 -d "-" | sed 's/"//'
"""
if run_bash(USEDFB):
    os.putenv("setfb", run_bash(USEDFB))
    # We also need to make sure that the adequate framebuffer resolution is in the stub
    FBLINE= """
    cat $stubfile | grep "@ $setfb" -m 1 -n | cut -f1 -d :
    """
    fbline = run_bash(FBLINE)
    if fbline != '' :
        fblineplus = int(fbline) + 1
        os.putenv("editline", repr(fblineplus))
        set_framebuffer = "sed $editline's/# //' -i $stubfile"
        subprocess.call(set_framebuffer, shell=True)
    # If no fitting resolution is available from the stub then failsafe to vga-normal
    else :
        failsafe_fb()
# If framebuffer is not available, we can use failsafe option again
else :
    failsafe_fb()

def lilosetup_undo():
    """
    Unmount temp mountpoints & cleanup some temp files

    """
    global temp_mount, temp_dir
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
        os.remove(config_location)
    except OSError:
        pass

def lilosetup_quit():
    """
    Unmount temp mountpoints, cleanup all temp files & close LiloSetup window.

    """
    if partition_set == [] :
        pass
    else:
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

class LiloSetup:
    """
    Main application class.
    """
    def __init__(self):
        """
        Initialize the application.
        """
        builder = gtk.Builder()
        if os.path.exists("lilosetup.glade") :
            builder.add_from_file("lilosetup.glade")
        elif os.path.exists("/usr/share/lilosetup/lilosetup.glade") :
            builder.add_from_file("/usr/share/lilosetup/lilosetup.glade")
        elif os.path.exists("../share/lilosetup/lilosetup.glade") :
            builder.add_from_file("../share/lilosetup/lilosetup.glade")

        # Get a handle on the glade file widgets we want to interact with
        self.Window = builder.get_object("lilosetup_main")
        self.AboutDialog = builder.get_object("about_dialog")
        self.BootPartitionTreeview = builder.get_object("boot_partition_treeview")
        self.BootPartitionListStore = builder.get_object("boot_partition_list_store")
        self.EditButton = builder.get_object("edit_button")
        self.UndoButton = builder.get_object("undo_button")
        self.ExecuteButton = builder.get_object("execute_button")
        self.UpButton = builder.get_object("up_button")
        self.DownButton = builder.get_object("down_button")
        self.LabelCellRendererCombo = builder.get_object("label_cellrenderercombo")
        self.LabelTreeViewColumn = builder.get_object("label_treeviewcolumn")
        self.LabelContextHelp = builder.get_object("label_context_help")

        # Connect signals
        builder.connect_signals(self)

        # Initialize the contextual help box
        global context_intro
        context_intro = _("<b>LiloSetup will install a new LILO bootloader on your computer.</b> \n\
\n\
A bootloader is required to load the main operating system of a computer and will initially display \
a boot menu if several operating systems are available on the same computer.")
        self.LabelContextHelp.set_markup(context_intro)

        # Initialize the partition list
        global setup_partition_list
        def setup_partition_list():
            """
            Generate the initial partition list.
            """
            # We need to get the file system of each device whether mounted or not
            # Start on a clean slate
            self.BootPartitionListStore.clear()
            # Initialize the different variables
            boot_partition_feedline_list = []
            partition_device = ''
            file_system = ''
            operating_system = ''
            boot_label = _('Set...')
            boot_partition_feedline = []
            try_prober = commands.getoutput('LANG=C os-prober')
            if 'os-prober' not in try_prober :
                boot_partition_output = try_prober.splitlines()
                for line in boot_partition_output:
                    if line.startswith("/dev/") :
                        # Get the partition device
                        partition_device = line.split(':')[0]
                        # Check that it is not a Windows factory settings recovery partition...
                        lshal_recovery_output = 'lshal | grep -B1 -A40 ' + partition_device + ' | grep -m 1 -i recovery'
                        partition_is_recovery = commands.getoutput(lshal_recovery_output)
                        if partition_is_recovery == '' :
                            # Get the operating system
                            try :
                                operating_system = line.split(':')[1].split()[0]
                            except IndexError :
                                operating_system = line.split(':')[2]
                            # Get the file system
                            lshal_string_output = 'lshal | grep -B1 -A40 ' + partition_device + ' | grep -m 1 volume.fstype'
                            file_system = commands.getoutput(lshal_string_output).split("'")[1]
                            boot_partition_feedline = [partition_device, file_system, operating_system, boot_label]
                            boot_partition_feedline_list.append(boot_partition_feedline)
            else:
                error_dialog(_("\nSorry! os-prober, a dependency of LiloSetup appears to be missing. Please verify and correct.\n"))
                sys.exit(1)
            # Add the main partition of the os we are in ( partition mounted on / is not taken care by os-prober)
            os.putenv("root_partition", "\'/\'")
            this_os_main_partition = commands.getoutput("lshal | grep -B40  $root_partition | grep block.device")
            try :
                if '/dev/' in this_os_main_partition.split("'")[1]:
                    # Get the partition device
                    partition_device = this_os_main_partition.split("'")[1]
                    # Get the file system
                    lshal_string_output = 'lshal | grep -B1 -A40 ' + partition_device + ' | grep -m 1 volume.fstype'
                    file_system = commands.getoutput(lshal_string_output).split("'")[1]
                    # Get the operating system.
                    try :
                        version_file_path = glob.glob("/etc/*version*")[0]
                        version_file = open(version_file_path)
                        operating_system = version_file.read().split()[0]
                    except :
                        operating_system = "Unknown"
                    # Put it all together
                    boot_partition_feedline = [partition_device, file_system, operating_system, boot_label]
                    boot_partition_feedline_list.append(boot_partition_feedline)
                else:
                    pass
            except:
                pass
            # Insert Menu Label editable combobox
            # We get this gui handle here to ensure it is reset to its default in the event of a configuration undo
            self.BootLabelListStore = builder.get_object("boot_label_list_store")
            self.LabelCellRendererCombo.set_property("model", self.BootLabelListStore)
            self.LabelCellRendererCombo.set_property('text-column', 0)
            self.LabelCellRendererCombo.set_property('editable', True)
            self.LabelCellRendererCombo.set_property('cell_background', '#CCCCCC')
            self.LabelTreeViewColumn.set_attributes(self.LabelCellRendererCombo, text = 3)
            # Sort the list for the partitions who do not follow the hard drive order
            boot_partition_feedline_list.sort()
            # Populate GUI partition list view rows
            for line in boot_partition_feedline_list:
                line.append('gtk-edit')
                self.BootPartitionListStore.append(line)
        # Show partition list
        setup_partition_list()

        global create_configuration
        def create_configuration():
            """
            Populate lilosetup.conf & mounts needed partition to lilo's chrooted partition.
            """
            shutil.copy(stub_location,config_location)
            # Re-initialize key variables
            # Temporary mountpoint list
            global temp_mount, temp_chroot_mnt, temp_dir, partition_set, chroot_mnt
            temp_mount = []
            # Configuration file
            config_creation = []
            # This will help ensure that at least one  partition has been configured
            partition_set = []
            # This is for retrieving all the partition rows values
            BootPartitionsValues = []
            x = 0
            while x <= 20 :
                try :
                    treeiter = self.BootPartitionListStore.get_iter(x)
                    x += 1
                    BootPartitionsValues.append(self.BootPartitionListStore.get(treeiter, 0, 1, 2, 3))
                except ValueError :
                    break
            for set in BootPartitionsValues:
                am_i_there = 'cat ' + config_location + ''' | grep -w label | cut -f3 -d " " '''
                already_there = commands.getoutput(am_i_there).splitlines()
                windows_sys_labels = ['Microsoft', 'Windows']
                # We ensure there are no identical labels
                if set[3] in already_there :
                    error_dialog(_("You have used the same label for different Operating Systems. Please verify and correct.\n"))
                    self.EditButton.set_sensitive(False)
                    self.ExecuteButton.set_sensitive(False)
                    self.UpButton.set_sensitive(True)
                    self.DownButton.set_sensitive(True)
                    self.BootPartitionTreeview.set_sensitive(True)
                    config_creation.append('failure')
                    break
                # We need to ensure that the labels are unique and do not contain empty space
                elif ' ' in set[3] :
                    error_dialog(_("\nAn Operating System label should not contain any space. \n\nPlease verify and correct.\n"))
                    self.EditButton.set_sensitive(False)
                    self.ExecuteButton.set_sensitive(False)
                    self.UpButton.set_sensitive(True)
                    self.DownButton.set_sensitive(True)
                    self.BootPartitionTreeview.set_sensitive(True)
                    config_creation.append('failure')
                    break
                # We ensure that the label is less than 15 characters long
                elif len(set[3]) >= 15 :
                    error_dialog(_("\nAn Operating System label should not hold more than 15 characters. \n\nPlease verify and correct.\n"))
                    self.EditButton.set_sensitive(False)
                    self.ExecuteButton.set_sensitive(False)
                    self.UpButton.set_sensitive(True)
                    self.DownButton.set_sensitive(True)
                    self.BootPartitionTreeview.set_sensitive(True)
                    config_creation.append('failure')
                    break
                # We skip the partitions that have not been configured by the user
                elif _('Set...') in set[3] :
                    pass
                # If Windows partition:
                elif set[2] in windows_sys_labels :
                    # Append to lilosetup.conf
                    stub = open(config_location, "a")
                    stub.write("#\n")
                    stub.write(_("# Windows bootable partition config begins\n"))
                    stub.write("other = " + set[0] + "\n")
                    stub.write("label = " + set[3] + "\n")
                    stub.write(_("# Windows bootable partition config ends\n"))
                    stub.close()
                else:
                    # Applies to Linux partitions
                    # Let's determines Lilo's chrooted Linux partition directory, only happens one.
                    am_i_first = 'cat ' + config_location + ' | grep -i uuid'
                    already_done = commands.getoutput(am_i_first).splitlines()
                    if already_done == []:
                        # This is the first Linux partition, the one we will chroot in to launch lilo!
                        chroot_dev = set[0]
                        mount_inconf = '' # Defines how the partitions 'appears' mounted from the 'chrooted' partition's viewpoint
                        other_mnt = '' # we need this blank for the first Linux partition
                        # Check if lilo's chroot directory is mounted
                        CHROOT_MNT="mount | grep -v \/mnt\/live | grep " + chroot_dev + " | awk -F' ' '{print $3 }'"
                        chroot_mnt = commands.getoutput(CHROOT_MNT) # chrooted partition mountpoint
                        if chroot_mnt == '' :
                            # Either it is not mounted or else it is used as the current root filesystem (/) but linked to /dev/root
                            check_if_root = commands.getoutput("ls -l /dev/root | grep " + chroot_dev.replace("/dev/", ""))
                            if check_if_root != '' :
                                # The link leads to the 'chrooted' device, it is the current file system.
                                chroot_mnt = "/"
                            else :
                                # It is not mounted, let's create a temporary mountpoint ourselves
                                temp_chroot_mnt = work_dir + chroot_dev.replace('dev', 'mnt')
                                try:
                                    os.makedirs(temp_chroot_mnt)
                                except OSError :
                                    pass                               
                                # Mount the 'chrooted' partition
                                chroot_mnt_command = "mount " + chroot_dev + " " + temp_chroot_mnt + " 2>/dev/null"
                                subprocess.call(chroot_mnt_command, shell=True)
                                chroot_mnt = temp_chroot_mnt
                        if chroot_mnt != "/" :
                            # This is necessary only if we execute lilo from a 'real' chrooted partition
                            subprocess.call("mount --bind /dev " + chroot_mnt + "/dev 2>/dev/null", shell=True)
                            temp_mount.append(chroot_mnt + "/dev") # allows unmounting temporary mountpoints later
                            subprocess.call("mount -t proc proc " + chroot_mnt + "/proc 2>/dev/null", shell=True)
                            temp_mount.append(chroot_mnt + "/proc") # allows unmounting temporary mountpoints later
                    else : # This applies to all subsequent partitions
                        # How this partition is --or should be-- mounted on a the current partition
                        if chroot_mnt == "/" :
                            mount_info=commands.getoutput("mount").splitlines()
                            while mount_info:
                                if set[0] in mount_info[0]:
                                    other_mnt = mount_info[0].split()[2]
                                mount_info.remove(mount_info[0])
                            if other_mnt == '':
                                # We need to create a temporary mountpoint ourself & mount it:
                                temp_other_mnt = work_dir + set[0].replace('dev', 'mnt')
                                try :
                                    os.makedirs(temp_other_mnt)
                                    temp_dir.append(temp_other_mnt)
                                except OSError :
                                    pass
                                other_mnt = temp_other_mnt
                                # all needed temporary mountpoints on chrooted partitions exist, we can now mount them
                                mnt_command = "mount " + set[0] + " " + other_mnt + " 2>/dev/null"
                                subprocess.call(mnt_command, shell=True)
                                temp_mount.append(other_mnt) # allows cleanup temporary mountpoints later
                        # Else, how this partition should (and will) be mounted on a 'real' chrooted partition
                        else :
                            other_mnt = '' # reinitialization
                            # We create a fork, chroot in the child process & pipe the mount info to the parent process
                            # If lilosetup is executed from a 32bit environment it can't chroot to a 64bit environment.
                            if os.path.isdir('/lib64') is not True and os.path.isdir(chroot_mnt + '/lib64') is True:
                                pass
                            else :
                                r, w = os.pipe() # these are file descriptors, not file objects
                                pid = os.fork()
                                if pid:
                                    chroot_mnt     # Parent process
                                    os.close(w) # use os.close() to close a file descriptor
                                    r = os.fdopen(r) # turn r into a file object
                                    other_mnt = r.read()
                                    os.waitpid(pid, 0) # make sure the child process gets cleaned up
                                else:
                                    # Child process
                                    os.close(r)
                                    w = os.fdopen(w, 'w')
                                    os.chroot(chroot_mnt)
                                    # We use fake mounting to avoid dealing with eventual fstab UUID schemes
                                    subprocess.call("mount -af 2>/dev/null", shell=True)
                                    # Retrieve the mount info
                                    mount_info=commands.getoutput("mount").splitlines()
                                    while mount_info:
                                        if set[0] in mount_info[0]:
                                            other_mnt = mount_info[0].split()[2]
                                        elif set[0].replace('hd', 'sd') in mount_info[0]:
                                            other_mnt = mount_info[0].split()[2]
                                        elif set[0].replace('sd', 'hd') in mount_info[0]:
                                            other_mnt = mount_info[0].split()[2]
                                        mount_info.remove(mount_info[0])
                                    w.write(other_mnt)
                                    w.close()
                                    # Exit child process
                                    sys.exit(0)
                            if other_mnt == '':  # we need to create a temporary mountpoint ourselves
                                temp_other_mnt = work_dir + set[0].replace('dev', 'mnt')
                                try :
                                    os.makedirs(chroot_mnt + temp_other_mnt)
                                    temp_dir.append(chroot_mnt + temp_other_mnt)
                                except OSError :
                                    pass
                                other_mnt = temp_other_mnt
                            # all needed temporary mountpoints on chrooted partitions exist, we can now mount them
                            mnt_command = "mount " + set[0] + " " + chroot_mnt + other_mnt + " 2>/dev/null"
                            subprocess.call(mnt_command, shell=True)
                            temp_mount.append(chroot_mnt +other_mnt) # allows cleanup temporary mountpoints later
                    mount_inconf = other_mnt	# defines how the partition 'appears' mounted in lilosetup.conf
                    # Confirm that the partition is configured
                    partition_set.append("OK")
                    # Append to lilosetup.conf
                    stub = open(config_location, "a")
                    # There maybe a few kernels in the same partition
                    # Some of them may have an initrd, which we assume have exactly the same suffix.
                    if chroot_mnt != "/":
                        vmlist = sorted(glob.glob(chroot_mnt + other_mnt + "/boot/vmlinuz*"))
                        initlist = sorted(glob.glob(chroot_mnt + other_mnt + "/boot/initr*"))
                    if chroot_mnt == "/":
                        vmlist = sorted(glob.glob(other_mnt + "/boot/vmlinuz*"))
                        initlist = sorted(glob.glob(other_mnt + "/boot/initr*"))
                    # Remove directories
                    for i in vmlist :
                        if os.path.isdir(i) :
                            vmlist.remove(i)
                    for i in initlist :
                        if os.path.isdir(i) :
                            initlist.remove(i)
                    # Remove symbolic links
                    for i in vmlist :
                        if os.path.islink(i) :
                            vmlist.remove(i)
                    for i in initlist :
                        if os.path.islink(i) :
                            initlist.remove(i)
                    # There could be a few kernels in the same partition:
                    it = 0
                    y = 1
                    while it < len(vmlist) :
                        stub.write("#\n")
                        stub.write(_("# Linux bootable partition config begins\n"))
                        try :
                            vmlinuz_file_path = vmlist[it].split("boot")[1]
                            stub.write("image = " + mount_inconf + "/boot" + vmlinuz_file_path + "\n")
                            vmlinuz_suffix = vmlinuz_file_path.split('/')[-1].replace("vmlinuz", "")
                        except:
                             error_dialog(_("One of your partitions does not seem to hold a valid kernel file. Please verify and correct LiloSetup configuration file manually.\n"))
                        # We'll use uuid to avoid libata/non-libata confusion
                        # Find the uuid linked to the partition
                        linked_partition = set[0].split('/')[-1]
                        uuid_line = commands.getoutput('ls -l /dev/disk/by-uuid | grep ' + linked_partition).split('->')[0].split()[-1]
                        if 'Fedora' in set[2]:
                             stub.write('append = "root=UUID=' + uuid_line +' "\n')
                        else:
                            stub.write("root = /dev/disk/by-uuid/" + uuid_line +"\n")
                        if len(vmlist) == 1 :
                            # There is only one kernel so only one entry for this partition
                            stub.write("label = " + set[3] + "\n")
                        else:
                            # There is more than one kernel in the same partition, we need to create multiple entries
                            # We need to ensure that the label is not too long
                            new_label = set[3] + vmlinuz_suffix
                            if len(new_label) >= 14 :
                                corrected_label = set[3] + '-' + str(y)
                                stub.write("label = " + corrected_label +"\n")
                            else:
                                stub.write("label = " + new_label +"\n")
                        # Add the initrd if suffix is matching kernel
                        for i in initlist:
                            if vmlinuz_suffix in i:
                                initrd_file_path = i.split("boot")[1]
                                stub.write("initrd = " + mount_inconf + "/boot" + initrd_file_path + "\n")
                                break
                        # If only one kernel & one initrd, we can assume they match even if their suffix do not.
                        if it == 0 and vmlinuz_suffix not in i:
                            if len(initlist) == 1 and len(vmlist) == 1:
                                initrd_file_path = initlist[0].split("boot")[1]
                                stub.write("initrd = " + mount_inconf + "/boot" + initrd_file_path + "\n")
                        stub.write("read-only\n")
                        stub.write(_("# Linux bootable partition config ends\n"))
                        y += 1
                        it += 1
                    stub.close()

### Callback signals waiting in a constant loop: ###

### WINDOWS MAIN SIGNALS ###

    # Contextual help:
    def on_about_button_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_text(_("About Lilo Setup."))
    def on_about_button_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_context_eventbox_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_text(_("It is necessary to (re)configure the \
bootloader each time you install a new operating system on your computer. \n\
LiloSetup can also be useful in the process of a disaster recovery in which case you \
may have to launch it from a LiveCD if you have lost all other means to boot into your system.\n\
Lilosetup can indifferently be executed from a Linux LiveCD environment or from a regular \
installed Linux system.  In both cases, it will setup a new LILO bootloader on the MBR of \
your first hard drive."))
    def on_context_eventbox_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_boot_partition_treeview_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Here you must define a Boot menu label for each \
of the operating system that will be displayed on your bootloader menu.\n\
Any partition for which you do not set a  Boot menu label will not be configured and will \
not be displayed on the bootloader menu.\n\
If a few kernels are available within one partition, the label you have chosen for that \
partition will be appended numerically to create multiple menu entries for each of these kernels.\n\
Any of these settings can be edited manually in lilosetup configuration file."))
    def on_boot_partition_treeview_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_up_button_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Use this arrow if you want to move the \
selected Operating System up to a higher rank.\n\
The partition with the highest rank will be displayed on the first line of the bootloader menu.\n\
Any of these settings can be edited manually in lilosetup configuration file."))
    def on_up_button_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_down_button_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Use this arrow if you want to move the \
selected Operating System down to a lower rank.\n\
The partition with the lowest rank will be displayed on the last line of the bootloader menu.\n\
Any of these settings can be edited manually in lilosetup configuration file."))
    def on_down_button_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_undo_eventbox_enter_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(_("This will undo all settings (even manual modifications)."))
    def on_undo_eventbox_leave_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(context_intro)
    def on_edit_eventbox_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Experienced users have the possibility to \
manually edit LiloSetup configuration file (settings are identical to lilo.conf). \n\
Please do not temper with this file unless you know what you are doing and you have \
read its commented instructions regarding chrooted paths."))
    def on_edit_eventbox_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_button_quit_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Exit Lilo Setup program."))
    def on_button_quit_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_execute_eventbox_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Once you have defined your settings, \
click on this button to create your new LILO's bootloader."))
    def on_execute_eventbox_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)


    # What to do when the exit X on the main window upper right is clicked
    def gtk_main_quit(self, widget, data=None):
        lilosetup_quit()

    # What to do when the quit button is is clicked
    def on_main_window_destroy(self, widget, data=None):
        lilosetup_quit()

    # What to do when the about button is is clicked
    def on_about_button_clicked(self, widget, data=None):
        """
        Open the about dialog.

        """
        self.AboutDialog.show()

    def on_about_dialog_close(self, widget, data=None):
        """
        Close the about dialog.

        """
        self.AboutDialog.hide()
        return True

    # What to do when a combo line is edited in the Label column
    def on_label_cellrenderercombo_edited(self, widget, row_number, new_text):
        # Retrieve the selected label row iter
        bootlabelchoice = self.BootPartitionTreeview.get_selection()
        self.BootPartitionListStore, iter = bootlabelchoice.get_selected()
        # Set the new partition row value on the fourth column (3)
        self.BootPartitionListStore.set_value(iter, 3, new_text)
        if new_text != _("Set..."):
            self.BootPartitionListStore.set_value(iter, 4, 'gtk-yes')
        else:
            self.BootPartitionListStore.set_value(iter, 4, 'gtk-edit')
        self.UndoButton.set_sensitive(True)
        self.EditButton.set_sensitive(True)
        self.ExecuteButton.set_sensitive(True)
        self.UpButton.set_sensitive(True)
        self.DownButton.set_sensitive(True)

    def on_label_cellrenderercombo_editing_started(self, widget, path, data):
        self.EditButton.set_sensitive(False)
        self.ExecuteButton.set_sensitive(False)
        self.UpButton.set_sensitive(False)
        self.DownButton.set_sensitive(False)

    def on_label_cellrenderercombo_editing_canceled(self, data):
        self.EditButton.set_sensitive(True)
        self.ExecuteButton.set_sensitive(True)
        self.UpButton.set_sensitive(True)
        self.DownButton.set_sensitive(True)

    def on_up_button_clicked(self, widget, data=None):
        """
        Move the row items upward.

        """
        # Obtain selection
        sel = self.BootPartitionTreeview.get_selection()
        # Get selected path
        ( model, rows ) = sel.get_selected_rows()
        if rows == [] :
            return
        # Get new path for each selected row and swap items. 
        for path1 in rows:
        # Move path2 upward
            path2 = ( path1[0] - 1, )
        # If path2 is negative, we're trying to move first path up. 
        if path2[0] < 0:
            return
        # Obtain iters and swap items.
        iter1 = model.get_iter( path1 )
        iter2 = model.get_iter( path2 )
        model.swap( iter1, iter2 )

    def on_down_button_clicked(self, widget, data=None):
        """
        Move the row items downward.

        """
        # Obtain selection
        sel = self.BootPartitionTreeview.get_selection()
        # Get selected path
        ( model, rows ) = sel.get_selected_rows()
        if rows == [] :
            return
        # Get new path for each selected row and swap items.
        for path1 in rows:
        # Move path2 downward
            path2 = ( path1[0] + 1, )
        # Obtain iters and swap items.
        # If the second iter is invalid, we're trying to move the last item down.
        iter1 = model.get_iter( path1 )
        try :
            iter2 = model.get_iter( path2 )
        except ValueError:
            return
        model.swap( iter1, iter2 )

    def on_undo_button_clicked(self, widget, data=None):
        """
        Delete lilosetup.conf & unmount temporary mountpoints
        """
        setup_partition_list()
        self.EditButton.set_sensitive(False)
        self.UndoButton.set_sensitive(False)
        self.ExecuteButton.set_sensitive(False)
        self.UpButton.set_sensitive(True)
        self.DownButton.set_sensitive(True)
        self.BootPartitionTreeview.get_selection().unselect_all()
        self.BootPartitionTreeview.set_sensitive(True)
        if partition_set == [] :
            pass
        else:
            lilosetup_undo()
            
    def on_edit_button_clicked(self, widget, data=None):
        """
        Opens the edit lilosetup.conf dialog.
        """
        # Check if the configuration file has already beeen created
        if os.path.isfile(config_location) == False :
            create_configuration()
        if 'failure' not in config_creation:
            try :
                if os.path.isfile("/usr/bin/mousepad") :
                    subprocess.call('/usr/bin/mousepad ' + config_location + ' 2>/dev/null', shell=True)
                elif os.path.isfile("/usr/bin/leafpad") :
                    subprocess.call('/usr/bin/leafpad ' + config_location + ' 2>/dev/null', shell=True)
                elif os.path.isfile("/usr/bin/gedit") :
                    subprocess.call('/usr/bin/gedit ' + config_location + ' 2>/dev/null', shell=True)
                elif os.path.isfile("/usr/bin/kwrite") :
                    subprocess.call('/usr/bin/kwrite ' + config_location + ' 2>/dev/null', shell=True)
                elif os.path.isfile("/usr/bin/geany") :
                    subprocess.call('/usr/bin/geany ' + config_location + ' 2>/dev/null', shell=True)
                else :
                    subprocess.call('xdg-open ' + config_location + ' 2>/dev/null', shell=True)
                # Ensure changes are taken into account
                subprocess.call('sync', shell=True)
                subprocess.call('rm -f ' + config_location + '~ 2>/dev/null', shell=True)
                self.UpButton.set_sensitive(False)
                self.DownButton.set_sensitive(False)
                self.ExecuteButton.set_sensitive(True)
                self.BootPartitionTreeview.get_selection().unselect_all()
                self.BootPartitionTreeview.set_sensitive(False)
            except :
                self.EditButton.set_sensitive(False)
                error_dialog(_("Sorry, LiloSetup is unable to find a suitable text editor in your system. You will not be able to manually modify LiloSetup configuration.\n"))

    def on_execute_button_clicked(self, widget, data=None):
        # Check if the configuration file has already beeen created
        if os.path.isfile(config_location) == False :
            create_configuration()
        if 'failure' not in config_creation:
            # Check if at least one Linux partition has been configured:
            if partition_set == [] :
                error_dialog(_("Your configuration is not complete. Please, select at least one Linux booting partition and define its Boot menu label.\n"))
                self.UndoButton.clicked()
            else:
                warning_dialog(_("You are about to install a new LILO bootloader. Are you sure you want to continue?"))
                if result_warning == gtk.RESPONSE_YES:
                    # If previous lilosetup.conf file exist, save it as lilosetup.old
                    if os.path.isfile(chroot_mnt + "/etc/lilosetup.conf") == True :
                        os.rename(chroot_mnt + "/etc/lilosetup.conf", chroot_mnt +'/etc/lilosetup.old')
                    shutil.copy(config_location, chroot_mnt + "/etc/lilosetup.conf")
                    # Copy /boot/salix graphics to chroot_mnt if needed
                    if os.path.isfile(chroot_mnt + "/boot/salix.bmp") == False :
                        if os.path.isfile("/boot/salix.bmp") == True :
                            shutil.copy("/boot/salix.bmp", chroot_mnt + "/boot/salix.bmp")
                        elif os.path.isfile("/mnt/live/memory/images/01-core.lzm/boot/salix.bmp") == True :
                            shutil.copy("/mnt/live/memory/images/01-core.lzm/boot/salix.bmp", chroot_mnt + "/boot/salix.bmp")
                    # Execute Lilo
                    lilo_command = "lilo -v -r " + chroot_mnt + " -C /etc/lilosetup.conf > /var/log/lilosetup.log"
                    output = commands.getstatusoutput(lilo_command)
                    if 0 in output :
                        info_dialog(_("The installation of your new LILO bootloader was succesful. You can now exit LiloSetup and reboot your computer.\n"))
                        self.ExecuteButton.set_sensitive(False)
                    else:
                        error_dialog(_("The installation of your new LILO bootloader failed. Please verify /var/log/lilosetup.log, modify your settings and try again.\n"))
                        self.ExecuteButton.set_sensitive(False)
                if result_warning == gtk.RESPONSE_NO:
                    pass

if __name__ == '__main__':
    # Checks for root privileges
    if os.getuid() != 0:
        error_dialog(_("<b>Sorry!</b> \n\nRoot privileges are required to run LiloSetup. "))
        sys.exit(1)
    # Executes the main program
    LiloSetup()
    gtk.main()
