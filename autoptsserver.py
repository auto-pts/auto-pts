import os
import sys
import logging
import xmlrpclib
import System.IO.IOException
from SimpleXMLRPCServer import SimpleXMLRPCServer

import ptscontrol

log = logging.debug

# TCP server port
PORT = 65000

class PyPTSWithXmlRpcCallback(ptscontrol.PyPTS):
    """A child class that adds support of xmlrpc PTS callbacks to PyPTS"""

    def __init__(self):
        """Constructor"""
        ptscontrol.PyPTS.__init__(self)

        # address of the auto-pts client that started it's own xmlrpc server to
        # receive callback messages
        self.client_address = None
        self.client_port = None
        self.client_xmlrcp_proxy = None

    def register_xmlrpc_ptscallback(self, client_address, client_port):
        """Registers client callback. xmlrpc proxy/client calls this method
        to register its callback

        client_address -- IP address
        client_port -- TCP port
        """

        self.client_address = client_address
        self.client_port = client_port

        self.client_xmlrcp_proxy = xmlrpclib.ServerProxy(
            "http://{}:{}/".format(self.client_address, self.client_port),
            allow_none = True)

        log("Created XMR RCP auto-pts client proxy, provides methods: %s" %
            self.client_xmlrcp_proxy.system.listMethods())

        self.register_ptscallback(self.client_xmlrcp_proxy)

    def unregister_xmlrpc_ptscallback(self):
        """Unregisters the client callback"""
        log("%s", self.unregister_xmlrpc_ptscallback.__name__)
        self.unregister_ptscallback()

        self.client_address = None
        self.client_port = None
        self.client_xmlrcp_proxy = None

def main():
    """Main."""

    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    try:
        logging.basicConfig(format = '%(name)s [%(asctime)s] %(message)s',
                            filename = log_filename,
                            filemode = 'w',
                            level = logging.DEBUG)
    except IOError as e:
        print "I/O error({0}): {1}, script needs to be run as administrator".format(e.errno, e.strerror)
        sys.exit()

    print "Starting PTS"

    pts = PyPTSWithXmlRpcCallback()

    print "Serving on port {}...".format(PORT)

    server = SimpleXMLRPCServer(("", PORT), allow_none = True)
    server.register_instance(pts)
    server.register_introspection_functions()
    server.serve_forever()

if __name__ == "__main__":
    main()
