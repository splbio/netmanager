#!/usr/bin/env python

import subprocess
import os
import json
import sys

import pprint

import logging

import copy

log = logging.getLogger(__file__)

def runit(args):
    log.debug(args)
    res = subprocess.check_output(args)
    log.debug(res)
    return res

class VMNetManager(object):

    def __init__(self):
        pass

    def get_tap(self):
        return {
            "if": runit(["ifconfig", "tap", "create"]).rstrip(),
            "cleanup": True,
            }

    def teardown_ifs(self, ifs):
        for key, val in ifs.iteritems():
            if val["cleanup"]:
                self._iface_kill(val["if"])

    def setup_taps(self):
        s = self
        taps = {}
        try:
            taps["router_control"] = s.get_tap()
            taps["router_data"] = s.get_tap()

            taps["appliance_mgmt0"] = s.get_tap()
            taps["appliance_span0"] = s.get_tap()
            taps["appliance_inject0"] = s.get_tap()

            taps["client_control"] = s.get_tap()
            taps["client_data"] = s.get_tap()
        except:
            self.teardown_ifs(taps)
            raise
        return taps

    def setup_bridges(self, cfg):
        bridges = {}
        for key, val in cfg.iteritems():
            if val["dynamic"]:
                bridge_if = runit(["ifconfig", "bridge", "create"]).rstrip()
            else:
                bridge_if = val["if"]
            bridges[key] = {}
            bridges[key]["cleanup"] = val["dynamic"]
            bridges[key]["if"] = bridge_if
        return bridges

    def make_network(self, config):
        s = self
        bridge_cfg = copy.deepcopy(config["bridge_config"])
        cleanup = []
        taps = {}
        bridges = {}
        try:
            taps = s.setup_taps()
            bridges = s.setup_bridges(bridge_cfg)
        except:
            self.teardown_ifs(taps)
            self.teardown_ifs(bridges)
            raise

        topology = copy.deepcopy(config["topology"])
        cleanup = []
        tap_map = {}
        try:
            for bridge_key in topology.keys():
                bridge_if = bridges[bridge_key]["if"]
                topology[bridge_key]["if"] = bridge_if
                if bridges[bridge_key]["cleanup"]:
                    cleanup.append(bridge_if)

                for tap_key in topology[bridge_key]["taps"].keys():
                    tap_if = taps[tap_key]["if"]
                    tap_map[tap_key] = tap_if
                    if taps[tap_key]["cleanup"]:
                        cleanup.append(tap_if)
                    topology[bridge_key]["taps"][tap_key]["if"] = tap_if
                    mode = topology[bridge_key]["taps"][tap_key]["mode"]

                    if mode == "tap":
                        runit(["ifconfig", bridge_if, "addm", tap_if, "stp", tap_if])
                    elif mode == "span":
                        runit(["ifconfig", bridge_if, "span", tap_if])
                    else:
                        raise(Exception("invalid mode %s for %s %s", (b,t)))
        except:
            self.teardown_ifs(taps)
            self.teardown_ifs(bridges)
            raise
        return {
            "topology": topology,
            "cleanup": cleanup,
            "tap_map": tap_map,
            "bridge_cfg": bridge_cfg
            }

    def _iface_kill(self, iface):
        runit(["ifconfig", iface, "destroy"])

    def cleanup(self, ifaces):
        for iface in ifaces:
            self._iface_kill(iface)


import argparse

def openfile(f, mode):
    if f == '-':
        if mode == 'r':
            return sys.stdin
        else:
            return sys.stdout
    return open(f, mode)

def op_create(args):
    config = json.loads(open(args.cfg, 'r').read())
    out = openfile(args.file, 'w')
    mgr = VMNetManager()
    network = mgr.make_network(config=config)
    out.write(json.dumps(network, sort_keys=True, indent=4))

def op_cleanup(args):
    inf = openfile(args.file, 'r')
    mgr = VMNetManager()
    mgr.cleanup(json.loads(inf.read())["cleanup"])
    pass

def op_show(args):
    inf = openfile(args.file, 'r')
    network = json.loads(inf.read())
    print json.dumps(network["tap_map"], sort_keys=True, indent=4)
    pass

def op_nuke(args):
    subprocess.call("ifconfig| grep ^tap | cut -f 1 -d: |xargs -n1 -tJ % ifconfig % destroy", shell=True)
    subprocess.call('ifconfig| grep ^bridge | grep -v "^bridge0" |  cut -f 1 -d: |xargs -n1 -tJ % ifconfig % destroy', shell=True)
    pass

def main():
    parser = argparse.ArgumentParser(description='Manage virtual networks for bhyve.')
    subparsers = parser.add_subparsers(help='sub-command help')
    parser_create = subparsers.add_parser('create', help='Create the virtual network, output to FILE')
    parser_create.set_defaults(func=op_create)
    parser_create.add_argument('-c', '--cfg', help="config file json")

    parser_cleanup = subparsers.add_parser('cleanup', help='Destroy the virtual network given by FILE')
    parser_cleanup.set_defaults(func=op_cleanup)

    parser_show = subparsers.add_parser('show-taps', help='Show taps')
    parser_show.set_defaults(func=op_show)

    parser_nuke = subparsers.add_parser('nuke-all', help='nuke all taps and bridges on system')
    parser_nuke.set_defaults(func=op_nuke)

    for p in [ parser_create, parser_cleanup, parser_show ]:
        p.add_argument('-f', '--file', default='-')

    args = parser.parse_args()
    #pprint.pprint(args)
    args.func(args)


if __name__ == "__main__":
    main()
    sys.exit(0)
    #../develop/tools/vmrun-current.sh -d ./FreeBSD-10.2-small.raw -t tap0 -m 4G -t tap6 router1

