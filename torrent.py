import hashlib
import os
from bencoding import BEncoding
import traceback
import requests
from bitfield import Bitfield


class Torrent:
    def __init__(self, name, location, client):
        self.bencoding = BEncoding()
        self.torrent_file = self.bencoding.decode_file(os.path.join(location, name))
        self.info_hash = self.get_info_hash()
        self.trackers = self.get_trackers()
        self.length = self.torrent_file['info']['length']
        self.name = self.torrent_file['info']['name']
        self.file = self.create_file()
        self.piece_length = self.torrent_file['info']['piece length']
        pieces = self.torrent_file['info']['pieces']
        pieces_len = len(pieces)
        self.pieces = [pieces[start:start+20]
                       for start in range(0, pieces_len, 20)]
        self.pieces_num = len(self.pieces)
        self.validate_piece_length()
        self.bitfield = self.create_bitfield()
        self.uploaded = 0
        self.downloaded = 0
        self.event = 'started'
        self.compact = '1'
        self.left = self.length
        self.client = client

    def is_completed(self):
        for piece_idx in range(self.pieces_num):
            if not self.bitfield.has_piece(piece_idx):
                return False
        return True

    def create_file(self):
        if not os.path.exists(self.name):
            fd = open(self.name, 'wb')
            fd.close()
        return open(self.name, 'rb+')

    def write_to_file(self, piece_idx, piece):
        self.file.seek(piece_idx*self.piece_length, 0)
        self.file.write(piece)

    def create_bitfield(self):
        bits = b'\x00' * (self.pieces_num // 8)
        if not self.pieces_num % 8 == 0:
            bits += b'\x00'
        return Bitfield(bits)

    def get_info_hash(self):
        info_hash = self.bencoding.encode(self.torrent_file['info'])
        hashing = hashlib.new('sha1', usedforsecurity=False)
        hashing.update(info_hash)
        return hashing.digest()

    def get_trackers(self):
        trackers = []
        announce = self.torrent_file.get('announce', [])
        if not announce:
            raise Exception("No trackers found in torrent")
        if announce.startswith(b'http'):
            trackers.append(announce)
        announce_list = self.torrent_file.get('announce-list', [])
        while announce_list:
            element = announce_list.pop()
            if isinstance(element, list):
                while element:
                    announce_list.append(element.pop())
            else:
                if element.startswith(b'http'):
                    trackers.append(element)
        if not trackers:
            raise Exception("No HTTP trackers found")
        return trackers

    def validate_piece_length(self):
        pieces_num = self.length // self.piece_length
        pieces_num += 0 if self.length % self.piece_length == 0 else 1
        if self.pieces_num == pieces_num:
            return True
        else:
            raise Exception('Not enough verification hashes for all pieces, torrent loading failed')

    def announce(self):
        trackers = self.trackers
        info_hash = self.info_hash
        peer_id = self.client.peer_id
        port = self.client.port
        uploaded = self.uploaded
        downloaded = self.downloaded
        left = self.left
        event = self.event
        compact = self.compact
        query_params = {
            'info_hash': info_hash,
            'peer_id': peer_id,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'event': event,
            'compact': compact
        }
        try:
            responses = []
            for tracker in trackers:
                response = requests.get(tracker, params=query_params)
                response = self.bencoding.decode(response.content)
                responses.append(response)
            return responses
        except Exception as e:
            print("Announce failed due to error :")
            traceback.print_exc()
            pass

    def get_peers_list(self, tracker_responses):
        peer_list = []
        for tracker_response in tracker_responses:
            peer_list.extend(self.get_peers(tracker_response))
        return peer_list

    def get_peers(self, tracker_response):
        peer_bytes = tracker_response['peers']
        peer_list = []
        for i in range(0, len(peer_bytes), 6):
            start = i
            end = i + 6
            peer = peer_bytes[start:end]
            first_4 = [str(byte) for byte in peer[:4]]
            ipaddr = '.'.join(first_4)
            port = int.from_bytes(peer[4::], "big")
            peer_list.append((ipaddr, port))
        return peer_list
