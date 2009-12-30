#!/usr/bin/env python

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#                                                                             #
# LiloSetup - GTK frontend to setup lilo, from a LiveCD or a standard system. #
#                                                                             #
# Copyright Pierrick Le Brun <akuna at free.fr>.                              #
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

# version = '0.1' - 20091229 build -    Forked LiloFix '0.9.7' to Salix environment
#                                       Modified name, logo, gui & lilosetup.conf stub
#                                       Migrated from libglade to gtkbuilder
#                                       Added extra info columns to the boot partition list
#                                       Switched to os-prober & lshal for booting partitions details
#                                       Added initrd autodetection
#                                       Added support for multiple kernels within the same partition
#                                       Adapt syntax if target kernel is using LIBATA

# To Do => Refine OS name detection
# To Do => Verify internationalization process with gtkbuilder
# To Do => Verify Raid device support

import shutil
import subprocess
import os
import sys
import commands
import glob
import gtk
import gtk.glade

# Internationalization (unchanged from libglade, to verify)
import locale
import gettext
locale.setlocale(locale.LC_ALL, "")
gettext.bindtextdomain("lilosetup", "../share/locale")
gettext.textdomain("lilosetup")
gettext.install("lilosetup", "../share/locale", unicode=1)
gtk.glade.bindtextdomain("lilosetup", "../share/locale")
gtk.glade.textdomain("lilosetup")

# The following 4 functions were borrowed from ndisgtk 
# The study of ndisgtk code taught me a lot when I first explored python/glade3 ;)

# Info window skeleton:
def info_dialog(message, parent = None):
    """
    Displays an information message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK, flags = gtk.DIALOG_MODAL)
    dialog.set_icon_from_file("/usr/share/icons/gnome/scalable/status/dialog-information.svg")
    dialog.set_markup(message)
    global result_info
    result_info = dialog.run()
    dialog.destroy()

# Warning window skeleton:
def warning_dialog(message, parent = None):
    """
    Displays a warning message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_WARNING, buttons = gtk.BUTTONS_NONE, flags = gtk.DIALOG_MODAL)
    dialog.set_icon_from_file("/usr/share/icons/gnome/scalable/status/dialog-warning.svg")
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
    Displays an error message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_CLOSE, flags = gtk.DIALOG_MODAL)
    dialog.set_icon_from_file("/usr/share/icons/gnome/scalable/status/dialog-error.svg")
    dialog.set_markup(message)
    global result_error
    result_error = dialog.run()
    dialog.destroy()

