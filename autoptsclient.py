#!/usr/bin/env python

import xmlrpclib

PORT = 65000

def main():
    """Main."""

    proxy = xmlrpclib.ServerProxy("http://10.237.67.148:{}/".format(PORT))
    print proxy.system.listMethods()
    print proxy.system.methodHelp("get_version")
    print proxy.system.methodHelp("bd_addr")
    print proxy.system.methodSignature("get_version")
    print proxy.system.methodSignature("bd_addr")

    print proxy.bd_addr()
    print "%x" % proxy.get_version()

if __name__ == "__main__":
    main()
