#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2025, Atmosic.
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
import argparse
import copy
import json
import logging
import os
import shutil
import sys
import time
import traceback
from collections.abc import Callable
from itertools import zip_longest
from typing import Any

from autopts.config import FILE_PATHS, ConfigDefinition, IUTMode
from autopts.ptsprojects.boards import com_to_tty, get_debugger_snr, get_free_device, get_tty, tty_exists
from autopts.utils import active_hub_server_replug_usb, get_tc_from_wid, load_wid_report, raise_on_global_end, ykush_replug_usb

log = logging.debug


class CliParser(argparse.ArgumentParser):
    def __init__(self, board_names=None, add_help=True, *args, **kwargs):
        super().__init__(description='PTS automation client', add_help=add_help)

        self.check_methods: dict[IUTMode, Callable[[Any], str]] = {
            IUTMode.TTY: self.check_args_tty,
            IUTMode.NATIVE: self.check_args_native,
            IUTMode.QEMU: self.check_args_qemu,
            IUTMode.BTPCLIENT_PATH: self.check_args_btpclient_path,
            IUTMode.BTPCLIENT_TCP: self.check_args_btp_tcp_client,
        }

        self._parameters_with_duplicated_cli = {}

        for key in ConfigDefinition.parameters.keys():
            parameter = ConfigDefinition.parameters[key]
            if parameter.cli is None or parameter.hidden:
                continue

            try:
                arguments = parameter.cli
                if isinstance(arguments, list):
                    self._parameters_with_duplicated_cli[key] = parameter
                else:
                    arguments = [arguments]

                for argument in arguments:
                    # When parameter's default is set to SUPPRESS, it will not appear in
                    # the parsing result namespace, which allows to determine which parameters
                    # were actually provided with the cli.
                    argument.kwargs["default"] = argparse.SUPPRESS
                    self.add_argument(*argument.flags, **argument.kwargs)
            except BaseException as e:
                traceback.print_exception(e)

    def parse_args(self, args=None, namespace=None):
        cli_args = super().parse_args(None, None)

        provided = set(vars(cli_args).keys())
        cli_args._cli_provided = provided

        if namespace is None:
            # Restore the parameters not provided with the cli using predefined default values.
            for name, parameter in ConfigDefinition.parameters.items():
                if getattr(cli_args, name, None) is None:
                    if parameter.default_factory:
                        value = parameter.default_factory()
                    else:
                        value = parameter.default

                    setattr(cli_args, name, value)

        for key, parameter in self._parameters_with_duplicated_cli.items():
            # Set value for parameters with multiple CliArguments definitions.
            setattr(cli_args, key, parameter.get_value(cli_args))

        return self.remodel_args(namespace, cli_args)

    def normalize_to_list(self, x):
        if x is None:
            return []
        if isinstance(x, list):
            return x
        return [x]

    def remodel_args(self, configpy_args, cli_args):
        iut_targets_args = {}

        # Filter out options/parameters that can be configured
        # separately for each IUT.
        iut_params = []
        not_iut_params = []
        for a in self._actions:
            param = ConfigDefinition.parameters.get(a.dest, None)
            if param and param.iut_param:
                iut_params.append(a)
            else:
                not_iut_params.append(a)

        # Filter out options/parameters actually provided in CLI
        lists = {
            a.dest: self.normalize_to_list(getattr(cli_args, a.dest))
            for a in iut_params if a.dest in cli_args._cli_provided
        }

        base_params = {
            a.dest: getattr(cli_args, a.dest)
            for a in not_iut_params if a.dest in cli_args._cli_provided
        }

        # Distribute CLI params per-IUT
        cli_targets = []
        for values in zip_longest(*lists.values(), fillvalue=None):
            params = dict(zip(lists.keys(), values, strict=False))

            if cli_targets:
                first = cli_targets[0]
                for k, v in params.items():
                    if v is None:
                        params[k] = first[k]

            cli_targets.append(params)

        # Select base source of arguments
        if configpy_args:
            base = configpy_args
            for name in base_params:
                setattr(base, name, base_params[name])
        else:
            base = cli_args

        # Create targets
        if configpy_args and configpy_args.iut_targets:
            targets = configpy_args.iut_targets
            if not cli_targets:
                cli_targets = [{} for _ in range(len(targets))]
        else:
            if not cli_targets:
                cli_targets = [{}]
            targets = [{"name": f"iut{i}"} for i in range(len(cli_targets))]

        for i, (target, cli_params) in enumerate(zip(targets, cli_targets, strict=False)):
            name = target.get("name", f"iut{i}")

            args_copy = copy.deepcopy(base)

            # config.py target
            for k, v in target.items():
                if hasattr(args_copy, k):
                    setattr(args_copy, k, v)

            # CLI override
            for k, v in cli_params.items():
                setattr(args_copy, k, v)

            args_copy.iut_target_name = name
            iut_targets_args[name] = args_copy

            # Add arguments that are in the CLI parser but not in the bot parser.
            for action in self._actions:
                dest = action.dest
                if not hasattr(args_copy, dest) and hasattr(cli_args, dest):
                    setattr(args_copy, dest, getattr(cli_args, dest))

        base.iut_targets_args = iut_targets_args

        for action in self._actions:
            dest = action.dest
            if not hasattr(base, dest) and hasattr(cli_args, dest):
                setattr(base, dest, getattr(cli_args, dest))

        if isinstance(base.iut_target_selection, str) and os.path.exists(base.iut_target_selection):
            with open(base.iut_target_selection) as f:
                base.iut_target_selection = json.load(f)
        elif not isinstance(base.iut_target_selection, dict):
            base.iut_target_selection = {'default_iut_map': {}}
            for i, iut_name in enumerate(base.iut_targets_args):
                base.iut_target_selection['default_iut_map'][str(i)] = iut_name

        return base

    def _replug_and_find_tty(self, args):
        log(f'{self._replug_and_find_tty.__name__}')

        if not args.ykush and not args.active_hub_server:
            return False

        if args.ykush:
            device_id = args.tty_alias if args.tty_alias else args.tty_file
            ykush_replug_usb(args.ykush, device_id=device_id, delay=args.ykush_replug_delay)
        elif args.active_hub_server:
            active_hub_server_replug_usb(args.active_hub_server)

        if args.tty_alias:
            while not os.path.islink(args.tty_alias) and not os.path.exists(os.path.realpath(args.tty_alias)):
                raise_on_global_end()
                log(f'Waiting for TTY {args.tty_alias} to appear...\n')
                time.sleep(1)

            args.tty_file = os.path.realpath(args.tty_alias)
        elif args.debugger_snr:
            args.tty_file = get_tty(args.debugger_snr, args.board_name)
        else:
            args.tty_file, args.debugger_snr = get_free_device(args.board_name)

        if not tty_exists(args.tty_file):
            return False

        return True

    def wid_run_tcs(self, args):
        """
        If --wid_run SERVICE WID was provided:
        - load the CSV mapping
        - lookup testcases for (service, wid)
        - print them before execution
        - and append to args.test_cases so they get executed like normal.
        """
        if not args.wid_run:
            return

        mapping = load_wid_report()
        service, wid = args.wid_run

        tcs = get_tc_from_wid(service, wid, mapping)
        if not tcs:
            print(f"No testcases found for service={service}, wid={wid}")
            return

        print(f"Testcases for {service} {wid}:")
        for tc in tcs:
            print(tc)

        # Append found test cases to test cases list
        args.test_cases = list(args.test_cases) + tcs

    def find_tty(self, args):
        log(f'{self.find_tty.__name__}')

        if args.tty_file:
            args.tty_alias = None
            log(f'Using tty_file={args.tty_file}')
        elif args.tty_alias:
            args.tty_file = os.path.realpath(args.tty_alias)
            log(f'Using tty_alias={args.tty_alias} -> tty_file={args.tty_file}')
        elif args.debugger_snr:
            args.tty_file = get_tty(args.debugger_snr, args.board_name)
            log(f'Using debugger_snr={args.debugger_snr} -> tty_file={args.tty_file}')
        else:
            args.tty_file, args.debugger_snr = get_free_device(args.board_name)
            log(f'Found free TTY tty_file={args.tty_file} debugger_snr={args.debugger_snr}')

        if not tty_exists(args.tty_file):
            log(f'The TTY tty_file={args.tty_file} does not exist.')
            # If an active hub is used, the board could be unplugged right now
            if not self._replug_and_find_tty(args):
                return f'{IUTMode.TTY} IUT mode: {repr(args.tty_file)} serial port does not exist!\n'

        if args.debugger_snr is None:
            args.debugger_snr = get_debugger_snr(args.tty_file)

        if args.tty_file.startswith("COM"):
            try:
                args.tty_file = com_to_tty(args.tty_file)
            except ValueError:
                return f'{IUTMode.TTY} IUT mode: Port {args.tty_file} is not a valid COM port!\n'

        return ''

    def check_args_tty(self, args):
        if not args.board_name:
            return f'{IUTMode.TTY} IUT mode: specify board_name\n'

        return ''

    def check_args_qemu(self, args):
        if not args.qemu_bin:
            return f'{IUTMode.QEMU} IUT mode: specify qemu_bin parameter to use this mode\n'

        if not shutil.which(args.qemu_bin):
            return f'{IUTMode.QEMU} IUT mode: qemu_bin={args.qemu_bin}, but not found!\n'

        if args.kernel_image:
            if not os.path.isfile(args.kernel_image):
                return f'{IUTMode.QEMU} IUT mode: kernel_image={repr(args.kernel_image)} is not a file!\n'
        elif not args.project_path:
            return f'{IUTMode.QEMU} IUT mode: specify kernel_image or project_path to use this IUT mode\n'

        return ''

    def check_args_native(self, args):
        if args.kernel_image:
            if not os.path.isfile(args.kernel_image):
                return f'{IUTMode.NATIVE} IUT mode: kernel_image {repr(args.kernel_image)} is not a file!\n'
        elif not args.project_path:
            return f'{IUTMode.NATIVE} mode: specify kernel_image or project_path to use this IUT mode\n'

        return ''

    def check_args_btpclient_path(self, args):
        if not os.path.exists(args.btpclient_path):
            return (
                f'{IUTMode.BTPCLIENT_PATH} IUT mode: Path {repr(args.btpclient_path)} of btp client '
                'does not exist!\n'
            )
        return ''

    def check_args_btp_tcp_client(self, args):
        if not 49152 <= args.btp_tcp_port <= 65535:
            return (
                f'{IUTMode.BTPCLIENT_TCP} IUT mode: Invalid server port number={args.btp_tcp_port}, expected '
                'range <49152,65535>'
            )
        return ''

    def get_iut_mode(self, args):
        # Specify IUT mode explicitly, or it will be inferred
        # from the parameters.
        if args.iut_mode:
            return IUTMode(args.iut_mode)

        if args.qemu_bin:
            return IUTMode.QEMU

        if args.kernel_image or args.hid_serial or args.hci is not None:
            return IUTMode.NATIVE

        if args.btpclient_path:
            return IUTMode.BTPCLIENT_PATH

        if args.btp_tcp_port:
            return IUTMode.BTPCLIENT_TCP

        return IUTMode.TTY

    def parse(self, arg_ns=None):
        """Parsing and sanity check command line arguments
        Args:
            arg_ns: namespace of arguments and parameters to overwrite
                    with the command line arguments parser

        Returns: (args, errmsg)
            where
            args: namespace of parameters overwritten with parsed
                  command line arguments
            errmsg: an error message if parsing failed, otherwise empty string
        """
        errmsg = ''

        args = self.parse_args(None, arg_ns)

        from autopts.client import init_logging
        init_logging('_' + '_'.join(str(x) for x in args.cli_port),
                     FILE_PATHS.get('BOT_LOG_FILE', None))

        if args.btproxy_bin and not is_executable(args.btproxy_bin):
            return args, f'The btproxy_bin={args.btproxy_bin} is not an executable file'

        if args.btattach_bin and not is_executable(args.btattach_bin):
            return args, f'The btattach_bin={args.btattach_bin} is not an executable file'

        args.superguard = 60 * args.superguard

        if not args.ip_addr:
            args.ip_addr = ['127.0.0.1'] * len(args.srv_port)

        if not args.local_addr:
            args.local_addr = ['127.0.0.1'] * len(args.cli_port)

        for iut_name in args.iut_targets_args:
            _args = args.iut_targets_args[iut_name]
            _args.iut_mode = self.get_iut_mode(_args)
            _args.superguard = args.superguard
            _args.ip_addr = args.ip_addr
            _args.local_addr = args.local_addr
            log(f'IUT {iut_name} works in {_args.iut_mode} mode.\n')

            if _args.ykush or _args.active_hub_server:
                _args.usb_replug_available = True
            else:
                _args.usb_replug_available = False

            if sys.platform == "win32" and _args.iut_mode in [IUTMode.QEMU, IUTMode.NATIVE]:
                errmsg = f'The {_args.iut_mode} mode is not supported under Windows!'
                return args, errmsg

            if _args.iut_mode == IUTMode.TTY or \
                    (_args.iut_mode == IUTMode.NATIVE and _args.tty_file or
                     _args.tty_alias or _args.debugger_snr):
                self.find_tty(_args)

            check_method = self.check_methods[_args.iut_mode]
            errmsg = check_method(_args)

        if args.wid_run:
            self.wid_run_tcs(args)

        return args, errmsg


def is_executable(path):
    return os.path.exists(path) and os.access(path, os.X_OK)
