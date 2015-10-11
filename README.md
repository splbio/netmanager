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

```./netmanager.py cleanup -f generated.json```

Enjoy!
