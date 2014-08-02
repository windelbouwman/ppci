#!/usr/bin/python

from ppci.utils.usb import UsbContext

# try to read usb.ids:
vids = {}
pids = {}
try:
   with open('usb.ids', 'r', errors='ignore') as f:
      vid = 0
      for l in f:
         if l.startswith('#') or not l.strip():
            continue
         if l.startswith('\t\t'):
            print('iface:', l)
         elif l.startswith('\t'):
            print('product', l)
            pid = int(l[1:5], 16)
            print('product', hex(pid), l)
         else:
            print('vendor', l)
            vid = int(l[0:4], 16)
            print('vendor', hex(vid), l)

except IOError as e:
   print("Error loading usb id's: {0}".format(e))

context = UsbContext()
for d in context.DeviceList:
   print(d)

