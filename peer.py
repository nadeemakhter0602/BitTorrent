class Peer:
    def __init__(self, port, ipaddr, peer_id=None):
        self.peer_id = peer_id
        self.port = port
        self.ipaddr = ipaddr
