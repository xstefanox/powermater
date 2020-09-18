from evdev import InputDevice, ecodes, list_devices
import subprocess
import sys
import errno
import logging

VOLUME_CMD = ['amixer', '-D', 'pulse', 'sset', 'Master']
MUTE_TOGGLE = 0


class DeviceNotFound(Exception):
    pass


def find_device():
    devices = [InputDevice(fn) for fn in list_devices()]
    for device in devices:
        if device.name.find('PowerMate') != -1:
            print('Device found: ' + device.name + ' (' + device.phys + ')')
            run(device.fn)
            sys.exit()
    raise DeviceNotFound


def execute(cmd, logger):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stdout:
        logger.debug(stdout)
    if stderr:
        logger.debug(stderr)


def run(device):
    """
    Monitor the given device and modify the sound volume

    :param device: the name of the device to read
    """

    logger = logging.getLogger('powermated')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    logger.debug('Listening on ' + device)

    try:

        for event in InputDevice(device).read_loop():

            # ignore synchronization events
            if event.type == ecodes.EV_SYN:
                continue

            logger.debug('Received event: ' + str(event))

            # event action: mute
            if event.type == ecodes.EV_KEY:

                cmd = VOLUME_CMD[:]
                cmd.append('toggle')

                if event.value == MUTE_TOGGLE:
                    execute(cmd, logger)

            # event action: volume
            elif event.type == ecodes.EV_REL:

                cmd = VOLUME_CMD[:]
                cmd.append(str(abs(event.value)) + '%')

                if event.value > 0:
                    cmd[-1] += '+'
                else:
                    cmd[-1] += '-'

                execute(cmd, logger)

    except IOError as e:

        if e.errno == errno.ENODEV:
            logger.debug('Device unplugged')
        else:
            logger.error(e.message)
            raise e

    except KeyboardInterrupt:
        logger.debug('Terminating')

    except OSError as e:
        logger.debug('Error: ' + str(e.strerror))


def main():
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        print('Attempting to find device...')
        try:
            find_device()
        except DeviceNotFound:
            print("Couldn't find device.\nTry: powermated <device>")
            sys.exit()


if __name__ == "__main__":
    main()
