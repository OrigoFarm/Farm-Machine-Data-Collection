# Hardware Requirements
Barebone hardware requirements consist of the following:
1. [Raspberry Pi Zero W(Wireless)](https://www.raspberrypi.org/products/raspberry-pi-zero-w/)
2. [PiTFT Touchscreen display](https://www.adafruit.com/product/2097)
3. 16GB or higher MicroSD Card
4. 2x MicroUSB Cable
5. USB Power Adapter Min:5W
6. John Deere Greenstar™ Displays and desktop power harness

**Please note:** The above setup main purpose is to test functionality. Requirements will differ if installed on a machine/tractor.

Additional external power might or might not be necessary depending on the output power of the USB port on the display. In our setup we are using GS3 2630 display and are experiencing abnormalities on the Raspberry Pi. This is due to insufficient power from the USB port of the display, hence the additional power requirements above in our setup.

Server:
1. Any machine capable of hosting NFS shared folder

# Setup

## Writing image to SDCard
Download Raspbian at https://www.raspberrypi.org/downloads/raspbian/  
Raspbian Version at the time of writing   
Raspbian Stretch Lite  
Version: (March 2018)  
Release Date: 2018-03-13

Please follow [this](https://www.raspberrypi.org/documentation/installation/installing-images/README.md) guide in writing the image to an SDCard

## Prepare for initial bootup
Before putting the SDCard into the Raspberry Pi Zero W, additional modification to some files in the boot partition is required. 
1. Edit cmdline.txt. Should be looking like the following after rootwait
    ```
    rootwait modules-load=dwc2,g_ether quiet
    ```
    This does the following:
    - Removing auto resize script on initial boot. By default it should have ```init=/usr/lib/raspi-config/init_resize.sh ``` at the end of the line.
    - adding g_ether module if no keyboard and monitor attached initially. This will initiate virtual ethernet to your computer via USB connection
2. Add an empty "ssh" file on the boot directory. This will enable ssh on bootup
3. Add the following at the end of config.txt:
    ```
    dtoverlay=dwc2
    ```
    This enables dwc2 module

Insert the SDCard to the Raspberry Pi Zero W and startup. You should be able to ssh into the Pi with 'raspberry' as default password
```
ssh pi@raspberrypi.local
```

For more information please see [Pi OTG](http://bit.ly/pi-otg)

## SDCard partitioning
Partitioning of SDCard is necessary since part of the storage will be used as a mass storage device while the rest is the system files. Using fdisk to modify the partition.
```
fdisk /dev/mmcblk0  #mmcblk0 as the sdcard device
```
**Resizing main system partition to 5GB:**  
Type d to proceed deleting partition  
Type 2 to delete 2nd partition and press Enter  
Type n to create new partition  
Type p to make primary partition  
Type 2 to make this second partition  
Enter start sector as 137215  
Enter end sector as 10485759  

**Partitioning rest of space:**  
Type n to create new partition  
Type p to make primary partition  
Type 3 to make this third partition  
Enter start sector as 10485760  
Press enter for end sector as default
Type t to change partition type
Type 3 to select third partition
Type c to select FAT32 as partition type

Type w to write changes to disk

Please reboot the system after applying changes

After reboot, execute the following:
```
#resizing main system partition to fill rest of partition
resizefs /dev/mmcblk0p2

#format partition 3 as FAT32. This will be the mass storage space
mkfs.fat /dev/mmcblk0p3
```

## Wi-Fi setup
Edit the file at ```/etc/wpa-supplicant/wpa-supplicant.conf```. Enter the following at the end of file to configure wireless as client. Enter SSID and PSK as applicate to your setup.
```
network={
    ssid=""
    psk=""
}
```
Apply configuration by executing ```wpa_cli -i wlan0 reconfigure```  
Please see this [guide](https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md) for more information  
A [Guide](https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md) to setting up access point.

## Install packages for PiTFT touchscreen display
Run the following as root (sudo)
```
apt-get update
apt-get upgrade

apt-get install python-pygame

apt-get autoremove python-pip
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py

pip install psutil

#Setting up PiTFT display. Please follow the prompts as required.
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/adafruit-pitft.sh
chmod +x adafruit-pitft.sh
./adafruit-pitft.sh
```

Known issues with SDL2.x and SDL1.2.15-10 with PiTFT. Please see [here](https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/pitft-pygame-tips) for more information.  
Copy paste the below code to a file named ```installsdl.sh```.  
```bash
#!/bin/bash
  
#enable wheezy package sources
echo "deb http://archive.raspbian.org/raspbian wheezy main
" > /etc/apt/sources.list.d/wheezy.list

#set stable as default package source (currently jessie)
echo "APT::Default-release \"stable\";
" > /etc/apt/apt.conf.d/10defaultRelease

#set the priority for libsdl from wheezy higher then the jessie package
echo "Package: libsdl1.2debian
Pin: release n=jessie
Pin-Priority: -10
Package: libsdl1.2debian
Pin: release n=wheezy
Pin-Priority: 900
" > /etc/apt/preferences.d/libsdl

#install
apt-get update
apt-get -y --force-yes install libsdl1.2debian/wheezy
```
Make it executable  
```chmod +x installsdl.sh```

Run it  
```./installsdl.sh```

Check version of SDL by  
```dpkg -l | grep sdl```  
Version needs to be 1.2.15-5

## Configure application

To make the program to run at bootup, insert the following in ```/etc/rc.local``` just before ```exit 0```
```
#replace <directory> to the full path of where script is located
(sleep 5; python /<directory>/transfer.py)&
```

Please edit ```transfer.py``` settings as required.

Reboot the system

# Server setup
The above setup assumes NFS server setup in the local network with shared folder setup.  
Apache2 is installed in this particular setup to view shared folder in a browser.

Please run the following as root (sudo)
```
apt-get install nfs-kernel-server
apt-get install apache2

mkdir /var/data
```

Edit ```/etc/exports``` and inser the following at end of file:
```
/var/data *(rw,sync,no_root_squash,no_subtree_check)
```

Restart service  
```sudo systemctl start nfs-kernel-server.service```

Add the following to ```/etc/apache2/apache2.conf```
```
<Directory /var/data/>
	Options Indexes FollowSymLinks
	Require all granted
	AllowOverride None
</Directory>
```

Edit the file ```/etc/apache2/sites-enabled/000-default.conf```.  
Replace
```
DocumentRoot /var/www
```
to
```
DocumentRoot /var/data
```