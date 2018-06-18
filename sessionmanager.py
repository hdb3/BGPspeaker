#
# threading based framework for reliably starting anf managing BGP FSMs on multiple peer sessions
#
# the session manager launches threads to initiate outbound sessions to peers
# and also starts a TCP server socket to accept incoming sessions from remote BGP peers
#
# the session manager is configured with a list of peers to connect to, consisting of a list of IP addresses
# the BGP speaker uses just the well known TCP port 179

#
# sessionmanager is always waiting for incoming sessions
# for outbound sessions sessionmanager tries to keep an active session request running unless there is
# already one session for that peer.  A list of active peers is used for this purpose
#

import errno
import sys
import socket
import concurrent.futures

_BGP_PORT = 179
_NEW_ACTIVE_SOCKET = 1
_NEW_PASSIVE_SOCKET = 2
_OLD_SOCKET = 3
_TIMEOUT_SOCKET = 4

class SessionManager:

    def __init__(self,peerlist,timeout=10.0):
        self.active_peers = {}
        self.timeout = timeout
        try:
            print("binding to port %d" % _BGP_PORT)
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("",_BGP_PORT))
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
                # completed futures may return new sockets, which require to run the FSM
                # or old sockets from an exiting FSM
                # or a timeout after unsuccesful active session request
                # some of which may require to start another listener/talker

                for f in done:
                    status,sock,peer = f.result()
                    if _NEW_ACTIVE_SOCKET == status or _NEW_PASSIVE_SOCKET == status:
                        remote_address = sock.getpeername()
                        local_address = sock.getsockname()
                        # if the socket is a passive one the local port will be the well known one
                        # if the socket is an active one the remote port will be the well known one
                        # it should never be the case that either both or neither port is well known
                        assert remote_address[1] != local_address[1]
                        assert remote_address[1] == _BGP_PORT or local_address[1] == _BGP_PORT
                        print("new connection to %s" % str(remote_address[0]))
                        if _NEW_ACTIVE_SOCKET == status:
                            assert remote_address[1] == _BGP_PORT
                        else: # _NEW_PASSIVE_SOCKET == _BGP_PORT
                            assert local_address[1] == _BGP_PORT
                            print("rescheduling passive port listener")
                            futures.append(executor.submit(self.get_passive_socket))
                        if remote_address[0] not in self.active_peers:
                            self.active_peers[remote_address[0]] = 0
                        self.active_peers[remote_address[0]] += 1
                        futures.append(executor.submit(self.fsm,sock,peer))
                    elif _OLD_SOCKET == status:
                        assert peer in self.active_peers
                        self.active_peers[peer] -= 1
                        assert self.active_peers[peer] >= 0
                        # exiting FSM - check if we need to restart an active session request thread
                        if self.active_peers[peer] == 0 and peer in self.peerlist:
                            futures.append(executor.submit(self.get_active_socket,peer))
                        try:
                            sock.shutdown(socket.SHUT_RDWR)
                            sock.close()
                        except Exception as e:
                            self.log_err("ignored exception closing socket: %s\n" % str(e))

                    elif _TIMEOUT_SOCKET == status:
                        if peer in self.active_peers and self.active_peers[peer] == 0 and peer in self.peerlist:
                            futures.append(executor.submit(self.get_active_socket,peer))
                    else:
                        assert False

    def get_passive_socket(self):

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
        return (_NEW_PASSIVE_SOCKET,sock,remote_address[0])

    def get_active_socket(self,peer):

        try:
            print("connecting to %s" % str(peer))
            sock = socket.create_connection((peer,_BGP_PORT),self.timeout)
            remote_address = sock.getpeername()
            sock.setblocking(True)
            print("connection complete to %s" % str(remote_address))
        except socket.timeout as e:
            return (None,peer)
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
        return (_NEW_ACTIVE_SOCKET,sock,remote_address[0])

    def fsm(self,sock,peer):
        sock.send("Hello from %s" % str())
        while True:
            msg = sock.recv()
            if len(msg) == 0:
                break
            else:
                sock.send(msg)

    def _fsm(self,sock,peer):
        self.fsm(self,sock,peer)
        return (_OLD_SOCKET,sock,peer)
