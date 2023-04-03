import secrets
import multiprocessing
import threading
import time
import queue
from torrent import Torrent
from peer import Peer
from peer_connection import Connection

class Client:
    def __init__(self, port, torrent_name, torrent_location):
        self.peer_id = bytes.fromhex(secrets.token_hex(20))
        self.port = port
        self.q = multiprocessing.JoinableQueue(100)
        self.torrent = Torrent(torrent_name, torrent_location, self)
        self.p_lock = multiprocessing.Lock()
        self.t_lock = threading.Lock()
        self.max_connections = 5
        self.peers = []

    def set_peers(self):
        tracker_responses = self.torrent.announce()
        self.peers = self.torrent.get_peers_list(tracker_responses)

    def producer(self):
        while self.torrent.piece_idx < self.torrent.pieces_num :
            try:
                self.q.put(self.torrent.piece_idx)
                self.torrent.piece_idx += 1
            except queue.Full:
                pass

    def consumer(self):
        while True:
            try:
                piece_idx = self.q.get()
                if piece == "TERMINATE":
                    break
                self.process(piece_idx)
                self.q.task_done()
            except queue.Empty:
                pass

    def process(self, piece_idx):
        with self.t_lock:
            peer = self.peers.pop()
            peer = Peer(peer[1], peer[0])
            connection = Connection(self, peer, self.torrent)
