#!/usr/bin/env python3

from netmiko import ConnectHandler
import csv
import datetime
import sys
import os

DEVICES_FILE = 'devices.csv'
BACKUP_DIR = 'C:\\tmp\\backup_script\\backups\\' # /tmp/backup_script/backups/
NTP_SRV = 'pool.ntp.org'

def connect_to_device(device):
    connection = ConnectHandler(
            host = device['ip'],
            username = device['username'],
            password=device['password'],
            device_type=device['device_type'],
            secret=device['secret'],
            port=device['port']
    )
    return connection

def get_devices_from_file(devices_file):
    device_list = list()
    with open(devices_file, 'r') as dev_list:
        dev_conn_params = csv.DictReader(dev_list, delimiter=',')
        for row in dev_conn_params:
            device_list.append(row)
    return device_list

def gather_info(connection, backup_path, hostname, ntp_server):
    #create backup
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y_%m_%d-%H_%M_%S")
    if not os.path.exists(os.path.join(backup_path, hostname)):
        os.makedirs(os.path.join(backup_path, hostname))
    backup_file = os.path.join(backup_path, hostname, f'{hostname}-{timestamp}.cfg')
    connection.enable()
    print("Connected to ", hostname)
    running_config = connection.send_command('sh run')
    with open(backup_file, 'w') as backup_file:
        backup_file.write(running_config)
    
    #Device type
    inventory_check = connection.send_command('show inventory | incl PID')
    device_type = inventory_check.split()[1]

    #Show version and PE/NPE
    version_check = connection.send_command('show version')
    if 'NPE' in version_check:
        pe_npe = 'NPE'
    else:
        pe_npe = 'PE'
    show_version_split = version_check.splitlines()
    for ver_line in show_version_split:
        if 'Version' and 'SOFTWARE' in ver_line:
            os_version = ver_line.split(',')[-2].strip()

    #Timezone and NTP
    connection.send_config_set(['clock timezone GMT 0 0'])
    ntp_check = connection.send_command('show ntp status')
    ntp_state = ntp_check.split(',')[0].lstrip('%')
    ntp_ping = connection.send_command(f'ping {ntp_server}')
    if "Success rate is 0" in ntp_ping:
        print ("NTP server", ntp_server, "unavailable")
    else:
        connection.send_config_set([f'ntp server {ntp_server}'])


    #Check for CDP process status and number of CDP neighbors
    cdp_show = connection.send_command('show cdp')
    if "CDP is not enabled" in cdp_show:
        cdp_state = "CDP is OFF"
    else:
        cdp_state = f"CDP is ON, {cdp_show[-1]} peers"

    #Check configured hostname
    hostname_check = connection.send_command('show run | incl hostname')
    configured_hostname = hostname_check.split()[-1]

    device_info = f'{configured_hostname} | {device_type} | {os_version} | {pe_npe} | {cdp_state} | {ntp_state}'
    print(device_info)

    #disconnect from device
    connection.disconnect()

for device in get_devices_from_file(DEVICES_FILE):
    gather_info(connect_to_device(device), BACKUP_DIR, device['hostname'], NTP_SRV)