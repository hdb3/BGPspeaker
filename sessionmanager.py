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

import sys, os, errno, socket, concurrent.futures
from time import sleep

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
            print("peerlist: ",str(peerlist))
            for peer in peerlist:
                #peerstate = {}
                #peers[peer] = peerstate
                print("scheduling active session request for",str(peer))
                futures.append(executor.submit(self.get_active_socket,peer))
            print("starting main loop")

            try:
                while True:
                    # the following code is required to ensure that exceptions (including caused by bad code)
                    # are raised - it is not possible to wait for exceptions and completions simultabeously
                    done,not_done = concurrent.futures.wait(futures, timeout=0, return_when=concurrent.futures.FIRST_EXCEPTION)
                    if done:
                        print("an exception occured in a running thread")
                        for f in done:
                            f.result()
                    done,not_done = concurrent.futures.wait(futures, timeout=1.0, return_when=concurrent.futures.FIRST_COMPLETED)
                    # futures = list(not_done)
                    # completed futures may return new sockets, which require to run the FSM
                    # or old sockets from an exiting FSM
                    # or a timeout after unsuccesful active session request
                    # some of which may require to start another listener/talker
                    if not done:
                        print("heartbeat")

                    for f in done:
                    # for f in concurrent.futures.as_completed(futures):
                        # futures.remove(f)
                        # status,sock,peer = f.result()
                        result = f.result()
                        status,sock,peer = result
                        print("Main loop event: %s" % str(result) )
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
                            print("scheduling FSM for",str(peer))
                            futures.append(executor.submit(self._fsm,sock,peer))
                            print("scheduled FSM for",str(peer))
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
                            # fixme - don't catch all excepetions - what are we trying to catch?
                            except Exception as e:
                                print("ignored exception closing socket: %s\n" % str(e))

                        elif _TIMEOUT_SOCKET == status:
                            assert peer in self.peerlist
                            if peer not in self.active_peers or self.active_peers[peer] == 0:
                                futures.append(executor.submit(self.get_active_socket,peer))
                        else:
                            assert False
            except KeyboardInterrupt:
                executor.shutdown(wait=False)
                kill_child_processes(os.getpid())

    def get_passive_socket(self):

        print("accepting on socket")
        try:
            sock,remote_address = self.server_socket.accept()
        except OSError as e:
            print("bind - unknown OS error %d" % e.errno)
            raise
        except (socket.herror,socket.gaierror) as e:
            print("unknown socket error %s" % e)
            raise
        except Exception as e:
            print("unknown error %s" % e)
            raise
        else:
            sock.setblocking(True)
            print("connection received from %s" % str(remote_address))
            return (_NEW_PASSIVE_SOCKET,sock,remote_address[0])

    def get_active_socket(self,peer):

        print("connecting to %s" % str(peer))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((peer,_BGP_PORT))
            # sock = socket.create_connection((peer,_BGP_PORT),self.timeout)
        except socket.timeout as e:
            sock.close()
            return (_TIMEOUT_SOCKET,None,peer)
        except ConnectionError as e:
            print("peer %s rejected connection %s" % (str(peer),e))
            sleep(self.timeout) # strictly this should be the 'idle hold timer' value which could be differetn to the connection timer.....
            return (_TIMEOUT_SOCKET,None,peer)
        except socket.error as e:
            print("unknown socket error %s" % e)
            raise
        except OSError as e:
            print("bind - unknown OS error %d" % e.errno)
            raise
        except (socket.herror,socket.gaierror) as e:
            print("unknown socket error %s" % e)
            raise
        # except Exception as e:
            # print("unknown error %s" % e)
            # raise
        else:
            remote_address = sock.getpeername()
            print("connection complete to %s" % str(remote_address))
            sock.setblocking(True)
            return (_NEW_ACTIVE_SOCKET,sock,remote_address[0])
        finally:
            print("exiting from get_active_socket")

    def fsm(self,sock,peer):
        print("FSM starts for connection to",peer)
        sock.send("Hello from %s" % str())
        print("FSM sent first message to",peer)
        while True:
            msg = sock.recv()
            if len(msg) == 0:
                print("FSM lost connection to",peer)
                break
            else:
                print("FSM received message from",peer)
                sock.send(msg)
        print("FSM ends for connection to",peer)

    def _fsm(self,sock,peer):
        print("wrapping FSM for",str(peer))
        self.fsm(sock,peer)
        print("unwrapping FSM for",str(peer))
        return (_OLD_SOCKET,sock,peer)

# ugly hack because concurrent.futures has no way to kill child threads
# see https://stackoverflow.com/questions/42782953/python-concurrent-futures-how-to-make-it-cancelable/

import signal, psutil

def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)
