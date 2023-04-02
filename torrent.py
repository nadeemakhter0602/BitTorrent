import hashlib
import os
from bencoding import BEncoding
import traceback
import requests


class Torrent:
    def __init__(self, name, location, client):
        self.bencoding = BEncoding()
        self.torrent_file = self.bencoding.decode_file(os.path.join(location, name))
        info_hash = self.bencoding.encode(self.torrent_file['info'])
        hashing = hashlib.new('sha1', usedforsecurity=False)
        hashing.update(info_hash)
        self.info_hash = hashing.digest()
        self.trackers = self.torrent_file['announce']
        self.length = self.torrent_file['info']['length']
        self.name = self.torrent_file['info']['name']
        self.piece_length = self.torrent_file['info']['piece length']
        pieces = self.torrent_file['info']['pieces']
        pieces_len = len(pieces)
        self.pieces = [pieces[start:start+20]
                       for start in range(0, pieces_len, 20)]
        self.uploaded = 0
        self.downloaded = 0
        self.event = 'started'
        self.compact = '1'
        self.left = self.length
        self.client = client

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
            if isinstance(trackers, list):
                for tracker in trackers:
                    response = requests.get(tracker, params=query_params)
                    response = self.bencoding.decode(response.content)
                    responses.append(response)
            else:
                response = requests.get(trackers, params=query_params)
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
