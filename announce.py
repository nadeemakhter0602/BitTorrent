from bencoding import BEncoding
import hashlib
import requests
import secrets


def announce(torrent_file, peer_id, port, uploaded, downloaded, left, event, compact):
    trackers = torrent_file['announce']
    info_hash = bencoding.encode(torrent_file['info'])
    hashing = hashlib.new('sha1', usedforsecurity=False)
    hashing.update(info_hash)
    digest = hashing.digest()
    query_params = {
        'info_hash': digest,
        'peer_id': peer_id,
        'port': port,
        'uploaded': uploaded,
        'downloaded': downloaded,
        'left': left,
        'event': event,
        'compact': compact
    }
    try:
        response = requests.get(trackers, params=query_params)
        return bencoding.decode(response.content)
    except Exception as e:
        print(str(e))

if __name__ == '__main__':
    peer_id = bytes.fromhex(secrets.token_hex(20))
    bencoding = BEncoding()
    torrent_file = bencoding.decode_file('test.torrent')
    length = str(torrent_file['info']['length'])
    event = 'started'
    port = '6881'
    compact = '1'
    uploaded = 0
    downloaded = 0

    tracker_response = announce(torrent_file, peer_id,
                                port, uploaded, downloaded, length, event, compact)
    peer_bytes = tracker_response['peers']
    peer_list = []
    for i in range(0, len(peer_bytes), 6):
        start = i
        end = i + 6
        peer = peer_bytes[start:end]
        first_4 = [byte for byte in peer[:4]]
        last_2 = int.from_bytes(peer[4::], "big")
        peer_list.append((first_4, last_2))
    print(peer_list)
