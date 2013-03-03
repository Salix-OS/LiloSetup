#!/usr/bin/env python

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#                                                                             #
# LiloSetup - GTK frontend to setup lilo, from a LiveCD or a standard system. #
#                                                                             #
# Copyright (c) Pierrick Le Brun <akuna~at~salixos~dot~org>.                  #
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

application_name = 'lilosetup'
application_version = '0.4'
application_copyright = u"Copyright \u00A9 2010-2013 Pierrick Le Brun"
 
import commands
import glob
import gtk
import gtk.glade
import os
import shutil
import subprocess
import sys

from gettext import gettext as _
import locale
locale.setlocale(locale.LC_ALL, "")

import lilosetup_modules as selflib

# Initialize key mountpoints value
try :
    root_device_uuid = commands.getoutput('blkid /dev/root').split()[1].split('"')[1]
except IndexError :
    root_device_uuid = 'none'

### Cleanup eventual remnants from previous use of LiloSetup ###
selflib.initial_cleanup()

# Retrieve the boot device with the MBR that will host LILO
# Preferably the first hard drive having a partition with a boot flag,
boot_partition = commands.getoutput('fdisk -l | grep "^/dev" | grep "*" -m 1 | cut -f1 -d " "').rstrip('0123456789')
# Else, just the first hard drive
if boot_partition == "" :
    boot_partition = commands.getoutput('fdisk -l | grep "^/dev" -m 1 | cut -f1 -d " "').rstrip('0123456789')
