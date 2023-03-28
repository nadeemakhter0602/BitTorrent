from bencoding import BEncoding
import hashlib
import requests
import secrets
from peer import Peer
from torrent import Torrent


def announce(torrent, peer, uploaded, downloaded, left, event, compact):
    bencoding = BEncoding()
    trackers = torrent.torrent_file['announce']
    info_hash = torrent.info_hash
    query_params = {
        'info_hash': info_hash,
        'peer_id': peer.peer_id,
        'port': peer.port,
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


def get_peers(tracker_response):
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


if __name__ == '__main__':
    bencoding = BEncoding()
    peer = Peer('6881')
    torrent = Torrent('test.torrent', './')
    length = torrent.length
    event = 'started'
    compact = '1'
    uploaded = 0
    downloaded = 0
    tracker_response = announce(torrent,
                                peer,
                                uploaded,
                                downloaded,
                                length,
                                event,
                                compact)
    peer_list = get_peers(tracker_response)
    print(peer_list)
