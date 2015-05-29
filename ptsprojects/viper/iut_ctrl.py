import subprocess
import os
import shlex

BTPROXY = None
VIPER_P = None

BTPROXY_PATH = "/tmp/bt-server-bredr"
QEMU_PATH = "/home/kolodgrz/bin/qemu-system-i386"

class ViperCtl:
    '''Viper System Control Class'''

    @staticmethod
    def new_viper(app_path, app_name):
        global VIPER_P

        if not os.path.exists(app_path):
            raise Exception("wrong qemu project path '%s'" % app_path)

        if not os.path.exists(app_path + "outdir/" + app_name):
            raise Exception("wrong project binary file name '%s' - doesn't exist"
                            % (app_path + "outdir/" + app_name))

        v_run_cmd = "%s -m 32 -cpu qemu32 -no-reboot -nographic -display none " \
                    "-net none -clock dynticks -no-acpi -balloon none " \
                    "-no-hpet -L /usr/share/qemu -bios bios.bin -serial " \
                    "mon:stdio -machine type=pc-0.14 -pidfile qemu.pid " \
                    "-serial unix:/tmp/bt-server-bredr -kernel %s" \
                    % (QEMU_PATH, app_path + "outdir/" + app_name)

        # TODO check if viper process has started correctly
        VIPER_P = subprocess.Popen(shlex.split(v_run_cmd), shell = False,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.STDOUT)

    @staticmethod
    def close_viper():
        if VIPER_P != None:
            VIPER_P.terminate()

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
    # TODO extra cleanup check since post routine should handle this
    ViperCtl.close_viper()

def init():
    """Main."""

    global BTPROXY

    BTPROXY = BtproxyCtl()
    BTPROXY.new_btproxy()
