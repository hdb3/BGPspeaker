#
# threading based framework for reliably starting anf managing BGP FSMs on multiple peer sessions
#
# the session manager launches threads to initiate outbound sessions to peers
# and also starts a TCP server socket to accept incoming sessions from remote BGP peers
#
# the session manager is configured with a list of peers to connect to, consisting of a list of IP addresses
# the BGP speaker uses just the well known TCP port 179


class SessionManager:

   def __init__(self,peerlist):
   
      self.peerlist = peerlist
      for peer in peerlist:
         peerstate = {}
         peers[peer] = peerstate
         peerstate[lock] = threading.lock()
         self.thread = ActiveSession(args=(peer))
         self.thread.start()
      self.passive_thread =  PassiveSession()
      self.passive_thread.start()
