#!/usr/bin/python
'''
Created by Andre Rumantir, Origo, 2018
'''

import pygame, os, sys, psutil, shutil
from datetime import datetime
from time import sleep
from subprocess import call


#global vars
##  EDIT AS REQUIRED  ##

#mass storage partition
DR_PARTITION = "mmcblk0p3"
#mount point for the mass storage partition
DR_MNTPT = "/mnt/removable"
#server to upload to. This requires NFS to be setup
SERVER = "192.168.101.22"
#shared mount point on server
SR_DIR = "/var/data"
#mount point on local for the shared folder
SR_MNTPT = "/mnt/data"


os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

#global colours
BLUE=(0,0,255)
WHITE=(255,255,255)

#setting up display
pygame.init()
pygame.mouse.set_visible(False)
lcd = pygame.display.set_mode((480,320))
lcd.fill(WHITE)
pygame.display.update()

#font settings
font_big = pygame.font.Font(None, 70)
font_small = pygame.font.Font(None,30)

#global hit box
begin_box = 0
end_box = 0
poll_box = 0
done_box = 0

check_dirs = ['GS3_2630','RCD','JD-Data','GS2_1800']

'''
=========================
    DISPLAY FUNCTIONS
=========================
'''
def begin():
    pygame.event.clear() #clear any queued events
    clear_bg()

    rect = pygame.Rect((240,106),(300,80))
    rect.center = (240,106)
    global begin_box
    begin_box = pygame.draw.rect(lcd,BLUE,rect)

    rect = pygame.Rect((240,212),(300,80))
    rect.center = (240,212)
    global end_box
    end_box = pygame.draw.rect(lcd,BLUE,rect)

    text = font_big.render('BEGIN',True,WHITE)
    txt_rect = text.get_rect(center=(240,106))
    lcd.blit(text,txt_rect)

    text = font_big.render('END', True, WHITE)
    txt_rect = text.get_rect(center=(240,212))
    lcd.blit(text,txt_rect)

    pygame.display.update()

def clear_bg():
    background = pygame.Rect((0,0),(480,320))
    background.center = (240,160)
    pygame.draw.rect(lcd,WHITE,background)

def blit_text(surface, text, pos, font, clearbg=True, color=pygame.Color('black')):
    if clearbg:
        clear_bg()

    words = [word.split(' ') for word in text.splitlines()]  # 2D array where each row is a list of words.
    space = font.size(' ')[0]  # The width of a space.
    font_height = font.size(' ')[1]
    max_width, max_height = surface.get_size()
    x, y = pos
    for line in words:
        line_rect = pygame.Rect((0,y),(480,font_height))
        pygame.draw.rect(surface,WHITE,line_rect)
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]  # Reset the x.
                y += word_height  # Start on new row.
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]  # Reset the x.
        y += word_height  # Start on new row.

        pygame.display.update()

def setup_poll_button():
    rect = pygame.Rect((240,220),(300,50))
    rect.center = (240,220)
    global poll_box
    poll_box = pygame.draw.rect(lcd,BLUE,rect)

    text = font_small.render('Check',True,WHITE)
    txt_rect = text.get_rect(center=(240,220))
    lcd.blit(text,txt_rect)

    blit_text(lcd,'WARNING: press only when transfer is completed',(0,260),font_small,False)

def setup_done_button():
    rect = pygame.Rect((240,220),(300,50))
    rect.center = (240,220)
    global done_box
    done_box = pygame.draw.rect(lcd,BLUE,rect)

    text = font_small.render('Done',True,WHITE)
    txt_rect = text.get_rect(center=(240,220))
    lcd.blit(text,txt_rect)
    
    pygame.display.update()

def setup_transfer():
    #mount removable drive
    call(["modprobe","g_mass_storage","file=/dev/" + DR_PARTITION,"ro=0","removable=y"])

    #disable collision on hit_box button
    global hit_box
    hit_box = pygame.draw.rect(lcd,WHITE,(0,0,0,1))

    blit_text(lcd,'Please proceed with exporting data on \nthe display', (50,120), font_small)

'''
=======================
    FUNCTIONALITIES
=======================
'''

'''
    Detects button pressed for poll button
'''
def poll_button():
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if poll_box.collidepoint(pos):
                return True
    return False

'''
    Detects button pressed for done button
'''
def done_button():
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if done_box.collidepoint(pos):
                return True
    return False

