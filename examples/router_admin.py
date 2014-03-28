#!/usr/bin/python
## ===========
## pysap - Python library for crafting SAP's network protocols packets
##
## Copyright (C) 2014 Core Security Technologies
##
## The library was designed and developed by Martin Gallo from the Security
## Consulting Services team of Core Security Technologies.
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##==============

# Standard imports
import logging
from optparse import OptionParser, OptionGroup
# External imports
from scapy.config import conf
from scapy.supersocket import socket
# Custom imports
from pysap.SAPNI import SAPNI, SAPNIStreamSocket
from pysap.SAPRouter import SAPRouter, router_is_error, router_is_control


# Set the verbosity to 0
conf.verb = 0


# Command line options parser
def parse_options():

    description = \
    """This example script connects with a SAP Router server and allows
    perform administrative tasks. The options are the ones found on the
    regular SAP Router tool with the addition of some undocumented
    operation codes.

    """

    epilog = \
    """pysap - http://corelabs.coresecurity.com/index.php?module=Wiki&action=view&type=tool&name=pysap"""

    usage = "Usage: %prog [options] -d <remote host>"

    parser = OptionParser(usage=usage, description=description, epilog=epilog)

    target = OptionGroup(parser, "Target")
    target.add_option("-d", "--remote-host", dest="remote_host", help="Remote host [%default]", default="127.0.0.1")
    target.add_option("-p", "--remote-port", dest="remote_port", type="int", help="Remote port [%default]", default=3299)
    target.add_option("--router-version", dest="router_version", type="int", help="SAP Router version to use [retrieve from the remote SAP Router]")
    parser.add_option_group(target)

    command = OptionGroup(parser, "Command")
    command.add_option("-s", "--stop-router", dest="stop", action="store_true", help="Stop router request")
    command.add_option("-o", "--soft-shutdown", dest="soft", action="store_true", help="Soft shutdown request")
    command.add_option("-l", "--router-info", dest="info", action="store_true", help="Router info request")
    command.add_option("-P", "--info-pass", dest="info_password", action="store", help="Password for info request")
    command.add_option("-n", "--new-route", dest="new_route", action="store_true", help="New route table request")
    command.add_option("-t", "--toggle-trace", dest="trace", action="store_true", help="Toggle trace request")
    command.add_option("-c", "--cancel-route", dest="cancel", action="store", help="Cancel route request")
    command.add_option("-b", "--dump-buffer", dest="dump", action="store_true", help="Dump buffers request")
    command.add_option("-f", "--flush-buffer", dest="flush", action="store_true", help="Flush buffers request")
    command.add_option("-z", "--hide-errors", dest="hide", action="store_true", help="Hide errors info")
    command.add_option("--set-peer-trace", dest="set_peer", action="store", help="Set peer trace (undocumented command)")
    command.add_option("--clear-peer-trace", dest="clear_peer", action="store", help="Clear peer trace (undocumented command)")
    command.add_option("--trace-connection", dest="trace_conn", action="store", help="Trace connection (undocumented command)")
    parser.add_option_group(command)

    misc = OptionGroup(parser, "Misc options")
    misc.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Verbose output [%default]")
    parser.add_option_group(misc)

    (options, _) = parser.parse_args()

    if not options.remote_host:
        parser.error("Remote host is required")

    return options


# Retrieve the version of the remote SAP Router
def get_router_version(connection):
    r = connection.sr(SAPRouter(type=SAPRouter.SAPROUTER_CONTROL, version=40, opcode=1))
    if router_is_control(r) and r.opcode == 2:
        return r.version
    else:
        return None


# Main function
def main():
    options = parse_options()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)

    response = False

    p = SAPRouter(type=SAPRouter.SAPROUTER_ADMIN)

    if options.stop:
        p.adm_command = 5
        print "[*] Requesting stop of the remote SAP Router"

    elif options.soft:
        p.adm_command = 9
        print "[*] Requesting a soft shutdown of the remote SAP Router"
        response = True

    elif options.info:
        p.adm_command = 2
        if options.info_password:
            if len(options.info_password) > 19:
                print "[*] Password too long, truncated at 19 characters"
            p.adm_password = options.info_password
            print "[*] Requesting info using password", p.adm_password
        else:
            print "[*] Requesting info"
        response = True

    elif options.new_route:
        p.adm_command = 3
        print "[*] Requesting a refresh of the router table"

    elif options.trace:
        p.adm_command = 4
        print "[*] Requesting a toggle on the trace settings"

    elif options.cancel:
        p.adm_command = 6
        p.adm_client_ids = map(int, options.cancel.split(","))
        print "[*] Requesting a cancel of the route(s) with client id(s) %s" % p.adm_client_ids
        response = True

    elif options.dump:
        p.adm_command = 7
        print "[*] Requesting a dump of the buffers"

    elif options.flush:
        p.adm_command = 8
        print "[*] Requesting a flush of the buffers"

    elif options.hide:
        p.adm_command = 14
        print "[*] Requesting a hide on the errors to clients"
        response = True

    elif options.set_peer:
        p.adm_command = 10
        p.adm_address_mask = options.set_peer
        print "[*] Request a set peer trace for the address mask %s" % p.adm_address_mask
        response = True

    elif options.clear_peer:
        p.adm_command = 11
        p.adm_address_mask = options.clear_peer
        print "[*] Request a clear peer trace for the address mask %s" % p.adm_address_mask
        response = True

    elif options.trace_conn:
        p.adm_command = 12
        p.adm_client_ids = map(int, options.trace_conn.split(","))
        print "[*] Requesting a connection trace with client id(s) %s" % p.adm_client_ids
        response = True

    else:
        print "[*] No command specified !"
        return

    # Initiate the connection
    sock = socket.socket()
    sock.connect((options.remote_host, options.remote_port))
    conn = SAPNIStreamSocket(sock)
    print "[*] Connected to the SAP Router %s:%d" % (options.remote_host, options.remote_port)

    # Retrieve the router version used by the server if not specified
    if options.router_version:
        p.version = options.router_version
    else:
        p.version = get_router_version(conn) or p.version
    print "[*] Using SAP Router version %d" % p.version

    # Send the router admin request
    print "[*] Sending Router Admin packet"
    if options.verbose:
        p.show2()
    conn.send(p)

    # Grab the response if required
    if response:

        # Some responses has no SAPRouter's packet format and are raw strings,
        # we need to get the SAP NI layer first and then check if we could go
        # down to the SAPRouter layer.
        response = conn.recv()[SAPNI]
        if SAPRouter in response and response[SAPRouter].payload:
            response = response[SAPRouter]

        # If the response is an error, print and exit
        if router_is_error(response):
            print "[*] Error requesting info:"
            if options.verbose:
                response.show2()
            else:
                print response.err_text_value

        # Otherwise, print all the packets sent by the SAP Router
        else:
            print "[*] Response:"
            try:
                while (response):
                    print response.payload
                    response = conn.recv()
            except:
                pass


if __name__ == "__main__":
    main()