#!/usr/bin/python3

# BTBeacon.py
# SJM Jul 21
#
#  Setup a bluetooth "Eddystone" beacon to broadcast your RPi's IP address
#  as a URI of the form http://<host-ip-address>
#  Can then use a bluetooth beacon app on a smart-phone to find and browse to the RPi
#  If not running a web server on the RPi then the ip address will still be of use.
#
#  *** This code must be run with root priviledges ***
#
#  To find the host machine's ip address parse the output of `ip route` and look
#  for dev <interface-name> * scope link * src <ip-addr> on a single line so as to
#  build an {interface:ip-addr} dict eg {'eth0':'192.168.0.3', 'wlan0':'192.168.0.45'}
#  If no active interfaces are found BTBeacon uses the machine's hostname
#  If more than one active interface is found:
#    choose the alphabetical first eth* interface
#    but if no eth* interfaces are listed just choose the alphabetical first
#
#
# Requires:
#  hostname, hciconfig and hcitool cli utilities @ /usr/bin/
#  ip cli utility @ /usr/sbin/
#  root status
#
#
# Usage:
#  sudo ./BTBeacon.py
#  or use sudo crontab -e to set as a root cron job @reboot and/or every hour.
#
#
# To do:
#  Allow command line spec'n of the URI & protocol
#  Allow cmd line spec'n of the interface who's ip to use
#  Parse CMD3's error message
#  Parse apache config file for an IP binding
#
#
# Notes on B'Tooth Eddystone URL beacon:
#  See: https://hackaday.io/project/10314-raspberry-pi-3-as-an-eddystone-url-beacon...
#  > sudo hciconfig hci0 up
#  > sudo hciconfig hci0 leadv 3
#  then...
#
#  Eg1: https://webgazer.org
#  > sudo hcitool -i hci0 cmd 0x08 0x0008 17 02 01 06 03 03 aa fe 0f 16 aa fe 10 00 03 77 65 62 67 61 7a 65 72 08 00 00 00 00 00 00 00 00
#
#  Eg2: http://192.168.0.103
#  > sudo hcitool -i hci0 cmd 0x08 0x0008 1b 02 01 06 03 03 aa fe 13 16 aa fe 10 00 02 31 39 32 2e 31 36 38 2e 30 2e 31 30 33 00 00 00 00
#
#  ie
#  > sudo hcitool -i hci0 cmd 0x08 0x0008 L1 02 01 06 03 03 aa fe L2 16 aa fe 10 00 ss cc cc cc cc cc cc cc cc cc 00 00 00 00 00 00 00 00
#  where:
#    L1 & L2 are the lengths of the byte-lists which follow
#    ss = 02 for http, 03 for https protocol
#    cc = hex(ord(ASCII)) of the text of the URI (without the protocol prefix)
#    if L = len(uri_without_http_or_https_://)
#      L1 = hex2(L + 14) 
#      L2 = hex2(L + 6)
#    Note the 08 at the end of eg1 expands to ".org"
#    It's not clear how many trailing 00s are required, if any

# -----------------------------------------------------------------------

# configuration options...

proto = 'http' # must be either http or https, default to http
# TBD optionally get proto from command line

# Set a host name or IP here or leave as None to auto-detect
host = None
# TBD optionally get host from command line

# -----------------------------------------------------------------------

import subprocess, re

CMD1 = "/usr/bin/ip route"
CMD2 = "/usr/bin/hciconfig hci0 up" # expect returncode == 0
CMD3 = "/usr/bin/hciconfig hci0 leadv 3" # returncode is no use
CMD4A = "/usr/bin/hcitool -i hci0 cmd 0x08 0x0008" # L1
CMD4B = "02 01 06 03 03 aa fe" # L2
CMD4C = "16 aa fe 10 00" # ss cc cc cc cc...

# general purpose shell-out routine
def shellOut(cmd): return subprocess.run(cmd.split(), capture_output=True, text=True, encoding='utf8')


ss = 0
if proto is not None:
  # remove any :// from proto
  proto = re.sub(r"[^a-z]", "", proto.lower())
  try:    ss = ['', '', 'http', 'https'].index(proto)  # yeilds 2 for http, 3 for https 
  except: pass
if ss not in range(2,4): # ie 2 or 3
  proto = 'http'
  ss = 2

if host is None:
  # get IP addrs...
  myIPs = {}
  lines = shellOut(CMD1).stdout.split('\n')
  for line in lines:
    if ' scope link ' not in line: continue
    if ' src ' not in line: continue
    if ' dev ' not in line: continue
    parts = line.split()
    try:
      dev = parts[parts.index('dev') + 1]  
      ip  = parts[parts.index('src') + 1]  
    except: continue
    myIPs[dev] = ip

  # if we currently have no active IP addrs assigned use hostname instead
  if len(myIPs) == 0:
    host = shellOut('hostname').stdout
  else:
    if len(myIPs) > 1:
      # must pick one of many
      ifaces = sorted(myIPs.keys())
      host = myIPs[ifaces[0]] # default pick the first entry
      # but choose instead an "eth" entry if there is one
      for iface in ifaces:
        if 'eth' in iface:
          host = myIPs[iface]
          break

if host is None:
  print('BTBeacon - no valid host-name or IP!')
  raise SystemExit(1)

# CMD2 UPs the hci0 i/face...
rslt = shellOut(CMD2)
# check for error code
if rslt.returncode != 0:
  print(f"BTBeacon '{CMD2}' errored out with: '{rslt.stdout} {rslt.stderr}' MUST be run with root piviledges")
  raise SystemExit(2)

# CMD3 will error out if leadv is already set, so safe to ignore.
# TBD parse the error message
rslt = shellOut(CMD3)

# build CMD4...
l = len(host)
l1 = '{:02x}'.format(l+14)
l2 = '{:02x}'.format(l+6)
ss = '{:02x}'.format(ss)
CMD4 = f"{CMD4A} {l1} {CMD4B} {l2} {CMD4C} {ss}"
# append our host/IP in hex format
for ch in host: CMD4 += ' {:02x}'.format(ord(ch))
# finally pad with some zeros, unclear how many (if any) are required.
for i in range(l, max(17,l+1)): CMD4 += ' 00'

# issue the command...
rslt = shellOut(CMD4)
if rslt.returncode != 0:
  print(f"BTBeacon '{CMD4}' Failed with error: '{rslt.stdout} {rslt.stderr}'")
  raise SystemExit(3)

# report success...
print(f"BTBeacon - successfuly set to {proto}://{host}") 
