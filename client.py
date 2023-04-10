import secrets
import threading
import time
import queue
import logging
from torrent import Torrent
from bitfield import Bitfield
from peer import Peer
from peer_connection import Connection


class Client:
    def __init__(self, port, torrent_name, torrent_location):
        self.peer_id = bytes.fromhex(secrets.token_hex(20))
        logging.basicConfig(filename="error.log",
                            format='%(asctime)s %(message)s',
                            filemode='w')
        self.logger = logging.getLogger()
        self.port = port
        self.q = queue.Queue(maxsize=1000)
        self.torrent = Torrent(torrent_name, torrent_location, self)
        self.block_size = 2**14
        self.block_size_bytes = self.block_size.to_bytes(4, 'big')
        self.t_lock = threading.Lock()
        self.max_connections = 1
        self.requests_per_peer = 1
        self.peers = []

    def set_peers(self):
        tracker_responses = self.torrent.announce()
        self.peers = self.torrent.get_peers_list(tracker_responses)

    def download_piece(self, piece_idx, connection):
        try:
            piece_offset = 0
            # piece length will be different for last piece
            offset_bound = self.torrent.piece_length
            if piece_idx == self.torrent.pieces_num - 1:
                offset_bound = self.torrent.last_piece_length
            piece = bytearray(b'\x00' * offset_bound)
            block_size = self.block_size
            ipaddr, port = connection.peer.ipaddr, connection.peer.port
            pieces_done, status = self.torrent.progress()
            print("[%.2f/100] Downloading piece #%d from %s:%d" % (status, piece_idx, ipaddr, port))
            # send multiple requests for all offsets of a piece
            while piece_offset < offset_bound:
                # handle last block of last piece
                if offset_bound == self.torrent.last_piece_length \
                    and self.torrent.last_piece_length - piece_offset < self.block_size:
                    block_size = self.torrent.last_piece_length - piece_offset
                connection.send_request(piece_idx, piece_offset, block_size)
                piece_offset += block_size
            # receive all piece messages
            while piece_offset > 0:
                length, msg_id, payload = connection.receive_message()
                if length == 0 and msg_id is None:
                    continue
                elif msg_id == 7 and payload is not None:
                    index = int.from_bytes(payload[:4], 'big')
                    begin = int.from_bytes(payload[4:8], 'big')
                    block = payload[8:]
                    # assemble piece
                    piece[begin:begin+len(block)] = block
                    piece_offset -= self.block_size
            piece = bytes(piece)
            # validate piece integrity
            if self.torrent.validate_piece(piece, piece_idx):
                pieces_done, status = self.torrent.progress()
                if pieces_done == self.torrent.pieces_num:
                    return
                # acquire lock before writing to field and updating bitfield
                with self.t_lock:
                    self.torrent.write_to_file(piece_idx, piece)
                    self.torrent.bitfield.set_piece(piece_idx)
                pieces_done, status = self.torrent.progress()
                print("[%.2f/100] Piece #%d downloaded" % (status, piece_idx))
            else:
                pieces_done, status = self.torrent.progress()
                print("[%.2f/100] Piece #%d integrity check failed" % (status, piece_idx))
        except Exception as err:
            self.logger.exception(err)

    def producer(self):
        while True:
            piece_idx = 0
            while piece_idx < self.torrent.pieces_num :
                pieces_done, status = self.torrent.progress()
                if pieces_done == self.torrent.pieces_num:
                    return
                if not self.torrent.bitfield.has_piece(piece_idx):
                    self.q.put(piece_idx)
                piece_idx += 1

    def consumer(self):
        while True:
            try:
                peer = tuple()
                pieces_done, status = self.torrent.progress()
                if pieces_done == self.torrent.pieces_num:
                    return
                with self.t_lock:
                    if not self.peers:
                        self.set_peers()
                peer = self.peers.pop()
                peer = Peer(peer[1], peer[0])
                connection = Connection(self, peer, self.torrent)
                connection.conn.settimeout(5)
                pieces_done, status = self.torrent.progress()
                print("[%.2f/100] Connecting to %s:%d" % (status, peer.ipaddr, peer.port))
                connection.connect_peer()
                pieces_done, status = self.torrent.progress()
                print("[%.2f/100] Connected to %s:%d" % (status, peer.ipaddr, peer.port))
                connection.send_handshake()
                payload = connection.receive_bitfield()
                bitfield = Bitfield(payload)
                for i in range(self.requests_per_peer):
                    pieces_done, status = self.torrent.progress()
                    if pieces_done == self.torrent.pieces_num:
                        return
                    piece_idx = self.q.get()
                    if bitfield.has_piece(piece_idx) and not self.torrent.bitfield.has_piece(piece_idx):
                        connection.am_choking = False
                        connection.send_unchoke()
                        connection.am_interested = True
                        connection.send_interested()
                        self.process(piece_idx, connection, bitfield)
                connection.close_connection()
            except Exception as err:
                self.logger.exception(err)
                pass

    def process(self, piece_idx, connection, bitfield):
        try:
            length, msg_id, payload = connection.receive_message()
            if msg_id == 1:
                connection.peer_choking = False
                connection.peer_interested = True
                self.download_piece(piece_idx, connection)
        except Exception as err:
            self.logger.exception(err)

    def start_workers(self):
        start = time.time()
        consumers = []
        for i in range(self.max_connections): 
            consumer = threading.Thread(target=self.consumer)
            consumer.start()
            consumers.append(consumer)
        self.producer()
        for consumer in consumers:
            if consumer.is_alive():
                consumer.join()
        print("Download completed in %s seconds." % (time.time() - start))
