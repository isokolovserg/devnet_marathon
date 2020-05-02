#!/usr/bin/python

from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from nornir.core.filter import F
import re
import sys

mac = input("Please, enter MAC address in format: HHHH.HHHH.HHHH").strip()
mac = mac.lower()
mac_regexp = re.compile(r'[a-f0-9]{4,4}\.[a-f0-9]{4,4}\.[a-f0-9]{4,4}')
mac_check = mac_regexp.search(mac)
if mac_check == None:
    print("Wrong MAC address.")
    sys.exit(1)

norn = InitNornir(config_file='norn-config-local.yml')

switches = norn.filter(F(groups__contains="switches"))

#get mac address tables and cdp neighbours from all switches
show_mac = switches.run(task=netmiko_send_command, command_string="show mac address-table", use_textfsm=True)
show_cdp_nei = switches.run(task=netmiko_send_command, command_string="show cdp neighbors", use_textfsm=True)
show_arp = norn.run(task=netmiko_send_command, command_string="show ip arp", use_textfsm=True)
show_int_sw = switches.run(task=netmiko_send_command, command_string="show interfaces switchport", use_textfsm=True)


for hostname in show_mac.keys():
    for interface in show_mac[hostname][0].result:
        if interface['destination_address'] == mac:
