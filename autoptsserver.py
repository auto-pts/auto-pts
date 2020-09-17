#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import os
import wmi
import sys
import logging
import xmlrpc.client
import xmlrpc.server
import winutils
import ptscontrol
from config import SERVER_PORT

log = logging.debug


class PyPTSWithXmlRpcCallback(ptscontrol.PyPTS):
    """A child class that adds support of xmlrpc PTS callbacks to PyPTS"""

    def __init__(self):
        """Constructor"""

        log("%s", self.__init__.__name__)

        ptscontrol.PyPTS.__init__(self)

        # address of the auto-pts client that started it's own xmlrpc server to
        # receive callback messages
        self.client_address = None
        self.client_port = None
        self.client_xmlrpc_proxy = None

    def register_xmlrpc_ptscallback(self, client_address, client_port):
        """Registers client callback. xmlrpc proxy/client calls this method
        to register its callback

        client_address -- IP address
        client_port -- TCP port
        """

        log("%s %s %d", self.register_xmlrpc_ptscallback.__name__,
            client_address, client_port)

        self.client_address = client_address
        self.client_port = client_port

        self.client_xmlrpc_proxy = xmlrpc.client.ServerProxy(
            "http://{}:{}/".format(self.client_address, self.client_port),
            allow_none=True)

        log("Created XMR RPC auto-pts client proxy, provides methods: %s" %
            self.client_xmlrpc_proxy.system.listMethods())

        self.register_ptscallback(self.client_xmlrpc_proxy)

    def unregister_xmlrpc_ptscallback(self):
        """Unregisters the client callback"""

        log("%s", self.unregister_xmlrpc_ptscallback.__name__)

        self.unregister_ptscallback()

        self.client_address = None
        self.client_port = None
        self.client_xmlrpc_proxy = None


def main():
    """Main."""
    winutils.exit_if_admin()

    script_name = os.path.basename(sys.argv[0])  # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    format = ("%(asctime)s %(name)s %(levelname)s : %(message)s")

    logging.basicConfig(format=format,
                        filename=log_filename,
                        filemode='w',
                        level=logging.DEBUG)

    c = wmi.WMI()
    for iface in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
        print("Local IP address: %s DNS %r" % (iface.IPAddress, iface.DNSDomain))

    print("Starting PTS ...")
    pts = PyPTSWithXmlRpcCallback()
    print("OK")

    print("Serving on port {} ...".format(SERVER_PORT))

    server = xmlrpc.server.SimpleXMLRPCServer(("", SERVER_PORT), allow_none=True)
    server.register_instance(pts)
    server.register_introspection_functions()
    server.serve_forever()


if __name__ == "__main__":
    main()
