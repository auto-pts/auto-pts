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
QEMU_UNIX_PATH = "/tmp/ubt_tester"

class TimeoutError(Exception):
    pass

class Completer:
    def __init__(self, words):
        self.words = words
        self.prefix = None
    def complete(self, prefix, index):
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

    return

def exec_cmd(choice, params):
    ch = choice.lower()
    try:
        cmds[ch](params)
    except KeyError:
        print "error: Invalid selection, please try again.\n"
        cmds['help'](params)

    return

def send(params):
    if conn_chk() is False:
        return

    try:
        svc_id = params[0]
        op = params[1]
    except IndexError:
        print "Invalid send frame format/data, usage: send 0 0 00 or send 0 0"
        return

    try:
        data = params[2]
    except IndexError:
        data = ""

    try:
        char_svc_id = chr(int(svc_id))
    except ValueError:
        print "error: Wrong svc_id format, possible values: ", SERVICE_ID
        return

    if char_svc_id not in SERVICE_ID.values():
        print "error: Given service ID not supported!"
        return

    try:
        char_op = chr(int(op))
    except ValueError:
        print "error: Wrong op format, should be an int: \"0-255\""
        return

    try:
        hex_data = binascii.unhexlify(data)
    except TypeError:
        print "error: Wrong data type, should be e.g.: \"0011223344ff\""
        return


    frame = enc_frame(char_svc_id, char_op, hex_data)

    conn.send(frame)
    receive(None)

    return

@timeout(2)
def receive(params):
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
            #TODO timeout
            continue

    tuple_hdr = dec_hdr(hdr)
    toread_data_len = tuple_hdr.data_len

    print "Received: hdr", tuple_hdr

    data = bytearray(toread_data_len)
    data_memview = memoryview(data)

    #Gather optional frame data
    while toread_data_len:
        try:
            nbytes = conn.recv_into(data_memview, toread_data_len)
            data_memview = data_memview[nbytes:]
            toread_data_len -= nbytes
        except:
            #TODO timeout
            continue

    tuple_data = dec_data(data)

    print "Received data: ", tuple_data

    return

@timeout(10)
def listen_accept():
    global conn, addr

    conn, addr = sock.accept()
    conn.setblocking(0)

    print "btp server connected sucesfully"

    return

def listen(params):
    global sock

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

    return

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

    return

def setup_completion():
    completer = Completer(cmds)

    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.complete)

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
