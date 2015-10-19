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
from ptsprojects.testcase import AbstractMethodException

sock = None
conn = None
addr = None
QEMU_UNIX_PATH = "/tmp/bt-stack-tester"
QEMU_PROCESS = None

def get_my_name():
    """Returns name of the script without extension"""
    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    return script_name_no_ext

class TimeoutError(Exception):
    pass

class Completer:
    def __init__(self, options):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.ERROR)
        # use DEBUG for extra info
        # self.log.setLevel(logging.DEBUG)

        self.log.debug("%s.%s %r", self.__class__, self.__init__.__name__,
                       options)

        self.options = options

        self.matches = []

    def find_matches(self, text):

        origline = readline.get_line_buffer()
        begin = readline.get_begidx()
        end = readline.get_endidx()
        being_completed = origline[begin:end]
        words = origline.split()

        self.log.debug('origline=%r', repr(origline))
        self.log.debug('begin=%r', begin)
        self.log.debug('end=%r', end)
        self.log.debug('being_completed=%r', being_completed)
        self.log.debug('words=%r', words)

        if not words:
            self.matches = sorted(self.options.keys())
        else:
            # first word
            if begin == 0:
                candidates = [word + " " for word in self.options.keys()]

            # later word
            else:
                first = words[0]
                candidates = self.options[first].sub_cmds.keys()

            # match options with portion of input being completed
            if being_completed:
                self.matches = [word for word in candidates
                                if word.startswith(being_completed)]

            # matching empty string so use all candidates
            else:
                self.matches = candidates

        self.log.debug("matches=%r", self.matches)

    def complete(self, text, state):
        self.log.debug("%s %r %r", self.complete.__name__, text, state)

        # first call for this text: build the match list
        if state == 0:
            try:
                self.find_matches(text)
            except Exception as error:
                logging.error("Match search exception!", exc_info = 1)
                self.matches = []

        try:
            response = self.matches[state]
        except IndexError:
            response = None

        self.log.debug("%s text=%r state=%r matches=%r", self.complete.__name__,
                      text, state, self.matches)
        return response

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

class Cmd(object):
    def __init__(self):
        # string name of the command used to invoke it in shell
        self.name = "no_name"
        self.sub_cmds = None

    def help_short(self):
        raise AbstractMethodException()

    def help(self):
        raise AbstractMethodException()

    def run(self):
        raise AbstractMethodException()

class StartZephyrCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "start-zephyr"

    def help_short(self):
        return "Start Zephyr OS under QEMU"

    def help(self):
        help_txt = (
            "\nUsage:\n"
            "\tstart-zephyr kernel_image\n"
            "\nNote: xterm must be installed for this command to work\n"
            "\nDescription:\n"
            "\nStart Zephyr OS under QEMU process\n"
            "\nExample:\n"
            "\tstart-zephyr ./microkernel.elf")

        return help_txt

    def run(self, kernel_image):
        global QEMU_PROCESS

        if QEMU_PROCESS:
            print "Zephyr is already up and running"
            return

        if not os.path.isfile(kernel_image):
            print "QEMU kernel image %s not found!" % repr(kernel_image)
            return

        qemu_cmd = get_qemu_cmd(kernel_image)

        # why running under xterm? cause of -serial mon:stdio: running qemu as
        # subprocess make terminal input impossible in the parent application, also
        # it is impossible to daemonize qemu
        xterm_qemu_cmd = ('xterm -e sh -c "%s 2>&1|tee qemu-%s.log"' %
                          (qemu_cmd, get_my_name()))

        # start listening
        logging.debug("Starting listen thread")
        thread = threading.Thread(target = listen, args = ([],))
        thread.start()

        # start qemu
        logging.debug("Starting qemu: %r", xterm_qemu_cmd)
        QEMU_PROCESS = subprocess.Popen(shlex.split(xterm_qemu_cmd))

        thread.join()

class StopZephyrCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "stop-zephyr"

    def help_short(self):
        return "Terminate Zephyr QEMU process"

    def help(self):
        help_txt = (
            "\nUsage:\n"
            "\tstop-zephyr\n"
            "\nDescription:\n"
            "\nStop Zephyr QEMU process")

        return help_txt

    def run(self):

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

class SendCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "send"

    def help_short(self):
        return "Send BTP command to tester"

    def help(self):
        help_txt = (
            "\nUsage:\n"
            "\tsend <service_id> <opcode> <index> [<data>]\n"
            "\nExample:\n"
            "\tsend 0 1 0 01\n"
            "\nDescription:\n"
            "\tsend <int> <int> <int> <hex>\n"
            "\t(send SERVICE_ID_CORE = 0x00, OP_CORE_REGISTER_SERVICE = 0x03,"
            "Controller Index = 0, SERVICE_ID_GAP = 0x01...)")

        return help_txt

    def run(self, svc_id, op, ctrl_index, data = ""):
        # TODO: should data be None and later check be done to append or not
        # append data to the frame?
        logging.debug(
            "%s %d %d %d", self.SendCmd.__name__, svc_id, op, ctrl_index)

        send(svc_id, op, ctrl_index, data)

class ReceiveCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "receive"

    def help_short(self):
        return "Receive BTP command from tester"

    def help(self):
        help_txt = (
            "\nUsage:\n"
            "\treceive\n"
            "\nDescription:\n"
            "\tThis method waits (timeout = 2sec) and reads data from btp socket")

        return help_txt

    def run(self):
        receive("")

class ListenCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "listen"

    def help_short(self):
        return "Listen to BTP messages from tester"

    def help(self):
        help_txt = (
            "\nUsage:\n"
            "\tlisten\n"
            "\nDescription:\n"
            "\tThis method starts listening btpclient for btpserver connection with 10sec timeout")

        return help_txt

    def run(self):
        listen([])

class DisconnectCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "disconnect"

    def help_short(self):
        return "Disconnect from BTP tester"

    def help(self):
        help_txt = (
            "\nUsage:\n"
            "\tdisconnect\n"
            "\nDescription:\n"
            "\tClear btp socket connection data")

        return help_txt

    def run(self):
        if conn_chk() is False:
            return

        clean_conn()
        print "Connection cleared"

class CoreCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "core"
        self.sub_cmds = CORE

    def help_short(self):
        return "Send core command to BTP tester"

    def help(self):
        help_txt = ("\nUsage: %s [command]\n"
                    "\nAvailable commands are:\n" % self.name)
        for cmd_name in sorted(CORE.keys()):
            help_txt += "    %s\n" % (cmd_name,)

        return help_txt

    def run(self, cmd):
        core_cmd(cmd)

class GapCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "gap"
        self.sub_cmds = GAP

    def help_short(self):
        return "Send GAP command to BTP tester"

    def help(self):

        help_txt = ("\nUsage: %s [command]\n"
                    "\nAvailable commands are:\n" % self.name)
        for cmd_name in sorted(GAP.keys()):
            help_txt += "    %s\n" % (cmd_name,)

        return help_txt

    def run(self, cmd):
        gap_cmd(cmd)

class GattsCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "gatts"
        self.sub_cmds = GATTS

    def help_short(self):
        return "Send GATT server command to BTP tester"

    def help(self):

        help_txt = ("\nUsage: %s [command]\n"
                    "\nAvailable commands are:\n" % self.name)
        for cmd_name in sorted(GATTS.keys()):
            help_txt += "    %s\n" % (cmd_name,)

        return help_txt

    def run(self, cmd):
        gatts_cmd(cmd)

class ExitCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "exit"

    def help_short(self):
        return "Exit the shell"

    def help(self):
        return "\n" + self.help_short()

    def run(self):
        sys.exit(0)

