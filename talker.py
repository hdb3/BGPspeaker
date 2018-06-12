import os.path
import errno
import yaml
import traceback
import sys
import socket
import threading
from time import sleep

class Talker(Collector):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def run(self):
        self.state = Connecting
        while True:
            try:
                if self.state == Connecting:
                    # only print out the message once per new connection attempt
                    # i.e. not every 1 second whilst retrying after timeout
                    if self.connections == 0:
                        self.log_err("attempting connection to %s\n" % _name(self.address))
                    else:
                        self.log_err("reattempting connection to %s\n" % _name(self.address))
                self.sock = socket.create_connection(self.address,1)
                self.remote_address = self.sock.getpeername()
                self.sock.setblocking(True)
                self.state = Connected
                self.connections += 1
                self.log_err("connected to %s\n" % _name(self.address))
                self.connections += 1
                session = Session(self.app,self.appconfig,self.name,self.remote_address,self.send,self.recv)
                self.sock.close()
                self.sock.shutdown(socket.SHUT_RDWR)
            except (socket.error,socket.timeout) as e:
                self.last_socket_error = e
                self.state = Retrying
                sleep(1)
                continue
            except (socket.herror,socket.gaierror) as e:
                self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % _name(self.address))
                traceback.print_tb( sys.exc_info()[2],limit=9)
                self.state = Error
                break
            except Exception as e:
                self.log_err("unknown error %s" % e + " connecting to %s\n" % _name(self.address))
                traceback.print_tb( sys.exc_info()[2],limit=9)
                self.state = Error
                break

