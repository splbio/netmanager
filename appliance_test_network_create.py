#!/usr/bin/env python

import subprocess
import os

import pprint

def runit(args):
    print args
    res = subprocess.check_output(args)
    print res
    return res

def get_tap():
    return runit(["ifconfig", "tap", "create"]).rstrip()

def make_network():
    taps = {}
    bridges = {}

    bridges["data"] = runit(["ifconfig", "bridge", "create"]).rstrip()
    bridges["control"] = runit(["ifconfig", "bridge", "create"]).rstrip()

    taps["router_control"] = get_tap()
    taps["router_data"] = get_tap()

    taps["appliance_mgmt0"] = get_tap()
    taps["appliance_span0"] = get_tap()
    taps["appliance_inject0"] = get_tap()

    taps["client_control"] = get_tap()
    taps["client_data"] = get_tap()

    attachments = [
        # bridge     tap                  mode
        ("control", "router_control",     "tap"),
        ("control", "appliance_mgmt0",    "tap"),
        ("control", "client_control",     "tap"),

        ("data",    "router_data",        "tap"),
        ("data",    "appliance_span0",    "span"),
        ("data",    "appliance_inject0",  "tap"),
        ("data",    "client_data",        "tap"),
    ]
    topology = {
        "control": {
            "taps": {
                "router_control":     {"mode":"tap"},
                "appliance_mgmt0":    {"mode":"tap"},
                "client_control":     {"mode":"tap"},
            }
        },
        "data": {
            "taps": {
                "router_data":        {"mode":"tap"},
                "appliance_span0":    {"mode":"span"},
                "appliance_inject0":  {"mode":"tap"},
                "client_data":        {"mode":"tap"},
            },
        }
    }
    for bridge_key in topology.keys():
        bridge_if = bridges[bridge_key]
        topology[bridge_key]["if"] = bridge_if

        for tap_key in topology[bridge_key]["taps"].keys():
            tap_if = taps[tap_key]
            topology[bridge_key]["taps"][tap_key]["if"] = tap_if
            mode = topology[bridge_key]["taps"][tap_key]["mode"]

            if mode == "tap":
                runit(["ifconfig", bridge_if, "addm", tap_if, "stp", tap_if])
            elif mode == "span":
                runit(["ifconfig", bridge_if, "span", tap_if])
            else:
                raise(Exception("invalid mode %s for %s %s", (b,t)))

    print pprint.pprint(topology)

# ifconfig| grep ^tap | cut -f 1 -d: |xargs -n1 -tJ % ifconfig % destroy
# ifconfig| grep ^bridge | grep -v "^bridge0" |  cut -f 1 -d: |xargs -n1 -tJ % ifconfig % destroy


if __name__ == "__main__":
    make_network()
