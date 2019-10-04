import fcntl
import socket
import struct
import time
from abc import ABC, abstractmethod

import iptc


class Offender:
    """
        Offender container for connections that are suspicious
    """

    def __init__(self, src, port, protocol, outbound):
        self.src = src
        self.offenses = 1
        self.port_mappings = set((port, protocol))
        self.outbound = outbound

    def add_offense(self, port, protocol):
        """
            Add an offense to the offender
        """
        self.offenses += 1
        self.port_mappings.add((port, protocol))


class Firewall(ABC):
    """
        Firewall class manager for adding rules to our firewall
    """

    def __init__(self, interface: str, interface_data: dict, naughty_count: int):
        # Setup general data
        self.interface = interface
        self.interface_data = interface_data
        self.naughty_count = naughty_count
        self.offenders = {}
        self.input_banned = {}
        self.output_banned = {}
        self.ip_version = 2

    @staticmethod
    def create_firewall(
        interface: str, interface_data: dict, firewall_type: str, naughty_count: int
    ):
        """
            Firewall factory. Will create a firewall based on the type of firewall that is passed in.
            Currently, this function only supports linux based operating systems
        """
        # Check the firewall type
        if firewall_type == "linux":
            return IPtable(interface, interface_data, naughty_count)

        # Invalid firewall
        raise ValueError(
            "linux is the only supported operating system for firewall mode. You entered: {firewall_type}"
        )

    @abstractmethod
    def create_rule(self, offender: Offender):
        """
            Create a firewall rule given:
                ips - tuple(from_ip, to_ip) 
                ports - tuple(from_port, to_port)
                protocol: "TCP"
        """
        return NotImplemented

    @abstractmethod
    def remove_rules(self):
        return NotImplemented

    def track_ips(self, connection_list):
        """
            Track ips that have been marked malicious
        """
        interface_info = self.interface_data[self.ip_version]
        local_ip = interface_info["address"]

        # Iterate through the malicious ips list
        for ips, ports, protocol in connection_list:
            from_ip, to_ip = ips
            from_port, to_port = ports

            # Was this connection outbound or inbound?
            outbound = True if from_ip == local_ip else False
            port = from_port if outbound else to_port
            connection = f"{from_ip}/{to_ip}"

            # Check if the connection occurred
            if connection in self.offenders:
                offender = self.offenders[connection]

                # They've had way too many violations, it's time to ban this malicious data.
                if offender.offenses > self.naughty_count:
                    self.create_rule(offender)
                    del self.offenders[connection]
                else:
                    print(" - Adding an offense")
                    offender.add_offense(port, protocol)

            else:
                # Register the connection offender :(
                self.offenders[connection] = Offender(
                    connection, port, protocol, outbound
                )


class IPtable(Firewall):
    """
        Linux based firewall class
    """

    def __init__(self, interface, interface_data, naughty_count):
        super().__init__(interface, interface_data, naughty_count)
        # Instantiate the filter table and all input/output rules on it
        self.filter_table = iptc.Table(iptc.Table.FILTER)
        self.input_chain = iptc.Chain(self.filter_table, "INPUT")
        self.output_chain = iptc.Chain(self.filter_table, "OUTPUT")

    def create_rule(self, offender):
        """
            Create a firewall rule that will disable communication between the from_ip and
            to_ip on the desired interface for the specified protocol.
        """
        print("- Creating rule for an offender")
        return

        # Unpack some variables
        interface_info = self.interface_data[self.ip_version]
        local_ip = interface_info["address"]

        # Get the from ip and to ip from the offendesr src
        from_ip, to_ip = offender.src.split("/")

        ip = from_ip if from_ip == local_ip else to_ip

        # Create a rule to drop packets for this connection on the currently hooked
        # up interface
        rule = iptc.Rule()
        rule.in_interface = self.interface
        rule.src = ip
        rule.target = iptc.Target(rule, "DROP")

        # Iterate through all of the communication channels
        # and add matches for them
        for port, protocol in list(offender.port_mappings):
            match = iptc.Match(rule, protocol)
            match.dport = port
            rule.add_match(match)

        # Choose which chain to output to
        if offender.outgoing:
            self.output_chain.insert_rule(rule)
            self.output_banned[rule.src] = time.time() // 60
        else:
            self.input_chain.insert_rule(rule)
            self.input_banned[rule.src] = time.time() // 60

    def remove_rules(self):
        pass