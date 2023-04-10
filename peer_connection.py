import socket
import traceback


class Connection:
    def __init__(self, client, peer, torrent):
        self.client = client
        self.peer = peer
        self.ip_port = (self.peer.ipaddr, self.peer.port)
        self.torrent = torrent
        self.conn = socket.socket()
        self.is_connected = False
        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False
        self.handshake_done = False
        self.protocol_identifier = b'\x13'
        self.pstr = b'BitTorrent protocol'
        self.reserved_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        self.msg_choke = 0
        self.msg_unchoke = 1
        self.msg_interested = 2
        self.msg_not_interested = 3
        self.msg_have = 4
        self.msg_bitfield = 5
        self.msg_request = 6
        self.msg_piece = 7
        self.msg_cancel = 8

    def recv(self, size):
        recv_bytes_len = 0
        total_bytes = b''
        while recv_bytes_len < size:
            recv_bytes = self.conn.recv(size - recv_bytes_len)
            if recv_bytes == b'':
                raise RuntimeError("Connection Broken")
            total_bytes += recv_bytes
            recv_bytes_len += len(recv_bytes)
        return total_bytes

    def send_message(self, msg_id, payload=b''):
        if not self.is_connected:
            raise Exception("No peer connected")
        if not self.handshake_done:
            raise Exception("No handshake completed with peer")
        message = self.serialize_message(msg_id, payload)
        self.conn.sendall(message)
        return True

    def receive_message(self):
        if not self.is_connected:
            raise Exception("No peer connected")
        if not self.handshake_done:
            raise Exception("No handshake completed with peer")
        deserialized = self.deserialize_message()
        length, msg_id, payload = deserialized
        return length, msg_id, payload

    def send_choke(self):
        return self.send_message(0)

    def send_unchoke(self):
        return self.send_message(1)

    def send_interested(self):
        return self.send_message(2)

    def send_not_interested(self):
        return self.send_message(3)

    def send_request(self, piece_idx, piece_offset, block_size):
        payload = piece_idx.to_bytes(4, 'big')
        payload += piece_offset.to_bytes(4, 'big')
        payload += block_size.to_bytes(4, 'big')
        self.send_message(6, payload)

    def receive_bitfield(self):
        length, msg_id, payload = self.receive_message()
        if msg_id != 5:
            raise Exception("No bitfield received")
        return payload

    def deserialize_message(self):
        conn = self.conn
        length = self.recv(4)
        length = int.from_bytes(length, 'big')
        if length <= 0:
            return length, None, b''
        msg_id = self.recv(1)
        msg_id = int.from_bytes(msg_id, 'big')
        payload_len = length - 1
        if payload_len <= 0:
            return length, msg_id, b''
        payload = self.recv(payload_len)
        if payload_len == len(payload):
            return length, msg_id, payload
        else:
            raise Exception("Expected payload length and received payload length is different")

    def serialize_message(self, msg_id, payload):
        msg_id = msg_id.to_bytes(1, 'big')
        payload = msg_id + payload
        length = len(payload)
        payload = length.to_bytes(4, 'big') + payload
        return payload

    def connect_peer(self):
        self.conn.connect(self.ip_port)
        self.is_connected = True
        return self.is_connected

    def send_handshake(self):
        if not self.is_connected:
            raise Exception("No peer connected")
        handshake = self.serialize_handshake()
        self.conn.sendall(handshake)
        deserialized = self.deserialize_handshake()
        protocol_identifier, pstr, reserved_bytes, info_hash, peer_id = deserialized
        self.peer.peer_id = peer_id
        if info_hash == self.torrent.info_hash:
            self.handshake_done = True
            return self.handshake_done
        else:
            raise Exception("Invalid Info Hash received from Peer %s with ID %s" % (str(self.ip_port), peer_id))
        return self.handshake_done

    def close_connection(self):
        self.conn.close()
        self.is_connected = False
        return self.is_connected

    def serialize_handshake(self):
        handshake = self.protocol_identifier
        handshake += self.pstr
        handshake += self.reserved_bytes
        handshake += self.torrent.info_hash
        handshake += self.client.peer_id
        return handshake

    def deserialize_handshake(self):
        conn = self.conn
        protocol_identifier = self.recv(1)
        pstr = self.recv(19)
        reserved_bytes = self.recv(8)
        info_hash = self.recv(20)
        peer_id = self.recv(20)
        return protocol_identifier, pstr, reserved_bytes, info_hash, peer_id
