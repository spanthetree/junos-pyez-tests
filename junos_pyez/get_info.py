#!/usr/bin/env python

import os, sys, argparse, pprint, getpass, re, yaml
from threading import Thread
# Import junos eznc factory loader - for generating new tables/views
from jnpr.junos.factory.factory_loader import FactoryLoader
# Import junos sample tables:
# https://www.juniper.net/techpubs/en_US/junos-pyez1.0/topics/concept/junos-pyez-tables-and-views-overview.html
from jnpr.junos.op.arp import ArpTable
from jnpr.junos.op.fpc import FpcHwTable, FpcInfoTable
from jnpr.junos.op.lacp import LacpPortTable
from jnpr.junos.op.lldp import LLDPNeighborTable
from jnpr.junos.op.phyport import PhyPortTable, PhyPortStatsTable, PhyPortErrorTable
from jnpr.junos.op.routes import RouteTable
from jnpr.junos.op.vlan import VlanTable
# Import junos connect method
from jnpr.junos import Device

__author__ = 'David Woodruff'

arp = '''
---
EtherSwTable:
  rpc: get-interface-ethernet-switching-table
  item: ethernet-switching-table/mac-table-entry[mac-type='Learn']
  key: mac-address
  view: EtherSwView

EtherSwView:
  fields:
    vlan_name: mac-vlan
    mac: mac-address
    mac_type: mac-type
    mac_age: mac-age
    interface: mac-interfaces-list/mac-interfaces
'''

COMMANDS = {
    'arptable': ArpTable,
    'hwtable': FpcHwTable,
    'lacptable': LacpPortTable,
    'lldp': LLDPNeighborTable,
    'phytable': PhyPortTable,
    'phystats': PhyPortStatsTable,
    'routetable': RouteTable,
    'vlantable': VlanTable,
    'mactable': 'EtherSwTable',

}

def group_by(fn, l):
    acc = {}
    for e in l:
        acc.setdefault(fn(e), []).append(e)
    return acc

def print_facts(args, passwd, dev):
    pp = pprint.PrettyPrinter(indent=4)
    fact = args.fact.lower()
    interface = args.interface.lower()


    facts = fact.split(',')
    for f in facts:
        print ''
        print "{} for {}:".format(f, dev)
        print "========================================"
        if 'vlantable' in f:
            entries = VlanTable(dev).get()
            #import pdb; pdb.set_trace()
            for k,v in entries.items():
                print k, v
            for e in entries:
                # ['status', 'instance', 'tag', 'name', 'members', 'created', 'owner']
                member_vlan = ', '.join(str(i) for i in e.members)
                if 'intmembers' in args.opt:
                    print ''
                    print e.name
                    print member_vlan
                else:
                    print ''
                    print 'Name: {}, Tag: {}, Status: {}, Instance: {}, Members: {}'\
                    .format(e.name, e.tag, e.status, e.instance, member_vlan)
                    #pp.pprint(e.keys())
                    #pp.pprint(e.values())
                    #print "SFHQ,{},{},Active".format(vlan.tag, vlan.name)

        # MK magic
        elif 'mactable' in f:
            table = EtherSwTable(dev).get()

            mac_tables = []

            for v in table.values():
                config = dict(v)
                vlan_name = config['vlan_name']
                mac = config['mac']

                if interface == 'all' or vlan_name.lower() == interface:
                    mac_tables.append(config)

            by_vlan = group_by(lambda e: e['vlan_name'], mac_tables)

            for vlan, macs in by_vlan.items():
                print "Total number of macs learned for interface {}: {}".format(
                    vlan, len(macs))
                #print "And the list of macs is: {}".format([mac['mac'] for mac in macs])

        else:
            rpc_cmd = COMMANDS[f]
            entries = rpc_cmd(dev).get()
            for k,v in entries.items():
                if args.opt is 'int':
                    print k
                else:
                    print k,v


def main():
    parser = argparse.ArgumentParser(description="Get fact table from Junos \
        devices")
    parser.add_argument('-d', '--device', nargs='+', help='Device hostname or \
        list of devices, separated by a space')
    parser.add_argument('-u', '--user', help='admin username, defaults to current user',
        default=getpass.getuser())
    parser.add_argument('-f', '--fact', help='Specify fact table to print - \
        vlantable, routetable, phystats, phytable, lldptable, lacptable, \
        hwtable, arptable ')
    parser.add_argument('-i', '--interface', help='Specify interface to check for mactable',
        default='all')
    parser.add_argument('-o', '--opt', help='Options - int (interface),\
        intmembers (members)')

    args = parser.parse_args()

    passwd = getpass.getpass()

    globals().update(FactoryLoader().load(yaml.load(arp)))

    if args.fact is None:
        raise RuntimeError('You must define a fact to check!')

    print ''
    fact_list = args.fact.lower().split(',')
    for fact in fact_list:
        if fact not in COMMANDS:
            raise ValueError('%s is not a valid fact!' % args.fact)
    print "**Gathering {} from {} devices**".format(fact_list, len(args.device))
    for device in args.device:
        dev = Device(host=device, user=args.user, password=passwd).open()
        print_facts(args, passwd, dev)

if __name__ == "__main__":
    main()
