"""
    The arg parsing 
"""
import argparse

import psutil


def create_parser():
    """
        Create the argument parser with some default arguments

        Returns:
            The arguments
    """
    parser = argparse.ArgumentParser(
        description="Welcome to deepdos, the machine learning/ai based ddos analysis/mitigation service"
    )
    # Read in the interface
    parser.add_argument(
        "-i",
        action="store",
        dest="interface",
        help="the network interface for deepdos to listen to",
        default=None,
    )

    # Read in the naughty count
    parser.add_argument(
        "-n",
        action="store",
        dest="naughty_count",
        type=int,
        help="the amount of malicious flows that can come from a given address",
        default=10,
    )

    # Find all user interfaces
    parser.add_argument(
        "--find-interface",
        action="store_true",
        dest="find_interface",
        help="List all of your devices network interfaces. Good if you don't know what interfaces your device has",
        default=False,
    )

    # Activate firemode
    parser.add_argument(
        "--firewall-linux",
        action="store_true",
        dest="firewall_linux",
        help="Turn on firewall mode for linux. The naughty list or -n argument is default to 10",
        default=False,
    )

    parser.add_argument()

    return parser.parse_args()


def obtain_interface_data(desired_interface):
    """
        Obtain the interface data and return a dictionary that contains
        the information of each associated address to that interface
    """
    addrs = psutil.net_if_addrs()
    data = {}

    # Iterate through the all of the interfaces
    if desired_interface in addrs:
        nic = addrs[desired_interface]
        for info in nic:
            # add data for the current address family
            data[f"{info.family}"] = {
                "address": str(info.address),
                "netmask": str(info.netmask),
                "broadcast": str(info.broadcast),
                "ptp": str(info.ptp),
            }
        return data
    else:
        # Couldn't find the requested interface
        raise ValueError(f"Couldn't find the requested interface: {desired_interface}")


def list_interface_data():
    addrs = psutil.net_if_addrs()
    for address, nic in addrs.items():
        print(f"interface: {address}")
        # Iterate through each associated address and it's information
        for info in nic:
            print("\tAssociated address:")
            print(f"\t\tFamily: {info.family}")
            print(f"\t\tAddress: {info.address}")
            print(f"\t\tNetmask: {info.netmask}")
            print(f"\t\tBroadcast: {info.broadcast}")
            print(f"\t\tPTP: {info.ptp}")
        print()

    print(
        "Pick one of these interfaces to listen to traffic on, and then rerun the command with it :)"
    )
    exit()


def parse_args():
    """
        Parse the arguments of the arg parser
        Return the options that will be used to configure the main loop
    """
    args = create_parser()
    options = {}

    # Find all interfaces if specified and then exit
    if args.find_interface:
        # List all of the interface data
        list_interface_data()

    # Store the interface and interface data
    if args.interface:
        options["interface"] = args.interface
        options["interface_data"] = obtain_interface_data(args.interface)
        print(options["interface_data"])
        print(args.interface)
    else:
        print(
            "You need to provide a network interface for deepdos to listen on, or run --find-interface to list all of them."
        )
        exit()

    # Check if firewall mode is enabled
    if args.firewall_linux:
        options["firewall_mode"] = True
    else:
        options["firewall_mode"] = False

    return options