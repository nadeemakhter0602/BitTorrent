import argparse
from client import Client
from pathlib import Path
import os

current_path = path = Path(__file__).parent.absolute()
parser = argparse.ArgumentParser(
                    prog='Torrent Client',
                    description='Download torrents')

parser.add_argument('-f', '--filepath', help="Path to the .torrent file", type=str)
parser.add_argument('-p', '--port', help="Port number to run the service at", type=int, default=6881)
parser.add_argument('-t', '--threads', help="Number of threads to use", type=int, default=50)
parser.add_argument('-r', '--requests-per-peer', help="Piece requests to send for each peer", type=int, default=5)

args = parser.parse_args()

torrent_file = args.filepath
directory, filename = os.path.split(torrent_file)

if not directory:
    directory = current_path
if not filename:
    raise Exception("No file location available in path provided")

port = args.port
threads = args.threads
requests_per_peer = args.requests_per_peer

client = Client(port, filename, directory)
client.max_connections = threads
client.requests_per_peer = requests_per_peer
client.start_workers()
