import errno
import sys
import socket
import threading
from time import sleep

class ActiveSession(Threading):

    def __init__(self,peer,timeout):
        self.peer = peer
        self.timeout = timeout
    
    def log_err(self,s):
        print(s,file=sys.stderr)
    
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
                self.sock = socket.create_connection(self.peer,self.timeout)
                self.remote_address = self.sock.getpeername()
                self.sock.setblocking(True)
                self.state = Connected
                self.connections += 1
                self.log_err("connected to %s\n" % _name(self.address))
                self.connections += 1
                self.fsm()
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
                
        def fsm(self):
            self.socket.send("Hello from %s" % str())
            while True:
                msg = self.socket.recv()
                self.socket.send(msg)
