import unittest
from bencoding import BEncoding


class BEncodingTests(unittest.TestCase):
    def setUp(self):
        self.bencoding = BEncoding()

    def test_decoding_number(self):
        result = self.bencoding.decode(b'i123e')
        self.assertEqual(123, result)

    def test_decoding_bytes(self):
        result = self.bencoding.decode(b'12:Middle Earth')
        self.assertEqual(b'Middle Earth', result)

    def test_decoding_list_string(self):
        result = self.bencoding.decode(b'l4:spame')
        self.assertEqual(isinstance(result, list), True)
        self.assertEqual(result[0], b'spam')

    def test_decoding_list_integer(self):
        result = self.bencoding.decode(b'li123ee')
        self.assertEqual(isinstance(result, list), True)
        self.assertEqual(result[0], 123)

    def test_decoding_list(self):
        result = self.bencoding.decode(b'l4:spam4:eggsi123ee')
        self.assertEqual(isinstance(result, list), True)
        self.assertEqual(result, [b'spam', b'eggs', 123])

    def test_decoding_dictionary_string(self):
        result = self.bencoding.decode(b'd3:cow3:moo4:spam4:eggse')
        self.assertEqual(isinstance(result, dict), True)
        self.assertEqual(result, {'cow': b'moo', 'spam': b'eggs'})

    def test_decoding_dictionary_integer(self):
        result = self.bencoding.decode(b'd3:cow3:moo4:spam4:eggs5:teggsi123ee')
        self.assertEqual(isinstance(result, dict), True)
        self.assertEqual(result, {'cow': b'moo', 'spam': b'eggs', 'teggs': 123})

    def test_decoding_dictionary_nested(self):
        result = self.bencoding.decode(
            b'd1:ai123e1:bd2:ba3:foo2:bb3:bare1:cll1:a1:be1:zee')
        self.assertEqual(isinstance(result, dict), True)
        self.assertEqual(result, {'a': 123, 'b': {'ba': b'foo', 'bb': b'bar'}, 'c': [[b'a', b'b'], b'z']})

    def test_encoding_number(self):
        result = self.bencoding.encode(123)
        self.assertEqual(b'i123e', result)

    def test_encoding_bytes(self):
        result = self.bencoding.encode(b'Middle Earth')
        self.assertEqual(b'12:Middle Earth', result)

    def test_encoding_list_string(self):
        result = self.bencoding.encode([b'spam'])
        self.assertEqual(result, b'l4:spame')

    def test_encoding_list_integer(self):
        result = self.bencoding.encode([123])
        self.assertEqual(result, b'li123ee')

    def test_encoding_list(self):
        result = self.bencoding.encode([b'spam', b'eggs', 123])
        self.assertEqual(result, b'l4:spam4:eggsi123ee')

    def test_encoding_dictionary_string(self):
        result = self.bencoding.encode({'cow': b'moo', 'spam': b'eggs'})
        self.assertEqual(result, b'd3:cow3:moo4:spam4:eggse')

    def test_encoding_dictionary_integer(self):
        result = self.bencoding.encode({'cow': b'moo', 'spam': b'eggs', 'teggs': 123})
        self.assertEqual(result, b'd3:cow3:moo4:spam4:eggs5:teggsi123ee')

    def test_encoding_dictionary_nested(self):
        result = self.bencoding.encode({'a': 123, 'b': {'ba': b'foo', 'bb': b'bar'}, 'c': [[b'a', b'b'], b'z']})
        self.assertEqual(result, b'd1:ai123e1:bd2:ba3:foo2:bb3:bare1:cll1:a1:be1:zee')


if __name__ == '__main__':
    unittest.main()