class HelpCmd(Cmd):

    def __init__(self, cmds_dict):
        Cmd.__init__(self)
        self.name = "help"
        self.sub_cmds = cmds_dict

    def help_short(self):
        return "Display help information about commands"

    def help(self):

        help_txt = (
            "%s\n"
            "\nSynopsis: help [command]\n"
            "%s"
            "\nRun 'help command' to see detailed help about specific command" %
            (self.help_short(), self.available_cmds()))

        return help_txt

    def available_cmds(self):
        """Returns string with available commands"""

        cmds_str = "\nAvailable commands are:\n"

        for cmd_name in sorted(self.sub_cmds.keys()):
            cmd = self.sub_cmds[cmd_name]
            cmds_str += "    %-15s %s\n" % (cmd_name, cmd.help_short())

        return cmds_str

    def run(self, cmd_name = None):
        if not cmd_name:
            print self.help()
            return

        try:
            print self.sub_cmds[cmd_name].help()
        except KeyError:
            print "\n%r is not a valid command!" % cmd_name
            print self.available_cmds()

def exec_cmd(choice, params, cmds_dict):
    logging.debug("%s choice=%r params=%r cmds_dict=%r",
                  exec_cmd.__name__, choice, params, cmds_dict)

    cmd_name = choice.lower()

    help_cmd = cmds_dict["help"]

    try:
        cmds_dict[cmd_name].run(*params)
    except KeyError:
        print "\n%r is not a valid command!" % cmd_name
        print help_cmd.available_cmds()
    except TypeError as e:
        print "Please enter correct arguments to command!"
        logging.debug(e)
        help_cmd.run(cmd_name)
    except TimeoutError:
        print "error: requested command timed out"

def clean_conn():
    global sock, conn, addr

    sock = None
    conn = None
    addr = None

def send(svc_id, op, ctrl_index, data = ""):
    # TODO: should data be None and later check be done to append or not
    # append data to the frame?
    logging.debug(
        "%s %r %r %r", send.__name__, svc_id, op, ctrl_index)

    if conn_chk() is False:
        return

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
            logging.debug("recv_into before")
            nbytes = conn.recv_into(hdr_memview, toread_hdr_len)
            logging.debug("recv_into after, %d", nbytes)
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

    # a tuple representing btp packet
    btp_cmd = svc[cmd]

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

    send(*frame)

# TODO: not needed? just move to run method of the respective class?
def core_cmd(cmd):
    generic_srvc_cmd_handler(CORE, cmd)

def gap_cmd(cmd):
    generic_srvc_cmd_handler(GAP, cmd)

def gatts_cmd(cmd):
    generic_srvc_cmd_handler(GATTS, cmd)

def conn_chk():
    if conn is None:
        print "error: btp client is not connected"
        return False

    return True

def cmd_loop(cmds_dict):
    my_name = get_my_name()

    while True:
        input = raw_input("\x1B[94m[%s]\x1B[0m$ " % my_name)

        if input == '':
            continue

        words = input.split()
        choice = words[0]
        params = words[1:]

        # TODO: exec_cmd catches TimeoutError
        exec_cmd(choice, params, cmds_dict)

def main():
    my_name = get_my_name()

    log_filename = "%s.log" % (my_name,)
    format = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
              "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format = format,
                        filename = log_filename,
                        filemode = 'w',
                        level = logging.DEBUG)

    history_filename = os.path.expanduser("~/.%s_history" % my_name)

    if os.path.exists(history_filename):
        logging.debug("Reading history file %s" % history_filename)
        readline.read_history_file(history_filename)

    cmds = [
        ListenCmd(),
        SendCmd(),
        ReceiveCmd(),
        ExitCmd(),
        DisconnectCmd(),
        StartZephyrCmd(),
        CoreCmd(),
        GapCmd(),
        GattsCmd()
    ]

    cmds_dict = { cmd.name : cmd for cmd in cmds }

    stop_zephyr_cmd = StopZephyrCmd()
    cmds_dict[stop_zephyr_cmd.name] = stop_zephyr_cmd

    # add help, that can provide help for all commands
    help_cmd = HelpCmd(cmds_dict)
    cmds_dict[help_cmd.name] = help_cmd

    readline.set_completer(Completer(cmds_dict).complete)
    readline.parse_and_bind("tab: complete")

    try:
        cmd_loop(cmds_dict)

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
            stop_zephyr_cmd.run()
        logging.debug("Writing history file %s" % history_filename)
        readline.write_history_file(history_filename)

if __name__ == "__main__":
    main()