# Generate a stub for LiloSetup configuration file 
selflib.purge_old_stub(selflib.stub_location)
selflib.generate_new_stub(selflib.stub_location, boot_partition)

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
        self.AboutDialog.set_version(application_version)
        self.AboutDialog.set_copyright(application_copyright)
        self.BootPartitionTreeview = builder.get_object("boot_partition_treeview")
        self.BootPartitionListStore = builder.get_object("boot_partition_list_store")
        self.EditButton = builder.get_object("edit_button")
        self.UndoButton = builder.get_object("undo_button")
        self.ExecuteButton = builder.get_object("execute_button")
        self.UpButton = builder.get_object("up_button")
        self.DownButton = builder.get_object("down_button")
        self.LabelCellRendererCombo = builder.get_object("label_cellrenderercombo")
        self.PartitionTreeViewColumn = builder.get_object("partition_treeviewcolumn")
        self.FileSystemTreeViewColumn = builder.get_object("filesystem_treeviewcolumn")
        self.OsTreeViewColumn = builder.get_object("os_treeviewcolumn")
        self.LabelTreeViewColumn = builder.get_object("label_treeviewcolumn")
        self.LabelContextHelp = builder.get_object("label_context_help")

        # Connect signals
        builder.connect_signals(self)

        # Set the column names
        self.PartitionTreeViewColumn.set_title(_('Partition'))
        self.FileSystemTreeViewColumn.set_title(_('File system'))
        self.OsTreeViewColumn.set_title(_('Operating system'))
        self.LabelTreeViewColumn.set_title(_('Boot menu label'))

        # Initialize the contextual help box
        global context_intro
        context_intro = _("<b>LiloSetup will install a new LILO bootloader on your computer.</b> \n\
\n\
A bootloader is required to load the main operating system of a computer and will initially display \
a boot menu if several operating systems are available on the same computer.")
        self.LabelContextHelp.set_markup(context_intro)

        # Set the appropriate framebuffer in the configuration file stub
        current_framebuffer = selflib.detect_fb()
        if current_framebuffer:
            selflib.set_fb(current_framebuffer, selflib.stub_location)
        # If framebuffer is not available, then failsafe to vga-normal
        else:
            selflib.failsafe_fb(selflib.stub_location)

        ### Initialize the partition list ###
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
            # Get a list of all partitions
            blkid_list = commands.getoutput('blkid -c /dev/null | grep -iv recovery | grep -v ' + root_device_uuid + ' | grep -v swap').splitlines()
            for i in blkid_list :
                partition = i.split(':')[0]
                try :
                    partition_device, file_system, operating_system = selflib.check_if_bootable(partition)
                    boot_partition_feedline = [partition_device, file_system, operating_system, boot_label]
                    boot_partition_feedline_list.append(boot_partition_feedline)
                except TypeError :
                    pass # this is not a bootable partition
            # Add the main partition of the os we are in
            blkid_global_output = commands.getoutput('blkid')
            if root_device_uuid != 'none' : # In which case we could otherwise be in a LiveCD
                root_device = commands.getoutput('blkid | grep ' + root_device_uuid).split(':')[0]
                for line in blkid_global_output.splitlines() :
                    if root_device_uuid in line :
                        # Check that it is a 'non-loop' device and that we are indeed in a non-live environment
                        if root_device != "/dev/root" :
                            # Yes, we are in a non-live environment, we need to add that partititon to lilosetup view
                            break # we break this process so that we can go on with adding it
                        else : # we are in a LiveCD , no need to add root
                            pass # so we do nothing & check the next partition
                if root_device != "/dev/root" : # Keep that extra check to ensure there will be no double entries
                    # Get the file system
                    string_output = commands.getoutput('blkid | grep ' + root_device_uuid + ' | grep -m 1 TYPE')
                    file_system = string_output.split()[-1].split('"')[1]
                    # Get the operating system.
                    try :
                        version_file_path = glob.glob("/etc/*version*")[0]
                        version_file = open(version_file_path)
                        operating_system = version_file.read().split()[0]
                        version_file.close()
                    except :
                        operating_system = "Unknown"
                    # Put it all together
                    boot_partition_feedline = [root_device, file_system, operating_system, boot_label]
                    boot_partition_feedline_list.append(boot_partition_feedline)
                else: # We probably are in a LiveCD environment.
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
            Populate lilosetup.conf & mounts needed partition(s) to lilo's chrooted partition.
            """
            shutil.copy(selflib.stub_location, selflib.configfile_location)
            # Re-initialize key variables
            # Temporary mountpoint list
            del selflib.temp_mount[:]
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
                windows_sys_labels = ['Microsoft', 'Windows']
                # We skip the partitions that have not been configured by the user
                if _('Set...') in set[3] :
                    pass
                # If Windows partition:
                elif set[2] in windows_sys_labels :
                    # Append to lilosetup.conf
                    stub = open(selflib.configfile_location, "a")
                    stub.write("#\n")
                    stub.write(_("# Windows bootable partition config begins\n"))
                    stub.write("other = " + set[0] + "\n")
                    stub.write("label = " + set[3] + "\n")
                    stub.write(_("# Windows bootable partition config ends\n"))
                    stub.close()
                else:
                    # Applies to Linux partitions
                    # Let's determines Lilo's chrooted Linux partition directory, only happens one.
                    am_i_first = 'cat ' + selflib.configfile_location + ' | grep -i uuid'
                    already_done = commands.getoutput(am_i_first).splitlines()
                    if already_done == []:
                        # This is the first Linux partition, the one we will chroot in to launch lilo!
                        chroot_dev = set[0]
                        mount_inconf = '' # Defines how the partitions 'appears' mounted from the 'chrooted' partition's viewpoint
                        other_mnt = '' # we need this blank for the first Linux partition
                        # Check if lilo's chroot directory is mounted
                        CHROOT_MNT="mount | grep -v \/mnt\/live | grep " + chroot_dev + " | awk -F' ' '{print $3 }'"
                        selflib.chroot_mnt = commands.getoutput(CHROOT_MNT) # chrooted partition mountpoint
                        if selflib.chroot_mnt == '' :
                            # Either it is not mounted or else it is used as the current root filesystem (/) but linked to /dev/root
                            check_if_root = commands.getoutput("ls -l /dev/root | grep " + chroot_dev.replace("/dev/", ""))
                            if check_if_root in chroot_dev :
                                # The link leads to the 'chrooted' device, it is the current file system.
                                selflib.chroot_mnt = "/"
                            else :
                                # It is not mounted, let's create a temporary mountpoint ourselves
                                selflib.temp_chroot_mnt = selflib.work_dir + chroot_dev.replace('dev', 'mnt')
                                try:
                                    os.makedirs(selflib.temp_chroot_mnt)
                                except OSError :
                                    pass                               
                                # Mount the 'chrooted' partition
                                chroot_mnt_command = "mount " + chroot_dev + " " + selflib.temp_chroot_mnt + " 2>/dev/null"
                                subprocess.call(chroot_mnt_command, shell=True)
                                selflib.chroot_mnt = selflib.temp_chroot_mnt
                        if selflib.chroot_mnt != "/" :
                            # This is necessary only if we execute lilo from a 'real' chrooted partition
                            subprocess.call("mount --bind /dev " + selflib.chroot_mnt + "/dev 2>/dev/null", shell=True)
                            selflib.temp_mount.append(selflib.chroot_mnt + "/dev") # allows unmounting temporary mountpoints later
                            subprocess.call("mount -t proc proc " + selflib.chroot_mnt + "/proc 2>/dev/null", shell=True)
                            selflib.temp_mount.append(selflib.chroot_mnt + "/proc") # allows unmounting temporary mountpoints later
                    else : # This applies to all subsequent partitions
                        # How this partition is --or should be-- mounted on a the current partition
                        if selflib.chroot_mnt == "/" :
                            mount_info=commands.getoutput("mount").splitlines()
                            while mount_info:
                                if set[0] in mount_info[0]:
                                    other_mnt = mount_info[0].split()[2]
                                mount_info.remove(mount_info[0])
                            if other_mnt == '':
                                # We need to create a temporary mountpoint ourself & mount it:
                                temp_other_mnt = selflib.work_dir + set[0].replace('dev', 'mnt')
                                try :
                                    os.makedirs(temp_other_mnt)
                                    selflib.temp_dir.append(temp_other_mnt)
                                except OSError :
                                    pass
                                other_mnt = temp_other_mnt
                                # all needed temporary mountpoints on chrooted partitions exist, we can now mount them
                                mnt_command = "mount " + set[0] + " " + other_mnt + " 2>/dev/null"
                                subprocess.call(mnt_command, shell=True)
                                selflib.temp_mount.append(other_mnt) # allows cleanup temporary mountpoints later
                        # Else, how this partition should (and will) be mounted on a 'real' chrooted partition
                        else :
                            other_mnt = '' # reinitialization
                            # We create a fork, chroot in the child process & pipe the mount info to the parent process
                            # If lilosetup is executed from a 32bit environment it can't chroot to a 64bit environment.
                            if os.path.isdir('/lib64') is not True and os.path.isdir(selflib.chroot_mnt + '/lib64') is True:
                                pass
                            else :
                                r, w = os.pipe() # these are file descriptors, not file objects
                                pid = os.fork()
                                if pid:
                                    selflib.chroot_mnt     # Parent process
                                    os.close(w) # use os.close() to close a file descriptor
                                    r = os.fdopen(r) # turn r into a file object
                                    other_mnt = r.read()
                                    os.waitpid(pid, 0) # make sure the child process gets cleaned up
                                else:
                                    # Child process
                                    os.close(r)
                                    w = os.fdopen(w, 'w')
                                    os.chroot(selflib.chroot_mnt)
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
                                temp_other_mnt = selflib.work_dir + set[0].replace('dev', 'mnt')
                                try :
                                    os.makedirs(selflib.chroot_mnt + temp_other_mnt)
                                    selflib.temp_dir.append(selflib.chroot_mnt + temp_other_mnt)
                                except OSError :
                                    pass
                                other_mnt = temp_other_mnt
                            # all needed temporary mountpoints on chrooted partitions exist, we can now mount them
                            mnt_command = "mount " + set[0] + " " + selflib.chroot_mnt + other_mnt + " 2>/dev/null"
                            subprocess.call(mnt_command, shell=True)
                            selflib.temp_mount.append(selflib.chroot_mnt +other_mnt) # allows cleanup temporary mountpoints later
                    mount_inconf = other_mnt	# defines how the partition 'appears' mounted in lilosetup.conf
                    # Confirm that the partition is configured
                    selflib.partition_set.append("OK")
                    # Append to lilosetup.conf
                    stub = open(selflib.configfile_location, "a")
                    # There maybe a few kernels in the same partition
                    # Some of them may have an initrd, which we assume have exactly the same suffix.
                    if selflib.chroot_mnt != "/":
                        vmlist = sorted(glob.glob(selflib.chroot_mnt + other_mnt + "/boot/vmlinuz*"))
                        initlist = sorted(glob.glob(selflib.chroot_mnt + other_mnt + "/boot/initr*"))
                    if selflib.chroot_mnt == "/":
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
                             selflib.error_dialog(_("One of your partitions does not seem to hold a valid kernel file. Please verify and correct LiloSetup configuration file manually.\n"))
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
    def on_up_eventbox_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Use this arrow if you want to move the \
selected Operating System up to a higher rank.\n\
The partition with the highest rank will be displayed on the first line of the bootloader menu.\n\
Any of these settings can be edited manually in lilosetup configuration file."))
    def on_up_eventbox_leave_notify_event(self, widget, data=None):
        global context_intro
        self.LabelContextHelp.set_markup(context_intro)
    def on_down_eventbox_enter_notify_event(self, widget, data=None):
        self.LabelContextHelp.set_markup(_("Use this arrow if you want to move the \
selected Operating System down to a lower rank.\n\
The partition with the lowest rank will be displayed on the last line of the bootloader menu.\n\
Any of these settings can be edited manually in lilosetup configuration file."))
    def on_down_eventbox_leave_notify_event(self, widget, data=None):
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
        selflib.lilosetup_quit()

    # What to do when the quit button is is clicked
    def on_main_window_destroy(self, widget, data=None):
        selflib.lilosetup_quit()

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

        # We ensure there are no identical labels
        if any(new_text in item for item in selflib.already_there) :
            for item in selflib.already_there[:] :
                # The user could change his mind and leave a label unchanged after starting edition, in which case we shouldn't warn him
                if (row_number,new_text) in selflib.already_there :
                    break
                else :
                    selflib.error_dialog(_("You have used the same label for different Operating Systems. Please verify and correct.\n"))
                    # Remove the item from the list if it already set before setting back to default
                    try :
                        selflib.already_there.remove((row_number,new_text))
                    except ValueError :
                        pass
                    # Reset the default value of the label
                    self.BootPartitionListStore.set_value(iter, 3, _("Set..."))
                    self.BootPartitionListStore.set_value(iter, 4, 'gtk-edit')
                    # Re-enables buttons if there are other valid entries
                    if selflib.already_there != [] :
                        self.UndoButton.set_sensitive(True)
                        self.EditButton.set_sensitive(True)
                        self.ExecuteButton.set_sensitive(True)
                        self.UpButton.set_sensitive(True)
                        self.DownButton.set_sensitive(True)
                    break

        # We need to ensure that the labels do not contain empty space
        elif ' ' in new_text :
            selflib.error_dialog(_("\nAn Operating System label should not contain any space. \n\nPlease verify and correct.\n"))

        # We ensure that the label is less than 15 characters long
        elif len(new_text) > 15 :
            selflib.error_dialog(_("\nAn Operating System label should not hold more than 15 characters. \n\nPlease verify and correct.\n"))

        else:
            # Allow for successive editing of the same partition
            for item in selflib.already_there[:] :
                if row_number in item :
                    selflib.already_there.remove(item)
            if new_text != _("Set..."):
                selflib.already_there.append((row_number,new_text))

            # Set the new partition row value on the fourth column (3)
            self.BootPartitionListStore.set_value(iter, 3, new_text)
            if new_text != _("Set..."):
                self.BootPartitionListStore.set_value(iter, 4, 'gtk-yes')
            else:
                self.BootPartitionListStore.set_value(iter, 4, 'gtk-edit')
            # Re-enables buttons if there are other valid entries
            if selflib.already_there != [] :
                self.UndoButton.set_sensitive(True)
                self.EditButton.set_sensitive(True)
                self.ExecuteButton.set_sensitive(True)
                self.UpButton.set_sensitive(True)
                self.DownButton.set_sensitive(True)

    def on_label_cellrenderercombo_editing_started(self, widget, path, data):
        self.UndoButton.set_sensitive(False)
        self.EditButton.set_sensitive(False)
        self.ExecuteButton.set_sensitive(False)
        self.UpButton.set_sensitive(False)
        self.DownButton.set_sensitive(False)

    def on_label_cellrenderercombo_editing_canceled(self, data):
        self.UndoButton.set_sensitive(False)
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
        self.EditButton.set_sensitive(False)
        self.UndoButton.set_sensitive(False)
        self.ExecuteButton.set_sensitive(False)
        self.UpButton.set_sensitive(False)
        self.DownButton.set_sensitive(False)
        self.BootPartitionTreeview.get_selection().unselect_all()
        self.BootPartitionTreeview.set_sensitive(True)
        del selflib.already_there[:]
        selflib.lilosetup_undo()
        setup_partition_list()
            
    def on_edit_button_clicked(self, widget, data=None):
        """
        Opens the edit lilosetup.conf dialog.
        """
        # Check if the configuration file has already beeen created
        if os.path.isfile(selflib.configfile_location) == False :
            create_configuration()
        try :
            if os.path.isfile("/usr/bin/mousepad") :
                subprocess.call('/usr/bin/mousepad ' + selflib.configfile_location + ' 2>/dev/null', shell=True)
            elif os.path.isfile("/usr/bin/leafpad") :
                subprocess.call('/usr/bin/leafpad ' + selflib.configfile_location + ' 2>/dev/null', shell=True)
            elif os.path.isfile("/usr/bin/gedit") :
                subprocess.call('/usr/bin/gedit ' + selflib.configfile_location + ' 2>/dev/null', shell=True)
            elif os.path.isfile("/usr/bin/kwrite") :
                subprocess.call('/usr/bin/kwrite ' + selflib.configfile_location + ' 2>/dev/null', shell=True)
            elif os.path.isfile("/usr/bin/geany") :
                subprocess.call('/usr/bin/geany ' + selflib.configfile_location + ' 2>/dev/null', shell=True)
            else :
                subprocess.call('xdg-open ' + selflib.configfile_location + ' 2>/dev/null', shell=True)
            # Ensure changes are taken into account
            subprocess.call('sync', shell=True)
            subprocess.call('rm -f ' + selflib.configfile_location + '~ 2>/dev/null', shell=True)
            self.UpButton.set_sensitive(False)
            self.DownButton.set_sensitive(False)
            self.ExecuteButton.set_sensitive(True)
            self.BootPartitionTreeview.get_selection().unselect_all()
            self.BootPartitionTreeview.set_sensitive(False)
        except :
            self.EditButton.set_sensitive(False)
            selflib.error_dialog(_("Sorry, LiloSetup is unable to find a suitable text editor in your system. You will not be able to manually modify LiloSetup configuration.\n"))

    def on_execute_button_clicked(self, widget, data=None):
        # Check if the configuration file has already beeen created
        if os.path.isfile(selflib.configfile_location) == False :
            create_configuration()
        # Check if at least one Linux partition has been configured:
        if selflib.partition_set == [] :
            selflib.error_dialog(_("Your configuration is not complete. Please, select at least one Linux booting partition and define its Boot menu label.\n"))
            self.UndoButton.clicked()
        else:
            selflib.warning_dialog(_("You are about to install a new LILO bootloader. Are you sure you want to continue?"))
            if selflib.response_to_warning[0] == gtk.RESPONSE_YES:
                # If previous lilosetup.conf file exist, save it as lilosetup.old
                if os.path.isfile(selflib.chroot_mnt + "/etc/lilosetup.conf") == True :
                    os.rename(selflib.chroot_mnt + "/etc/lilosetup.conf", selflib.chroot_mnt +'/etc/lilosetup.old')
                shutil.copy(selflib.configfile_location, selflib.chroot_mnt + "/etc/lilosetup.conf")
                # Copy /boot/salix graphics to selflib.chroot_mnt if needed
                if os.path.isfile(selflib.chroot_mnt + "/boot/salix.bmp") == False :
                    if os.path.isfile("/boot/salix.bmp") == True :
                        shutil.copy("/boot/salix.bmp", selflib.chroot_mnt + "/boot/salix.bmp")
                    elif os.path.isfile("/mnt/live/memory/images/01-core.lzm/boot/salix.bmp") == True :
                        shutil.copy("/mnt/live/memory/images/01-core.lzm/boot/salix.bmp", selflib.chroot_mnt + "/boot/salix.bmp")
                # Execute Lilo
                lilo_command = "lilo -v -r " + selflib.chroot_mnt + " -C /etc/lilosetup.conf > /var/log/lilosetup.log"
                output = commands.getstatusoutput(lilo_command)
                if 0 in output :
                    selflib.info_dialog(_("The installation of your new LILO bootloader was succesful. You can now exit LiloSetup and reboot your computer.\n"))
                    self.ExecuteButton.set_sensitive(False)
                else:
                    selflib.error_dialog(_("The installation of your new LILO bootloader failed. Please verify /var/log/lilosetup.log, modify your settings and try again.\n"))
                    self.ExecuteButton.set_sensitive(False)
            if selflib.response_to_warning[0] == gtk.RESPONSE_NO:
                pass

if __name__ == '__main__':
    # If no root privilege, displays the  version, an error message and then exit
    if os.getuid() != 0:
        selflib.error_dialog(_("<b>Sorry!</b>\n\nRoot privileges are required to run this program."))
        print application_name + ', version ' + application_version
        sys.exit(1)
    # Otherwise, displays the version and the GUI, and then wait for signal
    print application_name + ', version ' + application_version
    LiloSetup()
    gtk.main()
