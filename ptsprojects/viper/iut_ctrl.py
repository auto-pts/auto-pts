import subprocess
import shlex

BTPROXY = None

class BtproxyCtl:
    '''Btproxy Tool Control Class'''

    def __init__(self):
        '''Constructor'''

        self.__proc_btproxy = None

    def new_btproxy(self):
        p_run_cmd = "/home/kolodgrz/src/bluez/tools/btproxy -u"

        # TODO check btproxy process for errors
        self.__proc_btproxy = subprocess.Popen(shlex.split(p_run_cmd), shell = False,
                                               stdout = subprocess.PIPE,
                                               stderr = subprocess.STDOUT)

    def close_btproxy(self):
        if self.__proc_btproxy != None:
            self.__proc_btproxy.terminate()

def cleanup():
    # Clanup routine

    if BTPROXY != None:
        BTPROXY.close_btproxy()

def init():
    """Main."""

    global BTPROXY

    BTPROXY = BtproxyCtl()
    BTPROXY.new_btproxy()
