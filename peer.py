import secrets

class Peer:
    def __init__(self, port, ipaddr=None, peer_id=None):
        if not peer_id:
            self.peer_id = bytes.fromhex(secrets.token_hex(20))
        else:
            self.peer_id = peer_id
        self.port = port
        self.ipaddr = ipaddr
