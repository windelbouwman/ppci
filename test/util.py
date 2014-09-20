
import os
import subprocess
import socket
import time
import shutil
import logging

# Store testdir for safe switch back to directory:
testdir = os.path.dirname(os.path.abspath(__file__))


def relpath(*args):
    return os.path.normpath(os.path.join(testdir, *args))

qemu_app = 'qemu-system-arm'


def tryrm(fn):
    try:
        os.remove(fn)
    except OSError:
        pass


def has_qemu():
    """ Determines if qemu is possible """
    if not hasattr(shutil, 'which'):
        return False
    return bool(shutil.which(qemu_app))


def run_qemu(kernel, machine='lm3s811evb'):
    """ Runs qemu on a given kernel file """

    logger = logging.getLogger('runqemu')
    if not has_qemu():
        return ''
    # Check bin file exists:
    assert os.path.isfile(kernel)

    logger.debug('Running qemu')

    tryrm('qemucontrol.sock')
    tryrm('qemuserial.sock')

    # Listen to the control socket:
    qemu_control_serve = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    qemu_control_serve.bind('qemucontrol.sock')
    qemu_control_serve.listen(0)

    # Listen to the serial output:
    qemu_serial_serve = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    qemu_serial_serve.bind('qemuserial.sock')
    qemu_serial_serve.listen(0)

    args = [qemu_app, '-M', machine, '-m', '16M',
            '-nographic',
            '-kernel', kernel,
            '-monitor', 'unix:qemucontrol.sock',
            '-serial', 'unix:qemuserial.sock',
            '-S']
    p = subprocess.Popen(args)  # , stderr=subprocess.DEVNULL)

    # qemu_serial Give process some time to boot:
    qemu_serial_serve.settimeout(3)
    qemu_control_serve.settimeout(3)
    qemu_serial, address_peer = qemu_serial_serve.accept()
    qemu_control, address_peer = qemu_control_serve.accept()

    # Give the go command:
    qemu_control.send('cont\n'.encode('ascii'))

    qemu_serial.settimeout(0.2)

    # Receive all data:
    data = bytearray()
    for i in range(1400):
        try:
            c = qemu_serial.recv(1)
            if c == bytes([4]):  # EOT (end of transmission)
                break
            data += c
        except socket.timeout:
            break
    data = data.decode('ascii', errors='ignore')
    # print('data', data)

    # Send quit command:
    qemu_control.send("quit\n".encode('ascii'))
    if hasattr(subprocess, 'TimeoutExpired'):
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()
    else:
        time.sleep(2)
        p.kill()
    qemu_control.close()
    qemu_serial.close()
    qemu_control_serve.close()
    qemu_serial_serve.close()

    logger.debug('Qemu closed')

    tryrm('qemucontrol.sock')
    tryrm('qemuserial.sock')

    # Check that output was correct:
    return data


def run_python(kernel):
    """ Run given file in python and capture output """
    python_proc = subprocess.Popen(['python', kernel], stdout=subprocess.PIPE)
    outs, _ = python_proc.communicate()
    outs = outs.decode('ascii', errors='ignore')
    return outs


def gnu_assemble(source, as_args=[], prefix='arm-none-eabi-'):
    """ Helper function to feed source through gnu assembling tools """
    prefix = 'arm-none-eabi-'
    gas = '{}as'.format(prefix)
    objdump = prefix + 'objdump'
    print('assembling...')
    p_as = subprocess.Popen([gas] + as_args, stdin=subprocess.PIPE)
    p_as.communicate(input=source.encode('ascii'))
    if p_as.returncode != 0:
        raise Exception('{}'.format(p_as.returncode))

    p_objdump = subprocess.Popen([objdump, '-d'], stdout=subprocess.PIPE)
    output = p_objdump.communicate()[0].decode('ascii')
    if p_objdump.returncode != 0:
        raise Exception('{}'.format(p_objdump.returncode))
    print(output)

    p_objdump = subprocess.Popen([objdump, '-s', '-j', '.text'],
                                 stdout=subprocess.PIPE)
    output = p_objdump.communicate()[0].decode('ascii')
    if p_objdump.returncode != 0:
        raise Exception('{}'.format(p_objdump.returncode))
    print(output)
    return output
