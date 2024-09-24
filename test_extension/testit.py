# Klipper extension testing
#
# Copyright (C) 2024  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import sys, os, optparse, socket, fcntl, select, json, errno, time

# Set a file-descriptor as non-blocking
def set_nonblock(fd):
    fcntl.fcntl(fd, fcntl.F_SETFL
                , fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

def webhook_socket_create(uds_filename):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(0)
    sys.stderr.write("Waiting for connect to %s\n" % (uds_filename,))
    while 1:
        try:
            sock.connect(uds_filename)
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                time.sleep(0.1)
                continue
            sys.stderr.write("Unable to connect socket %s [%d,%s]\n"
                             % (uds_filename, e.errno,
                                errno.errorcode[e.errno]))
            sys.exit(-1)
        break
    sys.stderr.write("Connection.\n")
    return sock

class SocketHandler:
    def __init__(self, uds_filename):
        self.webhook_socket = webhook_socket_create(uds_filename)
        self.poll = select.poll()
        self.poll.register(self.webhook_socket, select.POLLIN | select.POLLHUP)
        self.socket_data = b""
    def process_socket(self):
        data = self.webhook_socket.recv(4096)
        if not data:
            sys.stderr.write("Socket closed\n")
            sys.exit(0)
        parts = data.split(b'\x03')
        parts[0] = self.socket_data + parts[0]
        self.socket_data = parts.pop()
        for line in parts:
            sys.stdout.write("GOT: %s\n" % (line,))
    def send_cmd(self, cmd):
        cm = json.dumps(cmd, separators=(',', ':'))
        sys.stdout.write("SEND: %s\n" % (cm,))
        self.webhook_socket.send(cm.encode() + b"\x03")
    def run(self):
        while 1:
            res = self.poll.poll(1000.)
            for fd, event in res:
                if fd == self.webhook_socket.fileno():
                    self.process_socket()

MY_CONFIG = """
[gcode_macro my_macro]
gcode:
  ECHO MSG='hello'
"""

def startup(sh, uuid):
    sh.send_cmd({"id": 123, "method": "extmgr/register_extension",
                 "params": {"uuid": uuid}})
    sh.send_cmd({"id": 125, "method": "extmgr/append_config",
                 "params": {'config': MY_CONFIG}})
    settings = {'test_extension': {'somevalue': 12.3}}
    sh.send_cmd({"id": 124, "method": "extmgr/acknowledge_config",
                 "params": {'config': settings}})
    sh.run()

def main():
    usage = "%prog [options] <socket filename> <uuid>"
    opts = optparse.OptionParser(usage)
    options, args = opts.parse_args()
    if len(args) != 2:
        opts.error("Incorrect number of arguments")

    sh = SocketHandler(args[0])
    startup(sh, args[1])

if __name__ == '__main__':
    main()
