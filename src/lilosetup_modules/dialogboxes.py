#!/usr/bin/env python

"""
Functions related to dialog boxes

"""

import gtk
import config

def info_dialog(message, parent = None):
    """
    Display an information message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_INFO, buttons = gtk.BUTTONS_OK, flags = gtk.DIALOG_MODAL)
    dialog.set_markup(message)
    dialogicon = dialog.render_icon(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_MENU)
    dialog.set_icon(dialogicon)
    dialog.run()
    dialog.destroy()

def warning_dialog(message, parent = None):
    """
    Display a warning message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_WARNING, flags = gtk.DIALOG_MODAL)
    dialog.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES)
    dialog.add_buttons(gtk.STOCK_NO, gtk.RESPONSE_NO)
    dialog.set_default_response(gtk.RESPONSE_NO)
    dialog.set_markup(message)
    dialogicon = dialog.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
    dialog.set_icon(dialogicon)
    config.response_to_warning[0] = dialog.run()
    dialog.destroy()

def error_dialog(message, parent = None):
    """
    Display an error message.

    """
    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_CLOSE, flags = gtk.DIALOG_MODAL)
    dialog.set_markup(message)
    dialogicon = dialog.render_icon(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)
    dialog.set_icon(dialogicon)
    dialog.run()
    dialog.destroy()
