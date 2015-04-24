from SimpleXMLRPCServer import SimpleXMLRPCServer

import ptscontrol

# TCP server port
PORT = 65000

def main():
    """Main."""

    pts = ptscontrol.PyPTS()

    print "Serving on port {}...".format(PORT)

    server = SimpleXMLRPCServer(("", PORT))
    server.register_instance(pts)
    server.register_introspection_functions()
    server.serve_forever()

if __name__ == "__main__":
    main()
