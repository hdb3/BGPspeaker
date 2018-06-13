#
# threading based framework for reliably starting anf managing BGP FSMs on multiple peer sessions
#
# the session manager launches threads to initiate outbound sessions to peers
# and also starts a TCP server socket to accept incoming sessions from remote BGP peers
#
# the session manager is configured with a list of peers to connect to, consisting of a list of IP addresses
# the BGP speaker uses just the well known TCP port 179

import Talker
import Listener

class SessionManager:

   def __init__(self,peerlist,timeout=10.0):
      # self.timeout = timeoute
      self.peerlist = peerlist
      for peer in peerlist:
         peerstate = {}
         peers[peer] = peerstate
         peerstate[lock] = threading.lock()
         self.thread = ActiveSession(args=(peer,timeout))
         self.thread.start()
      self.passive_thread =  PassiveSession()
      self.passive_thread.start()
