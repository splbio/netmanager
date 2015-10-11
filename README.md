# netmanager
Tool for creating tap and bridge topologies under FreeBSD

This tool takes a network description and can dynamically generate the bridges and taps for a private/public network.

Useful for making bhyve networks for testing virtual machines.

## Config file

### section: bridge_config

a section "bridge_config" which defines the bridges that will make up the network.  Each bridge can be dynamically made or it can be hardcoded to an existing bridge.  Any hardcoded bridges will NOT be deleted when the tool is told to 'cleanup'.

### section: toplogy

The topology section defines which bridges each tap is connected to and what type of tap it is.  A tap can be either a span or a tap.  

```
build2# cat config.sample.json 
{
    "bridge_config": {
        "control": {
            "dynamic": false, 
            "if": "bridge0"
        }, 
        "data": {
            "dynamic": true
        }
    }, 
    "topology": {
        "control": {
            "taps": {
                "appliance_mgmt0": {
                    "mode": "tap"
                }, 
                "client_control": {
                    "mode": "tap"
                }, 
                "router_control": {
                    "mode": "tap"
                }
            }
        }, 
        "data": {
            "taps": {
                "appliance_inject0": {
                    "mode": "tap"
                }, 
                "appliance_span0": {
                    "mode": "span"
                }, 
                "client_data": {
                    "mode": "tap"
                }, 
                "router_data": {
                    "mode": "tap"
                }
            }
        }
    }
}

```

## Running the netmanager

### Creating the network

% ./netmanager.py create -f generated.json --cfg config.sample.json​

You'll wind up with a file "generated.json" that has the topology in it.

### Displaying the network config

You can then show the taps:

```
build2# ./netmanager.py show-taps -f ./generated.json
{
    "appliance_inject0": "tap4", 
    "appliance_mgmt0": "tap2", 
    "appliance_span0": "tap3", 
    "client_control": "tap5", 
    "client_data": "tap6", 
    "router_control": "tap0", 
    "router_data": "tap1"
}
```

### Tearing down the network

Run the cleanup command:

```
./netmanager.py cleanup -f generated.json
```

## Using this with bhyve

Make two FreeBSD vms, both should have vtnet0 as dhcp and vtnet1 should be as follows:

"inet 192.168.190.1 netmask 255.255.255.255" on "myrouter"
"inet 192.168.190.2 netmask 255.255.255.255" on "fakeappliance"

```
# ./netmanager.py show-taps -f ./generated.json
{
    "appliance_inject0": "tap4", 
    "appliance_mgmt0": "tap2", 
    "appliance_span0": "tap3", 
    "client_control": "tap5", 
    "client_data": "tap6", 
    "router_control": "tap0", 
    "router_data": "tap1"
}
```

Now run your vms:

```
appliance/tools/vmrun-current.sh -d ./myrouter.raw -t tap0 -m 4G -t tap1 router1
appliance/tools/vmrun-current.sh -d ./fakeappliance.raw -t tap2 -t tap4 -t tap3 -m 4G  fakeappliance
```

What will happen now is that you'll wind up with two vms running.

Each vm will have vtnet0 on the bridge0 network and they should dhcp against it.
Both vms will have vtnet1 on the private bridge1 network.
Finally the 'fakeappliance' vm will have vtnet2 be a span interface to monitor bridge1

After they boot up, you can log into fakeappliance and set its vtnet1 interface ip to "inet 192.168.190.2 netmask 255.255.255.0​"  <- note the ".2"

After the interfaces settle you should be able to ping from 192.168.190.2 to 192.168.190.1 and you should also be able to run "tcpdump" on fakeappliance's vtnet2 by doing the following commands:

```
ifconfig vtnet2 up
tcpdump -nei vtnet2
```

Then you should also see the span traffic there.

Enjoy!
