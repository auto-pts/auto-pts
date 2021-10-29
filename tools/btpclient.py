#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

import os
import sys
import socket
import errno
import shlex
import struct
import logging
import readline
import binascii
import argparse
import threading
import subprocess
from distutils.spawn import find_executable

from autopts.pybtp import btp
from autopts.pybtp import defs
from autopts.pybtp.iutctl_common import BTPSocket
from autopts.ptsprojects.zephyr.iutctl import get_qemu_cmd, BTP_ADDRESS
from autopts.ptsprojects.testcase import AbstractMethodException

BTP_SOCKET = None
QEMU_PROCESS = None

# ANSI escape codes for Select Graphic Rendition (SGR) parameters
sgr_reset = "\x1B[0m"
sgr_fg_blue = "\x1B[94m"
sgr_fg_green = "\x1B[32m"
sgr_fg_red = "\x1B[31m"

# based on RL_PROMPT_START_IGNORE and RL_PROMPT_END_IGNORE in readline.h
rl_prompt_start_ignore = '\001'
rl_prompt_end_ignore = '\002'


def rl_prompt_ignore(text):
    """Return text surrounded by prompt ignore markers of readline"""
    return rl_prompt_start_ignore + text + rl_prompt_end_ignore


def red(text):
    """Return red text"""
    return sgr_fg_red + text + sgr_reset


def green(text):
    """Return green text"""
    return sgr_fg_green + text + sgr_reset


def blue(text):
    """Return blue text"""
    return sgr_fg_blue + text + sgr_reset


def get_my_name():
    """Returns name of the script without extension"""
    script_name = os.path.basename(sys.argv[0])  # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    return script_name_no_ext


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
                candidates = [word + " " for word in list(self.options.keys())]

            # later word
            else:
                first = words[0]
                candidates = list(self.options[first].sub_cmds.keys())

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
            except Exception:
                logging.error("Match search exception!", exc_info=1)
                self.matches = []

        try:
            response = self.matches[state]
        except IndexError:
            response = None

        self.log.debug(
            "%s text=%r state=%r matches=%r",
            self.complete.__name__,
            text,
            state,
            self.matches)
        return response


class Help(object):
    """Help text manager for Cmd classes"""

    def __init__(self):
        self.short = None
        self.long = None

        self.available_sub_cmds = None

    def build_available_sub_cmds(self, sub_cmds, margin):
        help_text = "\nAvailable commands are:\n"

        if isinstance(sub_cmds, list):
            for cmd_name in sorted(sub_cmds):
                help_text += margin + "%s\n" % (cmd_name,)
        else:  # dict
            for cmd_name in sorted(sub_cmds.keys()):
                cmd_help = sub_cmds[cmd_name]
                help_text += margin + "%-15s %s\n" % (cmd_name, cmd_help)

        help_text = help_text[:-1]  # remove last newline

        self.available_sub_cmds = help_text

        return help_text

    def build(self, short_help, synopsis=None, description=None,
              example=None, sub_cmds=None):
        """
        sub_cmds -- List of sub-command names, or dictionary with sub-command
                    names as keys and command help as values
        """

        self.short = short_help

        margin = " " * 4
        help_text = short_help

        if synopsis:
            help_text += ("\n\nSynopsis:\n"
                          "%s%s\n") % (margin, synopsis)

        if sub_cmds:
            help_text += self.build_available_sub_cmds(sub_cmds, margin)

        if description:
            help_text += "\nDescription:"
            for line in description.splitlines():
                help_text += "\n%s%s" % (margin, line)

        if example:
            help_text += "\n\nExample:\n%s%s" % (margin, example)

        self.long = help_text


class Cmd(object):
    def __init__(self):
        # string name of the command used to invoke it in shell
        self.name = "no_name"

        self.sub_cmds = None

        # child class must build the text
        self.help = Help()

    def help_short(self):
        return self.help.short

    def help_long(self):
        return self.help.long

    def run(self):
        raise AbstractMethodException()


class StartZephyrCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "start-zephyr"

        self.help.build(
            short_help="Start Zephyr OS under QEMU",
            synopsis="%s kernel_image" % self.name,
            description=("Start QEMU with Zephyr OS image"
                         "\nNote: xterm must be installed for "
                         "this command to work."),
            example="%s ./microkernel.elf" % self.name)

    def run(self, kernel_image):
        global QEMU_PROCESS

        if QEMU_PROCESS:
            print("Zephyr is already up and running")
            return

        if not os.path.isfile(kernel_image):
            print("QEMU kernel image %s not found!" % repr(kernel_image))
            return

        if not find_executable('xterm'):
            print("xterm is needed but not found!")
            return

        qemu_cmd = get_qemu_cmd(kernel_image)

        # why running under xterm? cause of -serial mon:stdio: running qemu as
        # subprocess make terminal input impossible in the parent application,
        # also it is impossible to daemonize qemu
        xterm_qemu_cmd = ('xterm -e sh -c "%s 2>&1|tee qemu-%s.log"' %
                          (qemu_cmd, get_my_name()))

        # start listening
        logging.debug("Starting listen thread")
        thread = threading.Thread(target=listen)
        thread.start()

        # start qemu in a new session to prevent killing it on Ctrl-C
        logging.debug("Starting qemu: %r", xterm_qemu_cmd)
        QEMU_PROCESS = subprocess.Popen(shlex.split(xterm_qemu_cmd),
                                        preexec_fn=os.setsid)

        thread.join()


class StopZephyrCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "stop-zephyr"

        self.help.build(
            short_help="Terminate Zephyr QEMU process",
            synopsis="%s" % self.name,
            description="Stop Zephyr QEMU process")

    def run(self):

        global QEMU_PROCESS

        if not QEMU_PROCESS:
            print("Zephyr is not running")
            return

        if QEMU_PROCESS:
            if QEMU_PROCESS.poll() is None:
                logging.debug("qemu process is running, will terminate it")
                QEMU_PROCESS.terminate()
                QEMU_PROCESS.wait()  # do not let zombies take over
                logging.debug("Completed termination of qemu process")
                QEMU_PROCESS = None


class SendCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "send"

        self.help.build(
            short_help="Send BTP command to tester",
            synopsis="%s <service_id> <opcode> <index> [<data>]" %
                     self.name,
            description=(
                "send <int> <int> <int> <hex>\n"
                "(send SERVICE_ID_CORE = 0x00, OP_CORE_REGISTER_SERVICE = 0x03"
                ",Controller Index = 0, SERVICE_ID_GAP = 0x01...)"),
            example="%s 0 1 0 01" %
                    self.name)

    def run(self, svc_id, op, ctrl_index, data=""):
        # TODO: should data be None and later check be done to append or not
        # append data to the frame?
        logging.debug("%s.%s %r %r %r", self.__class__.__name__,
                      self.run.__name__, svc_id, op, ctrl_index)

        send(svc_id, op, ctrl_index, data)


class ReceiveCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "receive"

        self.help.build(
            short_help="Receive BTP command from tester",
            synopsis="%s" % self.name,
            description=("This command reads BTP commands from tester."
                         "\nCan be interrupted with Ctrl-C."))

    def run(self, *args, **kwds):
        receive(*args, **kwds)


class ListenCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "listen"

        self.help.build(
            short_help="Listen to BTP messages from tester",
            synopsis="%s" % self.name,
            description=("This command starts listening for BTP server "
                         "connection.\nCan be interrupted with Ctrl-C"))

    def run(self):
        listen()


class DisconnectCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "disconnect"

        self.help.build(
            short_help="Disconnect from BTP tester",
            synopsis="%s" % self.name,
            description="Clear btp socket connection data")

    def run(self):
        if not conn_check():
            return

        conn_clean()
        print("Connection cleared")


class CoreCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "core"
        self.sub_cmds = btp.CORE

        self.help.build(
            short_help="Send core command to BTP tester",
            synopsis="%s [command]" % self.name,
            sub_cmds=list(self.sub_cmds.keys()))

    def run(self, *cmd):
        if not cmd:
            raise TypeError("Command arguments are missing")

        generic_srvc_cmd_handler(btp.CORE, cmd)


class GapCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "gap"
        self.sub_cmds = btp.GAP

        self.help.build(
            short_help="Send GAP command to BTP tester",
            synopsis="%s [command]" % self.name,
            sub_cmds=list(self.sub_cmds.keys()))

    def run(self, *cmd):
        if not cmd:
            raise TypeError("Command arguments are missing")

        generic_srvc_cmd_handler(btp.GAP, cmd)


class GattsCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "gatts"
        self.sub_cmds = btp.GATTS

        self.help.build(
            short_help="Send GATT server command to BTP tester",
            synopsis="%s [command]" % self.name,
            sub_cmds=list(self.sub_cmds.keys()))

    def run(self, *cmd):
        if not cmd:
            raise TypeError("Command arguments are missing")

        generic_srvc_cmd_handler(btp.GATTS, cmd)


class GattcCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "gattc"
        self.sub_cmds = btp.GATTC

        self.help.build(
            short_help="Send GATT client command to BTP tester",
            synopsis="%s [command]" % self.name,
            sub_cmds=list(self.sub_cmds.keys()))

    def run(self, *cmd):
        if not cmd:
            raise TypeError("Command arguments are missing")

        generic_srvc_cmd_handler(btp.GATTC, cmd)


class L2capCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "l2cap"
        self.sub_cmds = btp.L2CAP

        self.help.build(
            short_help="Send L2CAP command to BTP tester",
            synopsis="%s [command]" % self.name,
            sub_cmds=list(self.sub_cmds.keys()))

    def run(self, *cmd):
        if not cmd:
            raise TypeError("Command arguments are missing")

        generic_srvc_cmd_handler(btp.L2CAP, cmd)


class ExitCmd(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.name = "exit"

        self.help.build(short_help="Exit the shell")

    def run(self):
        sys.exit(0)


class HelpCmd(Cmd):

    def __init__(self, cmds_dict):
        Cmd.__init__(self)
        self.name = "help"
        self.sub_cmds = cmds_dict

    def __build_help(self):
        """Builds help.

        This is not done in constructor as with the other commands cause then
        this class is not created, hence it is not in the cmds_dict, from which
        commands and their help text are obtained.

        So, by building help after the constructor of this class we also get
        the help for this class in the list of available commands when running:
        "help help" or "help.

        """

        short_help = "Display help information about commands"

        # needed by the following dictionary comprehension
        self.help.short = short_help

        cmds = {cmd.name: cmd.help.short
                for cmd_name, cmd in list(self.sub_cmds.items())}

        self.help.build(
            short_help=short_help,
            synopsis="%s [command]" % self.name,
            description="Run '%s command' to see detailed help about "
                        "specific command" % self.name,
            sub_cmds=cmds)

    def run(self, cmd_name=None):
        if not self.help.short:
            self.__build_help()

        if not cmd_name:
            print(self.help_long())
            return

        try:
            print(self.sub_cmds[cmd_name].help_long())
        except KeyError:
            print("%r is not a valid command!" % cmd_name)
            print(self.help.available_sub_cmds)


def exec_cmd(choice, params, cmds_dict):
    logging.debug("%s choice=%r params=%r cmds_dict=%r",
                  exec_cmd.__name__, choice, params, cmds_dict)

    cmd_name = choice.lower()

    help_cmd = cmds_dict["help"]

    try:
        cmds_dict[cmd_name].run(*params)
    except KeyError:
        help_cmd.run(cmd_name)  # invalid command
    except TypeError as e:
        print("Please enter correct arguments to command!\n")
        logging.debug(e)
        help_cmd.run(cmd_name)
    except socket.timeout as e:
        print("socket timeout: %s\n" % e)
    except socket.error as e:
        print("socket error: %s\n" % e)
    except SyntaxWarning as e:
        print(e)


def parse_service_id(svc_id):
    """Parse service ID specified as string.

    Return -- integer service ID"""
    service_ids = {item: getattr(defs, item) for item in dir(defs)
                   if item.startswith("BTP_SERVICE_ID")}
    try:
        int_svc_id = int(svc_id)
    except ValueError:
        raise SyntaxWarning("Wrong service ID format, possible values: ",
                            service_ids)

    if int_svc_id not in list(service_ids.values()):
        raise SyntaxWarning(
            "Given service ID %c not supported, supported are %s!" %
            (int_svc_id, repr(list(service_ids.values()))))

    return int_svc_id


def parse_opcode(opcode):
    """Parse opcode specified as string.

    Return -- integer opcode"""
    try:
        int_opcode = int(opcode)
    except ValueError:
        raise SyntaxWarning('Wrong opcode format, should be an int: "0-255"')
    return int_opcode


def parse_ctrl_index(ctrl_index):
    """Parse controller index specified as string.

    Return -- integer controller index"""
    try:
        int_ctrl_index = int(ctrl_index)
    except ValueError:
        raise SyntaxWarning('Wrong Controler Index format, should be an int: '
                            '"0-255"')
    return int_ctrl_index


def parse_data(data):
    """Parse data specified as string.

    Return -- data in binary format"""
    try:
        hex_data = binascii.unhexlify(data)
    except TypeError:
        raise SyntaxWarning('Wrong data type, should be e.g.: "0011223344ff"')
    return hex_data


def send(svc_id, op, ctrl_index, data=""):
    logging.debug(
        "%s %r %r %r", send.__name__, svc_id, op, ctrl_index)

    if conn_check() is False:
        return

    int_svc_id = parse_service_id(svc_id)
    int_op = parse_opcode(op)
    int_ctrl_index = parse_ctrl_index(ctrl_index)
    hex_data = parse_data(data)

    logging.debug("Sending: %d %d %d %r" %
                  (int_svc_id, int_op, int_ctrl_index, hex_data))

    try:
        BTP_SOCKET.send(int_svc_id, int_op, int_ctrl_index, hex_data)
    except socket.error as serr:
        if serr.errno == errno.EPIPE:
            conn_clean()
            print("error: Connection error, please connect btp again")
            return

    receive(int_svc_id, int_op)

    return


def print_controller_info(data):
    """Print data of the BTP Read Controller Information response"""
    settings2txt = {
        defs.GAP_SETTINGS_POWERED: "Powered",
        defs.GAP_SETTINGS_CONNECTABLE: "Connectable",
        defs.GAP_SETTINGS_FAST_CONNECTABLE: "Fast Connectable",
        defs.GAP_SETTINGS_DISCOVERABLE: "Discoverable",
        defs.GAP_SETTINGS_BONDABLE: "Bondable",
        defs.GAP_SETTINGS_LINK_SEC_3: "Link Level Security (Sec. mode 3)",
        defs.GAP_SETTINGS_SSP: "Secure Simple Pairing",
        defs.GAP_SETTINGS_BREDR: "Basic Rate/Enhanced Data Rate",
        defs.GAP_SETTINGS_HS: "High Speed",
        defs.GAP_SETTINGS_LE: "Low Energy",
        defs.GAP_SETTINGS_ADVERTISING: "Advertising",
        defs.GAP_SETTINGS_SC: "Secure Connections",
        defs.GAP_SETTINGS_DEBUG_KEYS: "Debug Keys",
        defs.GAP_SETTINGS_PRIVACY: "Privacy",
        defs.GAP_SETTINGS_CONTROLLER_CONFIG: "Controller Configuration",
        defs.GAP_SETTINGS_STATIC_ADDRESS: "Static Address"
    }

    def get_settings_names(settings):
        """Return settings in human-readable format"""
        settings_names = []
        for i in list(settings2txt.keys()):
            if settings & (1 << i):
                settings_names.append(settings2txt[i])
        return " ".join(settings_names)

    fmt = '<6sII3s249s11s'
    if len(data) < struct.calcsize(fmt):
        print("Invalid data length")
        return

    (address, supported_settings, current_settings, class_of_device, name,
     short_name) = struct.unpack_from(fmt, data)

    address = binascii.hexlify(address[::-1]).upper()
    print("IUT BD_ADDR: %r" % address)
    print("Supported Settings: %r %s" %
          (supported_settings, get_settings_names(supported_settings)))
    print("Current Settings: %r %s" %
          (current_settings, get_settings_names(current_settings)))
    print("Class Of Device: %r" % class_of_device)
    print("Name: '%s'" % name)
    print("Short Name: '%s'" % short_name)


def receive(exp_svc_id=None, exp_op=None):
    """The parameters are the values used in the command, so response is
    expected to have the same value

    """
    logging.debug("%s %r %r", receive.__name__, exp_svc_id, exp_op)

    if conn_check() is False:
        return

    try:
        tuple_hdr, tuple_data = BTP_SOCKET.read()
    except KeyboardInterrupt:
        print("\nReceive interrupted!")
        return

    # default __repr__ of namedtuple does not print hex
    print(
        "Received header(svc_id=%d, op=0x%.2x, ctrl_index=%d, data_len=%d)" %
        (tuple_hdr.svc_id, tuple_hdr.op, tuple_hdr.ctrl_index,
         tuple_hdr.data_len))

    hex_str = binascii.hexlify(tuple_data[0])
    hex_str_byte = " ".join(hex_str[i:i + 2]
                            for i in range(0, len(hex_str), 2))
    print("Received data (hex): %s" % hex_str_byte)
    print("Received data (ascii):", tuple_data)

    if exp_svc_id is None and exp_op is None:
        return

    try:
        btp.btp_hdr_check(tuple_hdr, exp_svc_id, exp_op)
    except btp.BTPError as err:
        print(red("%s\nExpected svc_id=%s, op=0x%.2x" %
                  (err, exp_svc_id, exp_op)))
        return

    if tuple_hdr.svc_id == defs.BTP_SERVICE_ID_GAP:
        if tuple_hdr.op == defs.GAP_EV_PASSKEY_DISPLAY:
            passkey = struct.unpack('I', tuple_data[0][7:11])[0]
            print("Passkey:", passkey)
        if tuple_hdr.op == defs.GAP_READ_CONTROLLER_INFO:
            print_controller_info(tuple_data[0])
    print(green("OK"))


def listen():
    """Establish connection with the BTP tester"""
    logging.debug("%s", listen.__name__)

    if BTP_SOCKET.conn is not None:
        print("btpclient is already connected to btp server")
        return

    BTP_SOCKET.open()
    print("created fd %s, listening..." % BTP_ADDRESS)

    try:
        BTP_SOCKET.accept(None)
        print("btp server connected successfully")

    except KeyboardInterrupt:
        print("\nListen interrupted!")


def generic_srvc_cmd_handler(svc, cmd):
    logging.debug("%s svc=%r cmd=%r",
                  generic_srvc_cmd_handler.__name__, svc, cmd)

    # a tuple representing btp packet
    btp_cmd = svc[cmd[0]]

    if len(btp_cmd) == 0:
        print("Command not yet defined")
        return

    frame = []

    # 3 cause: service id, opcode, controller index
    for i in range(3):
        frame.append(str(btp_cmd[i]))

    # add data if there is any
    if len(btp_cmd) > 3:
        data = str(btp_cmd[3])

        if len(data) == 1:
            frame.append("0%s" % data)
        else:
            frame.append(binascii.hexlify(''.join(data)))

    elif len(cmd) > 1:  # some commands pass data from command line
        data = cmd[1]
        frame.append(data)

    logging.debug("frame %r", frame)

    send(*frame)


def conn_check():
    if BTP_SOCKET is None:
        return False

    if BTP_SOCKET.conn is None:
        print("error: btp client is not connected")
        return False

    return True


def conn_clean():
    global BTP_SOCKET
    BTP_SOCKET.close()
    BTP_SOCKET = None


def cmd_loop(cmds_dict):
    prompt = "%s[%s]%s$ " % (rl_prompt_ignore(sgr_fg_blue),
                             get_my_name(),
                             rl_prompt_ignore(sgr_reset))

    while True:
        text = input(prompt)

        if text == '':
            continue

        words = text.split()
        choice = words[0]
        params = words[1:]

        exec_cmd(choice, params, cmds_dict)


def exec_cmds_file(filename, cmds_dict):
    """Runs commands from a text file

    Each command should be on a separate line in the file. Comment lines start
    with the hash character.

    """
    print("Running commands from file")

    if not os.path.isfile(filename):
        sys.exit("Commands file %r does not exits!" % filename)

    for line in open(filename):
        line = line.strip()

        if line.startswith("#"):  # comment
            continue

        words = line.split()
        choice = words[0]
        params = words[1:]

        print("\n" + line)

        exec_cmd(choice, params, cmds_dict)

    print("\nDone running commands from file")


def parse_args():
    """Parses command line arguments and options"""

    arg_parser = argparse.ArgumentParser(
        description="Bluetooth Test Protocol command line client")

    arg_parser.add_argument("--cmds-file",
                            "-c",
                            metavar="FILE",
                            help="File with initial commands to run. Each "
                                 "command should be on a separate line in the "
                                 "file.  Comment lines start with the hash "
                                 "character.")

    args = arg_parser.parse_args()

    return args


def main():
    args = parse_args()
    my_name = get_my_name()

    log_filename = "%s.log" % (my_name,)
    format_template = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
                       "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format=format_template,
                        filename=log_filename,
                        filemode='w',
                        level=logging.DEBUG)

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
        GattsCmd(),
        GattcCmd(),
        L2capCmd()
    ]

    cmds_dict = {cmd.name: cmd for cmd in cmds}

    stop_zephyr_cmd = StopZephyrCmd()
    cmds_dict[stop_zephyr_cmd.name] = stop_zephyr_cmd

    # add help, that can provide help for all commands
    help_cmd = HelpCmd(cmds_dict)
    cmds_dict[help_cmd.name] = help_cmd

    readline.set_completer(Completer(cmds_dict).complete)
    readline.parse_and_bind("tab: complete")

    global BTP_SOCKET
    BTP_SOCKET = BTPSocket()

    try:
        if args.cmds_file:
            exec_cmds_file(args.cmds_file, cmds_dict)

        cmd_loop(cmds_dict)

    except KeyboardInterrupt:  # Ctrl-C
        sys.exit("")

    except EOFError:  # Ctrl-D
        sys.exit("")

    # SystemExit is thrown in arg_parser.parse_args and in sys.exit
    except SystemExit:
        raise  # let the default handlers do the work

    except BaseException:
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
