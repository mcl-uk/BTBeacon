# BTBeacon
Bluetooth 'eddystone' beacon for RPi

 A python3 script to setup a bluetooth "Eddystone" beacon to broadcast your RPi's IP
  address as a URI of the form http://{host-ip-address}.
  Can then use a bluetooth beacon app on a smart-phone to find and browse to the RPi.
  If not running a web server on the RPi then it's ip address may still be of use.

  *** Note this code must be run with root priviledges ***

  To find the host machine's ip address this code parses the output of `ip route` and looks for
  
  dev {interface-name} * scope link * src {ip-addr}

  on a single line so as to build an {interface:ip-addr} dictionary eg {'eth0':'192.168.0.3', 'wlan0':'192.168.0.45'}.
  If no active interfaces are found BTBeacon uses the machine's hostname.
  If more than one active interface is found:
  
    choose the alphabetical first eth* interface
  
    but if no eth* interfaces are listed just choose the alphabetical first


 Requires:
  hostname, hciconfig and hcitool cli utilities @ /usr/bin/
  ip cli utility @ /usr/sbin/
  root status


 Based on:
  https://hackaday.io/project/10314-raspberry-pi-3-as-an-eddystone-url-beacon...


 Usage:
  sudo ./BTBeacon.py
  or use sudo crontab -e to set as a root cron job @reboot and/or every hour.


 To do:
  Allow command line spec'n of the URI & protocol
  Allow cmd line spec'n of the interface who's ip to use
  Parse CMD3's error message
  Parse apache config file for an IP binding


