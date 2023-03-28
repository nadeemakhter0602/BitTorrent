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
        self.length = str(self.torrent_file['info']['length'])
