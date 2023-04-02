from bencoding import BEncoding
import traceback
import requests

def announce(torrent, client, uploaded, downloaded, left, event, compact):
    bencoding = BEncoding()
    trackers = torrent.trackers
    info_hash = torrent.info_hash
    query_params = {
        'info_hash': info_hash,
        'peer_id': client.peer_id,
        'port': client.port,
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
                response = bencoding.decode(response.content)
                responses.append(response)
        else:
            response = requests.get(trackers, params=query_params)
            response =  bencoding.decode(response.content)
            responses.append(response)
        return responses
    except Exception as e:
        print("Announce failed due to error :")
        traceback.print_exc()
        pass

def get_peers_list(tracker_responses):
    peer_list = []
    for tracker_response in tracker_responses:
        peer_list.extend(get_peers(tracker_response))
    return peer_list

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
