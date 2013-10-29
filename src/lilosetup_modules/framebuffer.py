#!/usr/bin/env python

"""
Functions used to detect and set LILO framebuffer.

"""

import os
import subprocess

def run_bash(cmd):
    """
    Take a bash command and return its output (the stdout from the shell command). 
    
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read().strip()
    return out 

def detect_fb():
    """
    Check if framebuffer is available
    
    """
    fb_geometry = "fbset | grep -w geometry"
    if fb_geometry:
        values = run_bash(fb_geometry).split(' ')
        xres = values[1]
        yres = values[2]
        if values[-1] == "8":
            depth = "256"
        elif values[-1] == "16":
            depth = "32k"
        elif values[-1] == "24":
            depth = "64k"
        elif values[-1] == "32":
            depth = "16M"
        else:
            return ""     
        return xres + 'x' + yres + 'x' + depth            

def set_fb(current_framebuffer, stub_location):
    """
    Set a framebuffer in LiloSetup config file if available, 
    otherwise failsafe to normal VGA console.
    
    """
    # Sets the variable 'stubfile' in bash environment
    os.putenv("stubfile", stub_location) 
    # Sets the variable 'current_framebuffer' in bash environment
    os.putenv("setfb", current_framebuffer)
    # Ensure the adequate framebuffer resolution is in the stub
    fb_desc_line = run_bash('cat $stubfile | grep "@ $setfb" -m 1 -n | cut -f1 -d :')
    if fb_desc_line != '' :        
        fb_set_line = int(fb_desc_line) + 1
        # Sets the variable 'fb_set_line' in bash environment
        os.putenv("editline", repr(fb_set_line))
        set_framebuffer = "sed $editline's/# //' -i $stubfile"
        subprocess.call(set_framebuffer, shell=True)
    # If no fitting resolution is available from the stub, then failsafe to vga-normal
    else :
        failsafe_fb()

def failsafe_fb(stub_location):
    """
    Fall back on a failsafe framebuffer option in LiloSetup configuration file

    """
    # Sets the variable 'stubfile' in bash environment
    os.putenv("stubfile", stub_location) 
    failsafe_line = run_bash('cat $stubfile | grep "vga = normal" -m 1 -n | cut -f1 -d :')
    # Sets the variable 'failsafe_line' in bash environment
    os.putenv("editline", failsafe_line)
    set_framebuffer = "sed $editline's/# //' -i $stubfile"
    subprocess.call(set_framebuffer, shell=True)
