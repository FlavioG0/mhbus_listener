#!/bin/sh
cd /var/ftp/flavio/myhome/mh_bus_listener
rm nohup.out
nohup python mh_bus_listener.py &