# Output of bash commands :
def run_bash(cmd):
    """
    Takes bash commands and returns the output.
    
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read().strip()
    return out  #This is the stdout from the shell command
    
# Create LiloSetup temporary work directory
global work_dir
work_dir = "/tmp/lilosetup/"
shutil.rmtree(work_dir, ignore_errors=True)
os.mkdir(work_dir)

# initialize some lists
temp_mount = []

# Build LiloSetup configuration file stub:
def build_lilosetupconf_stub():

    boot_partition = commands.getoutput('os-prober').splitlines()[0].split(':')[0].strip('0123456789')

    global stub_location
    stub_location = work_dir + "lilosetup.conf"

    stub = open(stub_location, "w")
    stub.write(_("# LILO configuration file\n"))
    stub.write(_("# Generated by LiloSetup\n"))
    stub.write("#\n")
    stub.write(_("# Start LILO global section\n"))
    stub.write(_("# Append any additional kernel parameters:\n"))
    stub.write('append = "quiet vt.default_utf8=1 "\n')
    stub.write("boot = " + boot_partition + "\n")
    stub.write("\n")
    stub.write(_("# Boot BMP Image.\n"))
    stub.write(_("# Bitmap in BMP format: 640x480x8\n"))
    stub.write("  bitmap = /boot/salix.bmp\n")
    stub.write(_("# Menu colors (foreground, background, shadow, highlighted\n"))
    stub.write(_("# foreground, highlighted background, highlighted shadow):\n"))
    stub.write("  bmp-colors = 255,20,255,20,255,20\n")
    stub.write(_("# Location of the option table: location x, location y, number of\n"))
    stub.write(_('# columns, lines per column (max 15), "spill" this is how many\n'))
    stub.write(_("# entries must be in the first column before the next begins to\n"))
    stub.write(_("# be used.  We don't specify it here, as there's just one column.\n"))
    stub.write("  bmp-table = 60,6,1,16\n")
    stub.write(_("# Timer location x, timer location y, foreground color,\n"))
    stub.write(_("# background color, shadow color.\n"))
    stub.write("  bmp-timer = 65,29,0,255\n")
    stub.write("\n")
    stub.write(_("# Standard menu.\n"))
    stub.write(_("# Or, you can comment out the bitmap menu above and \n"))
    stub.write(_("# use a boot message with the standard menu:\n"))
    stub.write("# message = /boot/boot_message.txt\n")
    stub.write("\n")
    stub.write(_("# Wait until the timeout to boot (if commented out, boot the\n"))
    stub.write(_("# first entry immediately):\n"))
    stub.write("prompt\n")
    stub.write(_("# Timeout before the first entry boots.\n"))
    stub.write(_("# This is given in tenths of a second, so 600 for every minute:\n"))
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
    stub.write(_("# LiloSetup can be executed from a LiveCD. This means that lilo\n"))
    stub.write(_("# will be issued from a 'chrooted' Linux partition, which will\n"))
    stub.write(_("# happen to be the first Linux partition listed below.\n"))
    stub.write(_("# Therefore the following paths are relevant only when viewed\n"))
    stub.write(_("# from that 'chrooted' partition's perspective. Please take this\n"))
    stub.write(_("# constraint into consideration if you must modify this file\n"))
    stub.write(_("# or else LiloSetup will fail.\n"))
    stub.close()

    # Let's set the appropriate framebuffer...
    # Setting bash environment variable
    os.environ['stubfile'] = stub_location

    # This function gives a failsafe option in case of trouble with framebuffer:
    def failsafe_fb():

        FBLINE= """
        cat $stubfile | grep "vga = normal" -m 1 -n | cut -f1 -d :
        """
        fbline = run_bash(FBLINE)
        os.environ['editline'] = fbline
        set_framebuffer = "sed $editline's/# //' -i $stubfile"
        subprocess.call(set_framebuffer, shell=True)

    # We first check if framebuffer is available
    try :
        USEDFB = """
        fbset | grep -w mode | cut -f2 -d " " | cut -f1 -d "-" | sed 's/"//'
        """
        os.environ['setfb'] = run_bash(USEDFB)
        # We also need to make sure that the adequate framebuffer resolution is in the stub
        FBLINE= """
        cat $stubfile | grep "@ $setfb" -m 1 -n | cut -f1 -d :
        """
        fbline = run_bash(FBLINE)
        if fbline != '' :
            fblineplus = int(fbline) + 1
            os.environ['editline'] = repr(fblineplus)
            set_framebuffer = "sed $editline's/# //' -i $stubfile"
            subprocess.call(set_framebuffer, shell=True)
        # If no fitting resolution is available from the stub then failsafe to vga-normal
        else :
            failsafe_fb()

    # If framebuffer is not available, we can use failsafe option again
    except :
        failsafe_fb()

def lilosetup_quit():
    """
    Closes LiloSetup window, cleanup temp files & unmount temp system.
    """
    shutil.rmtree(work_dir, ignore_errors=True)
    if temp_mount :
        for i in temp_mount :
            subprocess.call("umount -f " + i + " 2>/dev/null", shell=True)
            try:
                os.rmdir(i)
            except:
                pass
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
        self.CreateButton = builder.get_object("create_button")
        self.DeleteButton = builder.get_object("delete_button")
        self.ExecuteButton = builder.get_object("execute_button")
        self.LabelCellRendererCombo = builder.get_object("label_cellrenderercombo")
        self.BootLabelListStore = builder.get_object("boot_label_list_store")
        self.LabelTreeViewColumn = builder.get_object("label_treeviewcolumn")
        self.BootPartitionTreeview = builder.get_object("boot_partition_treeview")
        self.RankCellRendererCombo = builder.get_object("rank_cellrenderercombo")
        self.BootRankListStore = builder.get_object("boot_rank_list_store")
        self.RankTreeViewColumn = builder.get_object("rank_treeviewcolumn")
        self.BootPartitionListStore = builder.get_object("boot_partition_list_store")
        # Connect signals
        builder.connect_signals(self)

        # Initialize the partition list
        def setup_partition_list():
            """
            Sets up the partition list.
            """
            # We need to get the file system of all devices whether mounted or not
            # Start on a clean slate
            self.BootPartitionListStore.clear()
            # Initialize the different variables
            boot_partition_feedline_list = []
            partition_device = ''
            file_system = ''
            operating_system = ''
            boot_label = 'Set...'
            boot_rank = int(0)
            boot_partition_feedline = []
            boot_partition_output = commands.getoutput('os-prober').splitlines()
            for line in boot_partition_output:
                # Get the partition device
                partition_device = line.split(':')[0]
                # Check that it is not a Windows factory settings recovery partition...
                lshal_recovery_output = 'lshal | grep -B1 -A30 ' + partition_device + ' | grep -i recovery'
                partition_is_recovery = commands.getoutput(lshal_recovery_output)
                if partition_is_recovery == '' :
                    # Get the operating system
                    operating_system = line.split(':')[1].split()[0]
                    # TODO Refine OS recognition
                    if 'Slackware' in operating_system :
                        pass # Simply parse /etc/*version* in that mounted partition
                    # Get the file system
                    lshal_string_output = 'lshal | grep -B1 -A30 ' + partition_device + ' | grep volume.fstype'
                    file_system = commands.getoutput(lshal_string_output).split("'")[1]
                    boot_partition_feedline = [partition_device, file_system, operating_system, boot_label, boot_rank]
                    boot_partition_feedline_list.append(boot_partition_feedline)
                else:
                    pass
            # Add the main partition of the os we are in ( partition mounted on / is not taken care by os-prober)
            os.putenv("root_partition", "\'/\'")
            this_os_main_partition = commands.getoutput("lshal | grep -B33  $root_partition | grep block.device").split("'")[1]
            if '/dev/' in this_os_main_partition:
                # Get the partition device
                partition_device = this_os_main_partition
                # Get the file system
                lshal_string_output = 'lshal | grep -B1 -A30 ' + partition_device + ' | grep volume.fstype'
                file_system = commands.getoutput(lshal_string_output).split("'")[1]
                # Get the operating system.
                try :
                    version_file_path = glob.glob("/etc/*version")[0]
                    version_file = open(version_file_path)
                    operating_system = version_file.read().split()[0]
                except :
                    operating_system = "Unknown"
                # Put it all together
                boot_partition_feedline = [partition_device, file_system, operating_system, boot_label, boot_rank]
                boot_partition_feedline_list.append(boot_partition_feedline)
            else:
                pass
            # Insert Menu Label editable combobox
            self.LabelCellRendererCombo.set_property("model", self.BootLabelListStore)
            self.LabelCellRendererCombo.set_property('text-column', 0)
            self.LabelCellRendererCombo.set_property('editable', True)
            self.LabelTreeViewColumn.set_attributes(self.LabelCellRendererCombo, text = 3)
            # Insert Menu Rank editable combobox
            self.RankCellRendererCombo.set_property("model", self.BootRankListStore)
            self.RankCellRendererCombo.set_property('text-column', 0)
            self.RankCellRendererCombo.set_property('editable', True)
            self.RankTreeViewColumn.set_attributes(self.RankCellRendererCombo, text = 4)
            # Sort the list for the partitions who do not follow the hard drive order
            boot_partition_feedline_list.sort()
            # Populate GUI partition list view rows
            for line in boot_partition_feedline_list:
                self.BootPartitionListStore.append(line)
        # Show partition list
        setup_partition_list()

### Callback signals waiting in a constant loop: ###

### WINDOWS MAIN SIGNALS ###	

    # What to do when the exit X on the main window upper right is clicked
    def gtk_main_quit(self, widget, data=None):
        lilosetup_quit()

# What to do when the quit button is is clicked    
    def on_main_window_destroy(self, widget, data=None):
        lilosetup_quit()

    def on_about_button_clicked(self, widget, data=None):
        """
        Opens the about dialog.
        """
        self.AboutDialog.show()

    def on_about_dialog_close(self, widget, data=None):
        """
        Closes the about dialog.
        """
        self.AboutDialog.hide()
        return True;

    # What to do when a combo line is edited in the Linux New system column
    def on_label_cellrenderercombo_edited(self, widget, row_number, new_text):
        # Retrieve the selected label row iter
        bootlabelchoice = self.BootPartitionTreeview.get_selection()
        self.BootLabelListStore, iter = bootlabelchoice.get_selected()
        # Set the new partition row value on the fourth column (3)
        self.BootLabelListStore.set_value(iter, 3, new_text)

    # What to do when a combo line is edited in the Linux Rank column
    def on_rank_cellrenderercombo_edited(self, widget, row_number, new_text):
        # Retrieve the selected label row iter
        bootrankchoice = self.BootPartitionTreeview.get_selection()
        self.BootRankListStore, iter = bootrankchoice.get_selected()
        # Set the new partition row value on the fifth column (4)
        self.BootRankListStore.set_value(iter, 4, new_text)

    def on_create_button_clicked(self, widget, data=None):
        """
        Called when the 'Create configuration file' button is clicked.

        Populate lilosetup.conf & mounts needed partition to lilo's chrooted partition.
        """
        build_lilosetupconf_stub()
        # This will help us to ensure at least one partition has been configured
        partition_set = []
        # Retrieve all the partition rows values
        BootPartitionsValues = []
        x = 0
        while x <= 20 :
            try :
                treeiter = self.BootPartitionListStore.get_iter(x)
                x += 1
                BootPartitionsValues.append(self.BootPartitionListStore.get(treeiter, 4, 0, 1, 2, 3))
            except (ValueError) :
                break
        # First we need to order the sets by ranks
        BootPartitionsValues.sort()
        for set in BootPartitionsValues	:
            # We need to ensure that the labels are unique and do not contain empty space
            if ' ' in set[4] :
                error_dialog("\nAn Operating System label should not contain any space. \n\nPlease verify and correct! \n")
                self.EditButton.set_sensitive(False)
                self.CreateButton.set_sensitive(True)
                self.ExecuteButton.set_sensitive(False)
                self.BootPartitionTreeview.set_sensitive(True)
                break
            # We skip the partitions that have not been configured by the user
            elif '...' in set[4] :
                pass
            # We ensure there are no identical labels
            else :
                am_i_there = 'cat ' + stub_location + ''' | grep -w label | cut -f3 -d " " '''
                already_there = commands.getoutput(am_i_there).splitlines()
                if set[4] in already_there :
                    error_dialog(_("You have used the same label for different Operating Systems. Please verify and correct."))
                    self.EditButton.set_sensitive(False)
                    self.CreateButton.set_sensitive(True)
                    self.ExecuteButton.set_sensitive(False)
                    self.BootPartitionTreeview.set_sensitive(True)
                    break
                # Let's determines Lilo's chrooted Linux partition directory, only happens once.
                am_i_first = 'cat ' + stub_location + ''' | grep -v other | grep \/dev\/ | grep -w '.d.[1-9]' | cut -f3 -d " " '''
                already_done = commands.getoutput(am_i_first).splitlines()
                if already_done == []: # This is the first Linux partition, the one we will chroot into to launch lilo!
                    chroot_dev = set[1]
                    # we check how lilo's chroot directory is supposed to be mounted
                    CHROOT_MNT="cat /etc/fstab | grep " + chroot_dev + " | awk -F' ' '{print $2 }'"
                    global chroot_mnt # we will need global access to this info
                    chroot_mnt = commands.getoutput(CHROOT_MNT) # chrooted partition mountpoint
                    if chroot_mnt == '' : # we need to create a temporary mountpoint ourselves
                        temp_chroot_mnt = chroot_dev.replace('dev', 'mnt')
                        os.mkdir(temp_chroot_mnt)
                        temp_mount.append(temp_chroot_mnt) # allows cleanup temporary mountpoints later
                        chroot_mnt = temp_chroot_mnt
                    # let's mount the 'chrooted' partition, just in case
                    chroot_mnt_command = "mount " + chroot_dev + " " + chroot_mnt + " 2>/dev/null"
                    subprocess.call(chroot_mnt_command, shell=True)
                    mount_inconf = ''	# defines how the partition 'appears' mounted in lilosetup.conf
                    global other_mnt
                    other_mnt = '' # we need this blank for the first time
                else :	# This applies to all subsequent partitions
                    # we check how this partition should be mounted on the chrooted partition
                    OTHER_MNT="cat " + chroot_mnt + "/etc/fstab | grep " + set[1] + " | awk -F' ' '{print $2 }'"
                    other_mnt = commands.getoutput(OTHER_MNT) # partition mountpoint
                    if other_mnt == '':  # we need to create a temporary mountpoint ourselves
                        temp_other_mnt = set[1].replace('dev', 'mnt')
                        # just to be safe let's try to unmount it first
                        umnt_command = "umount -f "  + chroot_mnt + temp_other_mnt + " 2>/dev/null"
                        subprocess.call(umnt_command, shell=True)
                        try:
                            os.rmdir(chroot_mnt + temp_other_mnt)
                        except:
                            pass
                        os.mkdir(chroot_mnt + temp_other_mnt)
                        temp_mount.append(chroot_mnt + temp_other_mnt) # allows cleanup temporary mountpoints later
                        other_mnt = temp_other_mnt
                    # let's also mount this partition, just in case
                    mnt_command = "mount " + set[1] + " " + chroot_mnt + other_mnt + " 2>/dev/null"
                    subprocess.call(mnt_command, shell=True)
                    mount_inconf = other_mnt	# defines how the partition 'appears' mounted in lilosetup.conf
                # If Windows partition:
                windows_sys_labels = ['Microsoft', 'Windows']
                if set[3] in windows_sys_labels :
                        # Append to lilosetup.conf
                        stub = open(stub_location, "a")
                        stub.write("#\n")
                        stub.write(_("# Windows bootable partition config begins\n"))
                        stub.write("other = " + set[1] + "\n")
                        stub.write("label = " + set[4] + "\n")
                        stub.write(_("# Windows bootable partition config ends\n"))
                        stub.close()
                else:
                    # Applies to Linux partitions
                    # Confirm that a partition is configured
                    partition_set.append("OK")
                    # Append to lilosetup.conf
                    stub = open(stub_location, "a")
                    # There maybe a few kernels in the same partition
                    vmlist = sorted(glob.glob(chroot_mnt + other_mnt + "/boot/vmlinuz*"))
                    # Remove symbolic links
                    for i in vmlist :
                        if os.path.islink(i) :
                            vmlist.remove(i)
                    initlist = sorted(glob.glob(chroot_mnt + other_mnt + "/boot/initrd*"))
                    # Remove symbolic links
                    for i in initlist :
                        if os.path.islink(i) :
                            initlist.remove(i)
                    it = 0
                    while it < len(vmlist) :
                        stub.write("#\n")
                        stub.write(_("# Linux bootable partition config begins\n"))
                        try :
                            vmlinuz_file_path = vmlist[it].split("boot")[1]
                            stub.write("image = " + mount_inconf + "/boot" + vmlinuz_file_path + "\n")
                        except:
                             error_dialog(_("Error! One of your partitions does not seem to hold a valid kernel file, please verify & correct lilo.conf manually"))
                        # Add addappend line if neededed
                        # check if LIBATA is used
                        if "/dev/hd" in set[1] :
                            libata_try = set[1].replace("hd", "sd")
                            libata_line = commands.getoutput("cat " + mount_inconf + "/etc/fstab | grep " + libata_try)
                            if libata_line != '' :
                                libata_device = libata_line.split()[0]
                                if "/dev/sd" in libata_device :
                                    stub.write("""addappend = "root=""" + libata_device + """ "\n""")
                                else : # some fstab files may have weird layout & scheme, try mtab instead
                                    libata_device = commands.getoutput("cat " + mount_inconf + "/etc/mtab | grep " + libata_try).split()[0]
                                    if "/dev/sd" in libata_device :
                                        stub.write("""addappend = "root=""" + libata_device + """ "\n""")
                                    else :
                                        pass
                        else :
                            pass

                        stub.write("root = " + set[1] +"\n")
                        if len(vmlist) == 1 :
                            stub.write("label = " + set[4] + "\n")
                        else:
                            vmlinuz_suffix = vmlinuz_file_path.split('/')[-1].replace("vmlinuz", "")
                            stub.write("label = " + set[4] + vmlinuz_suffix +"\n")
                        try :
                            initrd_file_path = initlist[it].split("boot")[1]
                            stub.write("initrd = " + mount_inconf + "/boot" + initrd_file_path + "\n")
                        except :
                            pass
                        stub.write("read-only\n")
                        stub.write(_("# Linux bootable partition config ends\n"))
                        it += 1
                    stub.close()
        # Check if at least one Linux partition has been configured:
        if partition_set == [] :
            error_dialog(_("Your configuration is not complete. Please, select at least one Linux booting partition and define its Boot menu label."))
        else:
            self.EditButton.set_sensitive(True)
            self.DeleteButton.set_sensitive(True)
            self.CreateButton.set_sensitive(False)
            self.ExecuteButton.set_sensitive(True)
            self.BootPartitionTreeview.set_sensitive(False)

    def on_delete_button_clicked(self, widget, data=None):
        """
        Deletes lilosetup.conf.
        """
        os.remove(stub_location)
        self.EditButton.set_sensitive(False)
        self.DeleteButton.set_sensitive(False)
        self.CreateButton.set_sensitive(True)
        self.ExecuteButton.set_sensitive(False)
        self.BootPartitionTreeview.set_sensitive(True)

    def on_edit_button_clicked(self, widget, data=None):
        """
        Opens the edit lilosetup.conf dialog.
        """
        subprocess.call('xdg-open ' + stub_location, shell=True)

    def on_execute_button_clicked(self, widget, data=None):
        warning_dialog(_("You are about to install a new LILO bootloader. Are you sure you want to continue?"))
        if result_warning == gtk.RESPONSE_YES:
            # If previous lilosetup.conf file exist, save it as lilosetup.old
            if os.path.isfile(chroot_mnt + "/etc/lilosetup.conf") == True :
                os.rename(chroot_mnt + "/etc/lilosetup.conf", chroot_mnt +'/etc/lilosetup.old')
            shutil.copy(stub_location, chroot_mnt + "/etc/lilosetup.conf")
            # Copy /boot/salix graphics to chroot_mnt if needed
            if os.path.isfile(chroot_mnt + "/boot/salix.bmp") == False :
                if os.path.isfile("/boot/salix.bmp") == True :
                    shutil.copy("/boot/salix.bmp", chroot_mnt + "/boot/salix.bmp")
                elif os.path.isfile("/mnt/live/memory/images/01-core.lzm/boot/salix.bmp") == True :
                    shutil.copy("/mnt/live/memory/images/01-core.lzm/boot/salix.bmp", chroot_mnt + "/boot/salix.bmp")
            # Execute Lilo
            subprocess.call("mount --bind /dev " + chroot_mnt + "/dev 2>/dev/null", shell=True)
            lilo_command = "lilo -v -r " + chroot_mnt + " -C /etc/lilosetup.conf > /var/log/lilosetup.log"
            output = commands.getstatusoutput(lilo_command)
            if 0 in output :
                info_dialog(_("The installation of your new LILO bootloader was succesful. You can now exit LiloSetup and reboot your computer."))
                self.ExecuteButton.set_sensitive(False)
            else:
                error_dialog(_("The installation of your new LILO bootloader failed. Please verify /var/log/lilosetup.log, modify your settings and try again."))
                self.ExecuteButton.set_sensitive(False)
        if result_warning == gtk.RESPONSE_NO:
            pass

if __name__ == '__main__':
    # Checks for root privileges
    if os.getuid() != 0:
        error_dialog(_("Root privileges required!"))
        sys.exit(1)
    # Executes the main program
    LiloSetup()
    gtk.main()