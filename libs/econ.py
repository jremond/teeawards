import threading
import Queue
import telnetlib
import re
import time

from libs.lib import econ_command_queue

class EconClient(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.tn = None
        self.stop = threading.Event()

    def stop_server(self):
        self.stop.set()

    def stopped(self):
        return self.stop.isSet()

    def connect(self):
        self.tn = telnetlib.Telnet('localhost', 9999)
        self.tn.read_until("Enter password:")
        self.tn.write("teeawards\n")
        self.tn.read_until("[econ]: cid=0 authed")

    def disconnect(self):
        self.tn.close()

    def command(fnt):
        def wrapper(self, **kwargs):
            # Handle disconnected
            if not self.tn:
                self.connect()
            elif not self.tn.sock:
                self.connect()
            fnt(self, **kwargs)
        return wrapper

    # COMMANDS
    @command
    def broadcast(self, message):
        self.tn.write("broadcast %s\n" % message)

    @command
    def kick(self, player, message):
        self.tn.read_very_eager()
        self.tn.write("status\n")
        time.sleep(0.5)
        lines = self.tn.read_very_eager()
        for line in lines.splitlines():
            if re.match("\[Server\]: id=([0-9]*) addr=.*:[0-9]* name='%s' score=[0-9]*" % player, line):
                player_id = re.match("\[Server\]: id=([0-9]*) addr=.*:[0-9]* name='%s' score=[0-9]*" % player, line).groups()[0]
                self.tn.write("kick %s %s\n" % (player_id, message))

    # Thread
    def run(self):
        timeout = 2
        round_ = None

        while not self.stopped():
            try:
                command = econ_command_queue.get(True, 2)
            except Queue.Empty:
                continue
#            print "command", command
            getattr(self, command['type'])(**command['data'])


econ_client = EconClient()
econ_client.start()
