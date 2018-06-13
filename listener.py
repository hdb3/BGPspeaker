import errno
import sys
import socket
import threading
from time import sleep

#
# this generic listener runs a loop on a socket and spawns a thread for each incoming connection
#

class PassiveThread(Threading):

    def __init__(self,socket,address):
        self.socket = socket
        self.address = address

    def run(self):
        self.fsm()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except Exception as e:
            self.log_err("ignored exception closing listen socket: %s\n" % str(e))
            
    def fsm(self):
        while True:
            msg = self.socket.recv()
            self.socket.send(msg)
            
class Listener:

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def run(self):
        self.state = Connecting
        self.log_err("awaiting connection on %s\n" % _name(self.address))
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(100):
            try:
                self.state = Error
                self.server_socket.bind(self.address)
                self.state = Connecting
                if i > 0:
                    self.log_err("bind success!")
                break
            except OSError as e:
                if e.errno != errno.EADDRINUSE:
                    raise
                else:
                    if i == 0:
                        self.log_err("bind - address in use - will wait and try again")
                    else:
                        log("~")
                    sleep(3)
            except (socket.herror,socket.gaierror) as e:
                self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % _name(self.address))
                self.state = Error
            except Exception as e:
                self.log_err(("unknown error %s" % e) + (" connecting to %s\n" % _name(self.address)))
                self.state = Error

        if self.state == Error:
            self.log_err("bind - address in use - giving up")
            exit()

        self.server_socket.listen()

        while self.state != Error:
            try:
                self.sock,self.remote_address = self.server_socket.accept()
                self.sock.setblocking(True)
                self.state = Connected
                self.connections += 1
                self.log_err("connected to %s\n" % _name(self.remote_address))
                thread = PassiveThread(self.sock,self.remote_address)
                thread.start()
            except (socket.herror,socket.gaierror) as e:
                self.log_err("unrecoverable error %s" % e + " connecting to %s\n" % _name(self.address))
                self.state = Error
                break
            except Exception as e:
                self.log_err(("unknown error %s" % e) + (" connecting to %s\n" % _name(self.address)))
                self.state = Error
                sleep(10)
                self.log_err("reawaiting connection on %s\n" % _name(self.address))
                continue

