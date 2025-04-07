#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2024, Codecoup.
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
from threading import Event, Lock, Timer
from time import sleep

from autopts.utils import raise_on_global_end


class Property:
    def __init__(self, data):
        self._lock = Lock()
        self.data = data

    def __get__(self, instance, owner):
        with self._lock:
            return getattr(instance, self.data)

    def __set__(self, instance, value):
        with self._lock:
            setattr(instance, self.data, value)


class WildCard:
    def __eq__(self, other):
        return True


def timeout_cb(flag):
    flag.clear()


def wait_for_queue_event(event_queue, test, timeout, remove):
    flag = Event()
    flag.set()

    t = Timer(timeout, timeout_cb, [flag])
    t.name = f'QEventTimer{t.name}'
    t.start()

    while flag.is_set():
        raise_on_global_end()

        for ev in event_queue:
            if isinstance(ev, tuple):
                result = test(*ev)
            else:
                result = test(ev)

            if result:
                t.cancel()
                if ev and remove:
                    event_queue.remove(ev)

                return ev

            # TODO: Use wait() and notify() from threading.Condition
            #  instead of sleep()
            sleep(0.5)

    return None


def wait_for_event(timeout, test, *args, **kwargs):
    if test(*args, **kwargs):
        return True

    flag = Event()
    flag.set()

    t = Timer(timeout, timeout_cb, [flag])
    t.name = f'EventTimer{t.name}'
    t.start()

    while flag.is_set():
        raise_on_global_end()

        result = test(*args, **kwargs)
        if result:
            t.cancel()
            return result

    return False
