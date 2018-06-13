#
# threading based framework for reliably starting anf managing BGP FSMs on multiple peer sessions
#
# the session manager launches threads to initiate outbound sessions to peers
# and also starts a TCP server socket to accept incoming sessions from remote BGP peers
#
# the session manager is configured with a list of peers to connect to, consisting of a list of IP addresses
# the BGP speaker uses just the well known TCP port 179

import errno
import sys
import socket

BGP_PORT = 179

class SessionManager:

    def __init__(self,peerlist,timeout=10.0):
        self.timeout = timeoute
        try:
            print("binding to port %d" % BGP_PORT)
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("",port))
            self.server_socket.listen()
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print("bind - address in use")
            else:
                print("bind - unknown OS error %d" % e.errno)
            raise
        except (socket.herror,socket.gaierror) as e:
            print("unknown socket error %s" % e)
            raise
        except Exception as e:
            print("unknown error %s" % e)
            raise
        futures = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures.append(executor.submit(self.get_passive_socket))
            self.peerlist = peerlist
            for peer in peerlist:
                peerstate = {}
                peers[peer] = peerstate
                futures.append(executor.submit(self.get_active_socket,peer))

            while True:
                done,not_done = concurrent.futures.wait(futures, return_when=FIRST_COMPLETED)
                futures = not_done
                for f in done:
                    result = f.result()
                    if type(result) == socket.type:
                        remote_address = result.getpeername()
                        local_address = result.getsockname()
                    elif type(result) = tuple:


          

    def get_passive_socket(self)

        try:
            print("accepting on socket")
            sock,remote_address = self.server_socket.accept()
            sock.setblocking(True)
            print("connection received from %s" % str(remote_address))
        except OSError as e:
            print("bind - unknown OS error %d" % e.errno)
            raise
        except (socket.herror,socket.gaierror) as e:
            print("unknown socket error %s" % e)
            raise
        except Exception as e:
            print("unknown error %s" % e)
            raise
        return sock

    def get_active_socket(self,peer)

        try:
            print("connecting to %s" % str(peer))
            sock = socket.create_connection((peer,port),self.timeout)
            remote_address = self.sock.getpeername()
            sock.setblocking(True)
            print("connection complete to %s" % str(remote_address))
        except socket.timeout as e:
            return (None,(peer,port))
        except socket.error as e:
            print("unknown socket error %s" % e)
            raise
        except OSError as e:
            print("bind - unknown OS error %d" % e.errno)
            raise
        except (socket.herror,socket.gaierror) as e:
            print("unknown socket error %s" % e)
            raise
        except Exception as e:
            print("unknown error %s" % e)
            raise
        return sock
