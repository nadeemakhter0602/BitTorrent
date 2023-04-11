# BitTorrent

Implementation of certain parts of the BitTorrent Protocol Specification v1.

* Implemented [BEncode](https://en.wikipedia.org/wiki/Bencode) parsing, encoding and decoding of .torrent files and BEncoded data with unit tests.
* Implemented [Announce request](https://wiki.vuze.com/w/Announce) to [Trackers](https://en.wikipedia.org/wiki/BitTorrent_tracker) and retrieving [Peer](https://en.wikipedia.org/wiki/Glossary_of_BitTorrent_terms#Peer) List.
* Implemented [Peer wire protocol](https://wiki.theory.org/BitTorrentSpecification#Peer_wire_protocol_.28TCP.29).
* Implemented [Bitfield](https://en.wikipedia.org/wiki/Bit_field) Data Structure.
* Implemented Download Client.

```
$ python main.py -h
usage: Torrent Client [-h] [-f FILEPATH] [-p PORT] [-t THREADS] [-r REQUESTS_PER_PEER]

Download torrents

options:
  -h, --help            show this help message and exit
  -f FILEPATH, --filepath FILEPATH
                        Path to the .torrent file
  -p PORT, --port PORT  Port number to run the service at
  -t THREADS, --threads THREADS
                        Number of threads to use
  -r REQUESTS_PER_PEER, --requests-per-peer REQUESTS_PER_PEER
                        Piece requests to send for each peer

```
