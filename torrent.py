import hashlib
import os
from bencoding import BEncoding


class Torrent:
    def __init__(self, name, location):
        bencoding = BEncoding()
        self.torrent_file = bencoding.decode_file(os.path.join(location, name))
        info_hash = bencoding.encode(self.torrent_file['info'])
        hashing = hashlib.new('sha1', usedforsecurity=False)
        hashing.update(info_hash)
        self.info_hash = hashing.digest()
        self.length = self.torrent_file['info']['length']
        self.name = self.torrent_file['info']['name']
        self.piece_length = self.torrent_file['info']['piece length']
        pieces = self.torrent_file['info']['pieces']
        pieces_len = len(pieces)
        self.pieces = [pieces[start:start+20] for start in range(0, pieces_len, 20)]