'''
    Gets size of parameter 'path'.
    Supports directories and files
'''
def get_size(path):
    total_size = 0
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    elif os.path.isfile(path):
        total_size = os.path.getsize(path)

    return total_size

'''
    Checks if there are any recognized directory structure in the removable drive.
    This depends on what model display is connected.
    GS3 2630 exports "GS3_2630" folder
    GS2 2600 exports "RCD" folder
    GS2 1800 exports "GS2_1800" folder
    GS4 4600 exports "JD-Data" folder
'''
def check_dir():
    if not os.path.exists(DR_MNTPT):
        os.makedirs(DR_MNTPT)

    call(["mount","-o","ro","/dev/" + DR_PARTITION, DR_MNTPT])
    size = -1

    #wait until its mounted
    while not os.path.ismount(DR_MNTPT):
        if os.path.ismount(DR_MNTPT):
            break
        sleep(1)

    for dir in check_dirs:
        path = DR_MNTPT + "/" + dir
        if os.path.exists(path):
            size = get_size(path)

    call(["umount",DR_MNTPT])
    sleep(1)

    return size

'''
    Detects any on-going transfers to the removable drive by detecting two things:
        - I/O transfers
        - size changes on the folder (this requires a remount to check size changes).
            handled by check_dir()
'''
def detect_transfer():
    initial = psutil.disk_io_counters(True)[DR_PARTITION].write_bytes
    timer_start = False
    timer_write = 0
    idle_counter = 0
    dir_size = 0
    force_poll = False

    #if directory exists, transfer
    if check_dir() > 0:
        transfer()
        return 0

    while True:
        writes = psutil.disk_io_counters(True)[DR_PARTITION].write_bytes

        if initial != writes and not timer_start:
            initial = writes
            timer_start = True
            sys.stdout.write("transfering...")
            setup_poll_button()

        if timer_start:
            if timer_write == writes:
                idle_counter += 1
            else:
                sys.stdout.write(".")
            timer_write = writes
            force_poll = poll_button()

        sys.stdout.flush()

        if idle_counter == 15 or force_poll:
            size = check_dir()
            if size == dir_size and size != -1:
                transfer()
                break
            elif size == -1:
               blit_text(lcd,'Unable to find directory',(50,260),font_small,False)
               timer_start = False
            elif force_poll:
               blit_text(lcd,'Files are still transferring. Try again later',(50,260),font_small,False)

            dir_size = size
            idle_counter = 0

        sleep(1)

'''
    prepares transfer to server
'''
def transfer():
    call(["modprobe","-r","g_mass_storage"])
    sleep(1)
    if not os.path.ismount(DR_MNTPT):
        call(["mount","/dev/"+DR_PARTITION,DR_MNTPT])

    blit_text(lcd,'Please wait while files are uploading \nto server...', (50,120), font_small)

    mounted = False
    if not os.path.ismount(SR_MNTPT):
        if not mount_network():
            mounted = False
            blit_text(lcd,'UPLOAD UNSUCCESSFUL.\nUnable to connect to server', (50,120),font_small)
        else:
            mounted = True
    else:
        mounted = True

    if mounted:
        print "UPLOADING..."
        if upload():
            blit_text(lcd,'UPLOAD SUCCESSFUL', (50,120),font_small)
        else:
            blit_text(lcd,'UPLOAD UNSUCCESSFUL', (50,120),font_small)

    call(["umount",DR_MNTPT])

    setup_done_button()

    while not done_button():
        sleep(1)

    begin()

'''
    Tries to mount the network drive to be uploaded to.
    It requires NFS server shared folder
'''
def mount_network():
    response = call(["mount",SERVER +":" + SR_DIR, SR_MNTPT])
    if response > 0:
        return False

    return True

'''
    begin uploading to server
'''
def upload():
    dirname = SR_MNTPT + "/" + datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    try:
        shutil.copytree(DR_MNTPT, dirname)

        for file in os.listdir(DR_MNTPT):
            if not file.startswith('.') and os.path.isdir(DR_MNTPT + "/" + file):
                shutil.rmtree(DR_MNTPT + "/" + file)
    except:
        return False

    return True

def shutdown():
    pygame.quit()
    sys.exit(0)


'''
=============
    MAIN
=============
'''
begin()

while True:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if begin_box.collidepoint(pos):
                setup_transfer()
                detect_transfer()
            if end_box.collidepoint(pos):
                shutdown()
