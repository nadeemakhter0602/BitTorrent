import secrets

class Peer:
    def __init__(self, port):
        self.peer_id = bytes.fromhex(secrets.token_hex(20))
        self.port = port
