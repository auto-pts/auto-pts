#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
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

"""Utilities"""

import ctypes
import threading


class InterruptableThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(),
                 kwargs=None, *, daemon=None, queue=None, final_fun=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, args=args,
                                  kwargs=kwargs, daemon=daemon)
        self.queue = queue
        self.final_fun = final_fun

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except BaseException as exc:
            if self.queue:
                self.queue.put(exc)
        finally:
            if self.final_fun:
                self.final_fun()
            del self._target, self._args, self._kwargs

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for _id, thread in threading._active.items():
            if thread is self:
                return _id
        return None

    def interrupt(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')
