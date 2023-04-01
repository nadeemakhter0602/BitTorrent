import announce
import socket
from torrent import Torrent
from peer import Peer
import traceback


class Connection:
    def __init__(self, client, peer, torrent):
        self.client = client
        self.peer = peer
        self.ip_port = (self.peer.ipaddr, self.peer.port)
        self.torrent = torrent
        self.conn = socket.socket()
        self.is_connected = False
        self.is_choked = True
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

    def send_message(self, msg_id, payload):
        try:
            if not self.is_connected:
                print("No peer connected")
                return
            if not self.handshake_done:
                print("No handshake completed with peer")
                return
            if self.is_choked:
                print("Choked by other peer, waiting for unchoke message")
                length, msg_id, payload = self.deserialize_message()
                if not (length == 1 and msg_id == 1):
                    print("Did not receive unchoke message")
                    return
            self.is_choked = False
            print("Received unchoke message, sending requested message")
            message = self.serialize_message(msg_id, payload)
            self.conn.send(message)
            deserialized = self.deserialize_message()
            print("Deserialized response :", deserialized)
            length, msg_id, payload = deserialized
        except:
            print("Sending message failed due to error :")
            traceback.print_exc()
            pass

    def deserialize_message(self):
        conn = self.conn
        length = conn.recv(4)
        length = int.from_bytes(length, 'big')
        if length <= 0:
            return None, None, None
        msg_id = conn.recv(1)
        msg_id = int.from_bytes(1, msg_id)
        payload_len = length - 5
        if payload_len <= 0:
            return None, None, None
        payload = conn.recv(payload_len)
        return length, msg_id, payload

    def serialize_message(self, msg_id, payload):
        msg_id = msg_id.to_bytes(1, 'big')
        payload = msg_id + payload
        length = int(payload)
        payload = length.to_bytes(4, 'big') + payload
        return payload

    def connect_peer(self):
        try:
            print("Attempting to connect to %s" % str(self.ip_port))
            self.conn.connect(self.ip_port)
            self.is_connected = True
            print("Successfully connected to %s" % str(self.ip_port))
        except Exception as err:
            print("Connection failed due to error :")
            traceback.print_exc()
            pass

    def send_handshake(self):
        try:
            if not self.is_connected:
                print("No peer connected")
                return
            handshake = self.serialize_handshake()
            print("Sending handshake :", handshake)
            self.conn.send(handshake)
            deserialized = self.deserialize_handshake()
            print("Deserialized response :", deserialized)
            protocol_identifier, pstr, reserved_bytes, info_hash, peer_id = deserialized
            self.peer.peer_id = peer_id
            if info_hash == self.torrent.info_hash:
                print("Handshake Completed, Peer ID is %s" % peer_id)
                self.handshake_done = True
            else:
                print("Invalid Info Hash received from Peer %s with ID %s" % (str(self.ip_port), peer_id))
        except Exception as err:
            print("Handshake failed due to error :")
            traceback.print_exc()
            pass

    def close_connection(self):
        self.conn.close()

    def serialize_handshake(self):
        handshake = self.protocol_identifier
        handshake += self.pstr
        handshake += self.reserved_bytes
        handshake += self.torrent.info_hash
        handshake += self.client.peer_id
        return handshake

    def deserialize_handshake(self):
        conn = self.conn
        protocol_identifier = conn.recv(1)
        pstr = conn.recv(19)
        reserved_bytes = conn.recv(8)
        info_hash = conn.recv(20)
        peer_id = conn.recv(20)
        return protocol_identifier, pstr, reserved_bytes, info_hash, peer_id


if __name__ == '__main__':
    client = Peer('6881')
    torrent = Torrent('test.torrent', './')
    length = torrent.length
    event = 'started'
    compact = '1'
    uploaded = 0
    downloaded = 0
    tracker_response = announce.announce(torrent,
                                         client,
                                         uploaded,
                                         downloaded,
                                         length,
                                         event,
                                         compact)
    peer_list = announce.get_peers(tracker_response)
    for peer in peer_list:
        peer = Peer(ipaddr=peer[0], port=peer[1])
        print()
        connection = Connection(client, peer, torrent)
        connection.connect_peer()
        print()
        connection.send_handshake()
        connection.close_connection()
        print()
