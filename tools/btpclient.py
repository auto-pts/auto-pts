#!/usr/bin/env python

import os
import sys
import socket
import signal
import errno
import shlex
import logging
import readline
import binascii
import threading
import subprocess
from functools import wraps

# to be able to find ptsprojects module
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ptsprojects.zephyr import btpparser
from ptsprojects.zephyr import btpdef
from ptsprojects.zephyr.btp import CORE, GAP, GATTS
from ptsprojects.zephyr.iutctl import get_qemu_cmd

sock = None
conn = None
addr = None
QEMU_UNIX_PATH = "/tmp/bt-stack-tester"
QEMU_PROCESS = None

class TimeoutError(Exception):
    pass

class Completer:
    def __init__(self, words):
        self.menu = words[0]
        self.core = words[1]
        self.gap = words[2]
        self.gatts = words[3]

    def complete(self, text, state):
        words_arr = text.split()
        words_cnt = len(words_arr)

        if words_cnt == 1:
            if words_arr[0] in ['core', 'gap', 'gatts']:
                if words_arr[0] == 'core':
                    c = self.core.keys()
                    self.matching_words = ["core " + s for s in c]
                elif words_arr[0] == 'gap':
                    c = self.gap.keys()
                    self.matching_words = ["gap " + s for s in c]
                elif words_arr[0] == 'gatts':
                    c = self.gatts.keys()
                    self.matching_words = ["gatts " + s for s in c]
            else:
                c = [ w for w in self.menu if w.startswith(words_arr[0]) ]
                self.matching_words = c
        elif words_cnt == 2:
            if words_arr[0] == "core":
                c = [ w for w in self.core if w.startswith(words_arr[1]) ]
                self.matching_words = ["core " + s for s in c]
            elif words_arr[0] == "gap":
                c = [ w for w in self.gap if w.startswith(words_arr[1]) ]
                self.matching_words = ["gap " + s for s in c]
            elif words_arr[0] == "gatts":
                c = [ w for w in self.gatts if w.startswith(words_arr[1]) ]
                self.matching_words = ["gatts " + s for s in c]
            else:
                return None

        if not text: # words_cnt == 0
            self.matching_words = self.menu.keys()

        try:
            return self.matching_words[state]
        except IndexError:
            return None

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

def help(params):
    print "Available commands: "
    menu = cmds.viewkeys()
    print list(menu)

    print "\nEvery command has its own minihelp, type: \"<cmd> help\", to get specific help"

def exec_cmd(choice, params):
    ch = choice.lower()
    try:
        cmds[ch](params)
    except KeyError:
        print "error: Invalid selection, please try again.\n"
        cmds['help'](params)
    except TimeoutError:
        print "error: requested command timed out"

def clean_conn():
    global sock, conn, addr

    sock = None
    conn = None
    addr = None

def start_zephyr(params):
    logging.debug("%s %r", start_zephyr.__name__, params)

    if len(params) == 1 and params[0] == "help":
        print "\nUsage:"
        print "\tstart-zephyr kernel_image"
        print "\nNote: xterm must be installed for this command to work"
        print "\nDescription:"
        print "\nStarts Zephyr QEMU process"
        print "\nExample:"
        print "\tstart-zephyr ./microkernel.elf"
        return

    global QEMU_PROCESS

    if QEMU_PROCESS:
        print "Zephyr is already up and running"
        return

    if len(params) != 1:
        print "error: kernel image file not specified"
        return

    kernel_image = params[0]

    if not os.path.isfile(kernel_image):
        print "QEMU kernel image %s is not a file!" % repr(kernel_image)
        return

    qemu_cmd = get_qemu_cmd(kernel_image)

    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    # why running under xterm? cause of -serial mon:stdio: running qemu as
    # subprocess make terminal input impossible in the parent application, also
    # it is impossible to daemonize qemu
    xterm_qemu_cmd = ('xterm -e sh -c "%s 2>&1|tee qemu-%s.log"' %
                      (qemu_cmd, script_name_no_ext))

    # start listening
    logging.debug("Starting listen thread")
    thread = threading.Thread(target = listen, args = ([],))
    thread.start()

    # start qemu
    logging.debug("Starting qemu: %r", xterm_qemu_cmd)
    QEMU_PROCESS = subprocess.Popen(shlex.split(xterm_qemu_cmd))

    thread.join()

    print "Zephyr started"

