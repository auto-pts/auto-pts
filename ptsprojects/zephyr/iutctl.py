import subprocess
import os
import logging

log = logging.debug


# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-i386"

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

        qemu_cmd = "%s -m 32 -cpu qemu32 -no-reboot -nographic -display none " \
                   "-net none -clock dynticks -no-acpi -balloon none " \
                   "-no-hpet -L /usr/share/qemu -bios bios.bin -serial " \
                   "mon:stdio -machine type=pc-0.14 -pidfile qemu.pid " \
                   "-serial unix:/tmp/bt-server-bredr -kernel %s" \
                   % (QEMU_BIN, self.kernel_image)

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
