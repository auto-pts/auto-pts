import sys, os
import socket
import signal
import errno
import readline
import binascii
from ptsprojects.zephyr.msgdefs import *
from functools import wraps
from ptsprojects.zephyr.btpparser import enc_frame, dec_hdr, dec_data

sock = None
conn = None
addr = None
QEMU_UNIX_PATH = "/tmp/bt-stack-tester"

class TimeoutError(Exception):
    pass

class Completer:
    def __init__(self, words):
        self.words = words
        self.prefix = None
    def complete(self, prefix, index):
        if len(prefix.split()) > 1:
            return None
        if prefix.split()[0] in self.words and len(prefix.split()) == 1:
            try:
                return prefix.split()[index] + ' ' + "help"
            except IndexError:
                return None

        if prefix != self.prefix:
            self.matching_words = [ w for w in self.words if w.startswith(prefix) ]
            self.prefix = prefix
        try:
            return self.matching_words[index]
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
    print "Avilable commands: "
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

def send(params):
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

    # Parse Service ID
    try:
        char_svc_id = chr(int(svc_id))
    except ValueError:
        print "error: Wrong svc_id format, possible values: ", SERVICE_ID
        return

    if char_svc_id not in SERVICE_ID.values():
        print "error: Given service ID not supported!"
        return

    # Parse Opcode
    try:
        char_op = chr(int(op))
    except ValueError:
        print "error: Wrong op format, should be an int: \"0-255\""
        return

    # Parse Controler Index
    try:
        char_ctrl_index = chr(int(ctrl_index))
    except ValueError:
        print "error: Wrong Controler Index format, shoulb be an int: \"0-255\""
        return

    # Parse Data
    try:
        hex_data = binascii.unhexlify(data)
    except TypeError:
        print "error: Wrong data type, should be e.g.: \"0011223344ff\""
        return

    frame = enc_frame(char_svc_id, char_op, char_ctrl_index, hex_data)
    conn.send(frame)

    try:
        receive(None)
    except TimeoutError:
        print "error: problem with receiving response from server"

    return

@timeout(2)
def receive(params):
    if params != None and params[0] == "help":
        print "\nUsage:"
        print "\treceive"
        print "\nDescription:"
        print "\tThis method waits (timeout = 2sec) and reads data from btp socket"
        return

    if conn_chk() is False:
        return

    toread_hdr_len = HDR_LEN
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

    tuple_hdr = dec_hdr(hdr)
    toread_data_len = tuple_hdr.data_len

    print "Received: hdr: ", tuple_hdr

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

    tuple_data = dec_data(data)

    print "Received data: ", tuple_data

@timeout(10)
def listen_accept():
    global conn, addr

    conn, addr = sock.accept()
    conn.setblocking(0)

    print "btp server connected sucesfully"

    return

def listen(params):
    global sock

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
        listen_accept()
    except TimeoutError:
        print "error: Connection timeout..."

def exit(params):
    os._exit(0)

def conn_chk():
    if conn is None:
        print "error: btp client is not connected"
        return False

    return True

def prompt():
    while True:
        input = raw_input(" >> ")

        if input == '':
            continue

        words = input.split()
        choice = words[0]
        params = words[1:]

        exec_cmd(choice, params)

def setup_completion():
    completer = Completer(cmds)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.complete)
    readline.set_completer_delims('')

def main():
    setup_completion()

    try:
        prompt()
    except:
        import traceback
        traceback.print_exc()
        os._exit(16)

cmds = {
    'help': help,
    'listen': listen,
    'send': send,
    'receive': receive,
    'exit': exit,
}

if __name__ == "__main__":
    main()
