import sys, os
import socket
import signal
import errno
import readline
from functools import wraps

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
    print "send: "

    return

def receive(params):
    print "receive: "

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
