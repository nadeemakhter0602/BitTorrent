import announce
import socket
from torrent import Torrent
from peer import Peer
import traceback


class Connection:
    def __init__(self, peer, torrent):
        self.peer = peer
        self.torrent = torrent
        self.conn = socket.socket()
        self.protocol_identifier = b'\x13'
        self.pstr = b'BitTorrent protocol'
        self.reserved_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00'

    def send_handshake(self, peer):
        try:
            print("Attempting to connect to %s" % str(peer))
            self.conn.connect(peer)
            handshake = self.serialize_handshake()
            print("Sending handshake :", handshake)
            self.conn.send(handshake)
            recv = self.conn.recv(68)
            print("Received response :", recv)
            deserialized = self.deserialize_handshake(recv)
            print("Deserialized response :", deserialized)
            protocol_identifier, pstr, reserved_bytes, info_hash, peer_id = deserialized
        except Exception as err:
            print("Connection failed due to error :")
            traceback.print_exc()
            pass

    def close_connection(self):
        self.conn.close()

    def serialize_handshake(self):
        handshake = self.protocol_identifier
        handshake += self.pstr
        handshake += self.reserved_bytes
        handshake += self.torrent.info_hash
        handshake += self.peer.peer_id
        return handshake

    def deserialize_handshake(self, handshake):
        protocol_identifier = handshake[0]
        pstr = handshake[1:20]
        reserved_bytes = handshake[20:28]
        info_hash = handshake[28:48]
        peer_id = handshake[48:68]
        return protocol_identifier, pstr, reserved_bytes, info_hash, peer_id


if __name__ == '__main__':
    my_peer = Peer('6881')
    torrent = Torrent('test.torrent', './')
    length = torrent.length
    event = 'started'
    compact = '1'
    uploaded = 0
    downloaded = 0
    tracker_response = announce.announce(torrent,
                                         my_peer,
                                         uploaded,
                                         downloaded,
                                         length,
                                         event,
                                         compact)
    peer_list = announce.get_peers(tracker_response)
    for peer in peer_list:
        print()
        connection = Connection(my_peer, torrent)
        connection.send_handshake(peer)
        connection.close_connection()
        print()
