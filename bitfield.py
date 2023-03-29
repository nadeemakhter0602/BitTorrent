class Bitfield:
    def __init__(self, bits):
        self.bits = bits

    def has_piece(self, index):
        byte_index = index // 8
        offset = index % 8
        return self.bits[byte_index] >> (7 - offset) & 1 != 0

    def set_piece(self, index):
        byte_index = index // 8
        offset = index % 8
        self.bits[byte_index] |= 1 << (7 - offset)
