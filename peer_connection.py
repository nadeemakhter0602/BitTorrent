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
            recv = self.conn.recv(68)
            print("Received response :", recv)
            deserialized = self.deserialize_handshake(recv)
            print("Deserialized response :", deserialized)
            protocol_identifier, pstr, reserved_bytes, info_hash, peer_id = deserialized
            self.peer.peer_id = peer_id
            if info_hash == self.torrent.info_hash:
                print("Handshake Completed, Peer ID is %s" % peer_id)
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

    def deserialize_handshake(self, handshake):
        protocol_identifier = handshake[0]
        pstr = handshake[1:20]
        reserved_bytes = handshake[20:28]
        info_hash = handshake[28:48]
        peer_id = handshake[48:68]
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
