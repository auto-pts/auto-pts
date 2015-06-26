import sys, os

def help():
    print "Avilable commands: "
    menu = cmds.viewkeys()
    print list(menu)

    return

def exec_cmd(choice):
    ch = choice.lower()
    if ch == '':
        cmds['help']()
    else:
        try:
            cmds[ch]()
        except KeyError:
            print "Invalid selection, please try again.\n"
            cmds['help']()
    return

def send():
    print "send: "

    return

def receive():
    print "receive: "

    return

def exit():
    sys.exit()

def prompt():
    while True:
        input = raw_input(" >> ")
        exec_cmd(input)

    return

def main():
    prompt()

cmds = {
    'help': help,
    'send': send,
    'receive': receive,
    'exit': exit,
}

if __name__ == "__main__":
    main()