def stop_zephyr(params = []):
    logging.debug("%s %r", stop_zephyr.__name__, params)

    if len(params) == 1 and params[0] == "help":
        print "\nUsage:"
        print "\tstop-zephyr"
        print "\nDescription:"
        print "\nStops Zephyr QEMU process"
        return

    global QEMU_PROCESS

    if not QEMU_PROCESS:
        print "Zephyr is not running"
        return

    if QEMU_PROCESS:
        if QEMU_PROCESS.poll() is None:
            logging.debug("qemu process is running, will terminate it")
            QEMU_PROCESS.terminate()
            QEMU_PROCESS.wait() # do not let zombies take over
            logging.debug("Completed termination of qemu process")
            QEMU_PROCESS = None

def send(params):
    logging.debug("%s %r", send.__name__, params)

    if len(params) == 1 and params[0] == "help":
        print "\nUsage:"
        print "\tsend <service_id> <opcode> <index> [<data>]"
        print "\nExample:"
        print "\tsend 0 1 0 01"
        print "\nDescription:"
        print "\tsend <int> <int> <int> <hex>"
        print "\t(send SERVICE_ID_CORE = 0x00, OP_CORE_REGISTER_SERVICE = 0x03,"\
              "Controller Index = 0, SERVICE_ID_GAP = 0x01...)"
        return

    if conn_chk() is False:
        return

    try:
        svc_id = params[0]
        op = params[1]
        ctrl_index = params[2]
    except IndexError:
        print "Invalid send frame format/data (check - send help)"
        return

    try:
        data = params[3]
    except IndexError:
        data = ""

    service_ids = {item : getattr(btpdef, item) for item in dir(btpdef)
                   if item.startswith("BTP_SERVICE_ID")}

    # Parse Service ID
    try:
        int_svc_id = int(svc_id)
    except ValueError:
        print "error: Wrong svc_id format, possible values: ", service_ids
        return

    if int_svc_id not in service_ids.values():
        print ("error: Given service ID %c not supported, supported are %s!" %
               (int_svc_id, repr(service_ids.values())))
        return

    # Parse Opcode
    try:
        int_op = int(op)
    except ValueError:
        print "error: Wrong op format, should be an int: \"0-255\""
        return

    # Parse Controler Index
    try:
        int_ctrl_index = int(ctrl_index)
    except ValueError:
        print "error: Wrong Controler Index format, shoulb be an int: \"0-255\""
        return

    # Parse Data
    try:
        hex_data = binascii.unhexlify(data)
    except TypeError:
        print "error: Wrong data type, should be e.g.: \"0011223344ff\""
        return

    frame = btpparser.enc_frame(int_svc_id, int_op, int_ctrl_index, hex_data)

    logging.debug("Sending: %d %d %d %r" %
                  (int_svc_id, int_op, int_ctrl_index, hex_data))
    logging.debug("Sending frame: %r" % frame)

    try:
        conn.send(frame)
    except socket.error as serr:
        if serr.errno == errno.EPIPE:
            clean_conn()
            print "error: Connection error, please connect btp again"
            return

    try:
        receive("")
    except TimeoutError:
        print "error: problem with receiving response from server"

    return

@timeout(2)
def receive(params):
    logging.debug("%s %r", receive.__name__, params)

    if len(params) == 1 and params[0] == "help":
        print "\nUsage:"
        print "\treceive"
        print "\nDescription:"
        print "\tThis method waits (timeout = 2sec) and reads data from btp socket"
        return

    if conn_chk() is False:
        return

    toread_hdr_len = btpparser.HDR_LEN
    hdr = bytearray(toread_hdr_len)
    hdr_memview = memoryview(hdr)

    #Gather frame header
    while toread_hdr_len:
        try:
            nbytes = conn.recv_into(hdr_memview, toread_hdr_len)
            hdr_memview = hdr_memview[nbytes:]
            toread_hdr_len -= nbytes
        except:
            continue

    tuple_hdr = btpparser.dec_hdr(hdr)
    toread_data_len = tuple_hdr.data_len

    print "Received: hdr: ", tuple_hdr
    logging.debug("Received: hdr: %r %r", tuple_hdr, hdr)

    data = bytearray(toread_data_len)
    data_memview = memoryview(data)

    #Gather optional frame data
    while toread_data_len:
        try:
            nbytes = conn.recv_into(data_memview, toread_data_len)
            data_memview = data_memview[nbytes:]
            toread_data_len -= nbytes
        except:
            continue

    tuple_data = btpparser.dec_data(data)

    hex_str = binascii.hexlify(tuple_data[0])
    hex_str_byte = " ".join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
    print "Received data (hex): %s" % hex_str_byte
    print "Received data (ascii):", tuple_data

    logging.debug("Received data %r %r", data, tuple_data)

