import secrets
import multiprocessing
import threading
import time
import os
import queue
import hashlib
from torrent import Torrent
from bitfield import Bitfield
from peer import Peer
import logging
from peer_connection import Connection

class Client:
    def __init__(self, port, torrent_name, torrent_location):
        self.peer_id = bytes.fromhex(secrets.token_hex(20))
        logging.basicConfig(filename="error.log",
                            format='%(asctime)s %(message)s',
                            filemode='a')
        self.logger = logging.getLogger()
        self.port = port
        self.q = multiprocessing.Queue(maxsize=100)
        self.torrent = Torrent(torrent_name, torrent_location, self)
        self.block_size = 2**17
        self.block_size_bytes = self.block_size.to_bytes(4, 'big')
        self.p_lock = multiprocessing.Lock()
        self.t_lock = threading.Lock()
        self.max_connections = 50
        self.requests_per_peer = 5
        self.peers = []

    def set_peers(self):
        tracker_responses = self.torrent.announce()
        self.peers = self.torrent.get_peers_list(tracker_responses)

    def download_piece(self, piece_idx, connection):
        try:
            piece = b''
            piece_offset = 0
            ipaddr, port = connection.peer.ipaddr, connection.peer.port
            while piece_offset < self.torrent.piece_length:
                connection.send_request(piece_idx, piece_offset, self.block_size)
                piece_offset += self.block_size
            while piece_offset > 0:
                length, msg_id, payload = connection.receive_message()
                if length == 0 and not msg_id:
                    continue
                elif msg_id == 7 and payload:
                    index = int.from_bytes(payload[:4], 'big')
                    begin = int.from_bytes(payload[4:8], 'big')
                    block = payload[8:]
                    piece += block
                    piece_offset -= self.block_size
                else:
                    return False
            if self.torrent.validate_piece(piece, piece_idx):
                with self.t_lock:
                    self.torrent.write_to_file(piece_idx, piece)
                    self.torrent.bitfield.set_piece(piece_idx)
                return True
            else:
                return False
        except TimeoutError:
            pass
        except ConnectionRefusedError:
            pass
        except Exception as err:
            self.logger.exception(err)
            return False

    def producer(self):
        piece_idx = 0
        while piece_idx < self.torrent.pieces_num :
            try:
                pieces_done = self.torrent.progress()
                if pieces_done == self.torrent.pieces_num:
                    break
                if not self.torrent.bitfield.has_piece(piece_idx):
                    self.q.put(piece_idx, block=False)
                piece_idx += 1
            except queue.Full:
                pass

    def consumer(self):
        while True:
            try:
                peer = tuple()
                pieces_done = self.torrent.progress()
                status = (pieces_done / self.torrent.pieces_num) * 100
                size = (os.get_terminal_size().columns * 50) // 100
                scale = int((size * status)/100)
                status = "%.2f" % status
                print("{}[{}{}] {}/{}".format("Downloading ", u"█"*scale, "."*(size - scale), status, 100), end='\r', flush=True)
                if pieces_done == self.torrent.pieces_num:
                    break
                with self.t_lock:
                    if not self.peers:
                        self.set_peers()
                    peer = self.peers.pop()
                peer = Peer(peer[1], peer[0])
                connection = Connection(self, peer, self.torrent)
                connection.connect_peer()
                connection.send_handshake()
                payload = connection.receive_bitfield()
                bitfield = Bitfield(payload)
                connection.am_choking = False
                connection.send_unchoke()
                connection.am_interested = True
                connection.send_interested()
                for i in range(self.requests_per_peer):
                    while True:
                        try:
                            piece_idx = self.q.get(block=False)
                            result = self.process(piece_idx, connection, bitfield)
                            if not result:
                                self.q.put(piece_idx, block=False)
                            break
                        except queue.Empty:
                            pass
                        except queue.Full:
                            pass
                connection.close_connection()
            except TimeoutError:
                pass
            except ConnectionRefusedError:
                pass
            except Exception as err:
                self.logger.exception(err)
                pass

    def process(self, piece_idx, connection, bitfield):
        try:
            length, msg_id, payload = connection.receive_message()
            if msg_id == 1 and bitfield.has_piece(piece_idx):
                connection.peer_choking = False
                connection.peer_interested = True
                return self.download_piece(piece_idx, connection)
        except TimeoutError:
            pass
        except ConnectionRefusedError:
            pass
        except Exception as err:
            self.logger.exception(err)
            return False
        return False

    def start_workers(self):
        consumers = []
        for i in range(self.max_connections): 
            consumer = threading.Thread(target=self.consumer)
            consumer.start()
            consumers.append(consumer)
        self.producer()
        for consumer in consumers:
            consumer.join()
            consumer.is_alive()
        print()
        print("Finished.")
