import os


class BEncoding:
    def __init__(self):
        self.dictionary_start = bytes('d', 'utf-8')
        self.list_start = bytes('l', 'utf-8')
        self.number_start = bytes('i', 'utf-8')
        self.end = bytes('e', 'utf-8')
        self.divider = bytes(':', 'utf-8')

    def decode_file(self, path):
        if not os.path.exists(path):
            raise Exception('Unable to find file :', path)

        with open(path, 'rb') as f:
            file_bytes = f.read()
            self.decode(file_bytes)

    def byte_generator(self, byte_array):
        for byte in byte_array:
            yield bytes(chr(byte), 'utf-8')

    def decode(self, byte_array):
        byte_data_generator = self.byte_generator(byte_array)
        return self.decode_byte_generator(byte_data_generator)

    def decode_byte_generator(self, byte_data_generator, current_byte = None):
        if current_byte is None:
            current_byte = next(byte_data_generator)
        else:
            current_byte = current_byte
        if current_byte == self.dictionary_start:
            return self.decode_dictionary(byte_data_generator)
        elif current_byte == self.number_start:
            return self.decode_number(byte_data_generator)
        elif current_byte == self.list_start:
            return self.decode_list(byte_data_generator)
        return self.decode_byte_array(byte_data_generator, current_byte)

    def decode_number(self, byte_data_generator):
        byte_array = bytes()
        current_byte = bytes()
        while current_byte != self.end:
            byte_array += current_byte
            current_byte = next(byte_data_generator)
        return int(byte_array)

    def decode_dictionary(self, byte_data_generator):
        dictionary = dict()
        keys = list()
        current_byte = bytes()
        while current_byte != self.end:
            key = self.decode_byte_generator(byte_data_generator, current_byte).decode()
            current_byte = next(byte_data_generator)
            value = self.decode_byte_generator(byte_data_generator, current_byte)
            current_byte = next(byte_data_generator)
            dictionary[key] = value
            keys.append(key)
        if sorted(keys, key = lambda x : bytes(x, 'utf-8')) != list(dictionary.keys()):
            raise Exception('Dictionary keys not sorted')
        return dictionary

    def decode_list(self, byte_data_generator):
        list_bytes = list()
        current_byte = bytes()
        while current_byte != self.end:
            if not current_byte == b'':
                byte_array = self.decode_byte_generator(
                    byte_data_generator, current_byte)
            else:
                byte_array = self.decode_byte_generator(byte_data_generator)
            current_byte = next(byte_data_generator)
            list_bytes.append(byte_array)
        return list_bytes

    def decode_byte_array(self, byte_data_generator, current_byte):
        byte_array = bytes()
        current_byte = current_byte
        while current_byte != self.divider:
            byte_array += current_byte
            current_byte = next(byte_data_generator)
        byte_length = int(byte_array)
        byte_array = bytes()
        for i in range(byte_length):
            byte_array += next(byte_data_generator)
        return byte_array

    def encode_to_file(self, decoded_object, path):
        if os.path.exists(path):
            raise Exception('File already exists :', path)

        with open(path, 'wb') as f:
            f.write(self.encode(decoded_object))

    def get_encoded_bytes(self, encoded_bytes, decoded_object):
        if isinstance(decoded_object, bytes):
            self.encode_byte_array(encoded_bytes, decoded_object)
        elif isinstance(decoded_object, str):
            self.encode_string(encoded_bytes, decoded_object)
        elif isinstance(decoded_object, int):
            self.encode_number(encoded_bytes, decoded_object)
        elif isinstance(decoded_object, list):
            self.encode_list(encoded_bytes, decoded_object)
        elif isinstance(decoded_object, dict):
            self.encode_dictionary(encoded_bytes, decoded_object)
        else:
            raise Exception('Unable to encode type', type(decoded_object))

    def encode(self, decoded_object):
        encoded_bytes = list()
        self.get_encoded_bytes(encoded_bytes, decoded_object)
        return b''.join(encoded_bytes)

    def encode_byte_array(self, encoded_bytes, decoded_object):
        encoded_bytes.append(bytes(str(len(decoded_object)), 'utf-8'))
        encoded_bytes.append(self.divider)
        encoded_bytes.append(decoded_object)

    def encode_string(self, encoded_bytes, decoded_object):
        self.encode_byte_array(encoded_bytes, bytes(decoded_object, 'utf-8'))

    def encode_number(self, encoded_bytes, decoded_object):
        encoded_bytes.append(self.number_start)
        encoded_bytes.append(bytes(str(decoded_object), 'utf-8'))
        encoded_bytes.append(self.end)

    def encode_list(self, encoded_bytes, decoded_object):
        encoded_bytes.append(self.list_start)
        for item in decoded_object:
            self.get_encoded_bytes(encoded_bytes, item)
        encoded_bytes.append(self.end)

    def encode_dictionary(self, encoded_bytes, decoded_object):
        encoded_bytes.append(self.dictionary_start)
        for key in decoded_object:
            value = decoded_object[key]
            self.encode_string(encoded_bytes, key)
            self.get_encoded_bytes(encoded_bytes, value)
        encoded_bytes.append(self.end)