def listen(params):
    logging.debug("%s %r", listen.__name__, params)
    global sock
    global conn
    global addr

    if len(params) == 1 and params[0] == "help":
        print "\nUsage:"
        print "\tlisten"
        print "\nDescription:"
        print "\tThis method starts listening btpclient for btpserver connection with 10sec timeout"
        return

    if conn is not None:
        print "btpclient is already connected to btp server"
        return

    if sock is None:
        if os.path.exists(QEMU_UNIX_PATH):
            os.remove(QEMU_UNIX_PATH)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(QEMU_UNIX_PATH)

        #queue only one connection
        sock.listen(1)
        print "created fd %s, listening..." % QEMU_UNIX_PATH

    try:
        conn, addr = sock.accept()
        conn.setblocking(0)
        print "btp server connected successfully"

    except KeyboardInterrupt:
        print "\nListen interrupted!"
        conn = None
        addr = None

def exit(params):
    sys.exit(0)

def disconnect(params):
    if len(params) == 1 and params[0] == "help":
        print "\nUsage:"
        print "\tdisconnect"
        print "\nDescription:"
        print "\tClear btp socket connection data"
        return

    if conn_chk() is False:
        return

    clean_conn()
    print "info: Connection cleared"

def generic_srvc_cmd_handler(svc, cmd):
    logging.debug("%s svc=%r cmd=%r",
                  generic_srvc_cmd_handler.__name__, svc, cmd)

    if len(cmd) == 0 or len(cmd) == 1 and cmd == "help":
        print "\nAdditional command must be given"
        print "\nPossible core commands:"
        print svc.keys()
        return

    # a tuple representing btp packet
    btp_cmd = svc[cmd[0]]

    if len(btp_cmd) == 0:
        print "Command not yet defined"
        return

    frame = []

    # 3 cause: service id, opcode, controller index
    for i in range(3):
        frame.append(str(btp_cmd[i]))

    data = None

    # add data if there is any
    if len(btp_cmd) > 3:
        data = str(btp_cmd[3])

        if len(data) == 1:
            frame.append("0%s" %  data)
        else:
            frame.append(binascii.hexlify(''.join(data)))

    elif len(cmd) > 1: # some commands pass data from command line
        data = cmd[1]
        frame.append(data)

    logging.debug("frame %r", frame)

    send(frame)

def core_cmd(params):
    generic_srvc_cmd_handler(CORE, params)

def gap_cmd(params):
    generic_srvc_cmd_handler(GAP, params)

def gatts_cmd(params):
    generic_srvc_cmd_handler(GATTS, params)

def conn_chk():
    if conn is None:
        print "error: btp client is not connected"
        return False

    return True

def cmd_loop():
    while True:
        input = raw_input(" >> ")

        if input == '':
            continue

        words = input.split()
        choice = words[0]
        params = words[1:]

        exec_cmd(choice, params)

def setup_completion():
    words = (cmds, CORE, GAP, GATTS)
    completer = Completer(words)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.complete)
    readline.set_completer_delims('')

def main():
    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    format = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
              "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format = format,
                        filename = log_filename,
                        filemode = 'w',
                        level = logging.DEBUG)

    history_filename = os.path.expanduser("~/.%s_history" % script_name_no_ext)

    try:
        if os.path.exists(history_filename):
            logging.debug("Reading history file %s" % history_filename)
            readline.read_history_file(history_filename)

        setup_completion()
        cmd_loop()

    except KeyboardInterrupt: # Ctrl-C
        sys.exit("")

    except EOFError: # Ctrl-D
        sys.exit("")

    # SystemExit is thrown in arg_parser.parse_args and in sys.exit
    except SystemExit:
        raise # let the default handlers do the work

    except:
        import traceback
        traceback.print_exc()
        sys.exit(16)

    finally:
        logging.debug("Exiting...")
        if QEMU_PROCESS:
            stop_zephyr()
        logging.debug("Writing history file %s" % history_filename)
        readline.write_history_file(history_filename)

cmds = {
    'help': help,
    'listen': listen,
    'send': send,
    'receive': receive,
    'exit': exit,
    'disconnect': disconnect,
    'start-zephyr' : start_zephyr,
    'stop-zephyr' : stop_zephyr,

    'core': core_cmd,
    'gap': gap_cmd,
    'gatts': gatts_cmd,
}

if __name__ == "__main__":
    main()
