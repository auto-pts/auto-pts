import subprocess
import os
import logging

log = logging.debug


# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"
QEMU_UNIX_PATH = "/tmp/ubt_tester"

# qemu log file object
QEMU_LOG_FO = None

# microkernel.elf
ZEPHYR_KERNEL_IMAGE = None

class ZephyrCtl:
    '''Zephyr OS Control Class'''

    def __init__(self):
        """Constructor."""

        assert ZEPHYR_KERNEL_IMAGE, "Kernel image file is not set!"


        self.kernel_image = ZEPHYR_KERNEL_IMAGE
        self.qemu_process = None

    def start(self):
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        qemu_cmd = "%s -cpu cortex-m3 -machine lm3s6965evb -nographic " \
                        "-serial mon:stdio -serial unix:/tmp/bt-server-bredr " \
                        "-serial unix:%s -kernel %s" \
                        % (QEMU_BIN, QEMU_UNIX_PATH, self.kernel_image)

        log("Starting QEMU zephyr process: %s", qemu_cmd)

        # TODO check if zephyr process has started correctly
        self.qemu_process = subprocess.Popen("exec " + qemu_cmd,
                                             shell = True,
                                             stdout = QEMU_LOG_FO,
                                             stderr = QEMU_LOG_FO)

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.qemu_process != None:
            self.qemu_process.terminate()
            self.qemu_process.wait() # do not let zombies take over

def init(kernel_image):
    """IUT init routine

    kernel_image -- Path to Zephyr kernel image"""

    global QEMU_LOG_FO
    global ZEPHYR_KERNEL_IMAGE

    QEMU_LOG_FO = open("qemu-zephyr.log", "w")

    if not os.path.isfile(kernel_image):
        raise Exception("QEMU kernel image %s is not a file!" %
                        repr(kernel_image))

    ZEPHYR_KERNEL_IMAGE = kernel_image

def cleanup():
    """IUT cleanup routine"""
    global QEMU_LOG_FO
    QEMU_LOG_FO.close()
    QEMU_LOG_FO = None
