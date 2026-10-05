import unittest

from base32_zooko_encoder import (
    encode,
    decode,
    encode_bytes,
    decode_to_bytes,
    Z_BASE32_ALPHABET,
)


class TestAlphabet(unittest.TestCase):
    def test_alphabet_length(self):
        self.assertEqual(len(Z_BASE32_ALPHABET), 32)

    def test_alphabet_is_lowercase_only(self):
        self.assertEqual(Z_BASE32_ALPHABET, Z_BASE32_ALPHABET.lower())

    def test_alphabet_has_no_duplicates(self):
        self.assertEqual(len(set(Z_BASE32_ALPHABET)), len(Z_BASE32_ALPHABET))


class TestRoundTrip(unittest.TestCase):
    def test_empty_bytes(self):
        self.assertEqual(encode_bytes(b""), "")
        self.assertEqual(decode_to_bytes(""), b"")

    def test_empty_string(self):
        self.assertEqual(encode(""), "")
        self.assertEqual(decode(""), "")

    def test_single_byte(self):
        self.assertEqual(decode_to_bytes(encode_bytes(b"\x00")), b"\x00")
        self.assertEqual(decode_to_bytes(encode_bytes(b"\xff")), b"\xff")
        self.assertEqual(decode_to_bytes(encode_bytes(b"A")), b"A")

    def test_known_text_round_trip(self):
        for text in ["hello", "world", "The quick brown fox", "1234567890"]:
            self.assertEqual(decode(encode(text)), text)

    def test_binary_round_trip(self):
        data = bytes(range(256))
        self.assertEqual(decode_to_bytes(encode_bytes(data)), data)

    def test_long_randomish_bytes(self):
        # Deterministic pseudo-random data, no time or RNG dependency.
        data = bytes((i * 1103515245 + 12345) & 0xFF for i in range(1000))
        self.assertEqual(decode_to_bytes(encode_bytes(data)), data)


class TestKnownVectors(unittest.TestCase):
    """Vectors derived from the algorithm itself.

    These pin the exact output so that accidental alphabet or bit-order
    changes are caught immediately.
    """

    def test_zero_byte_encodes_to_yo(self):
        # 0x00 = 00000000 -> 00000 00000 -> indices 0,0 -> 'y','y', then
        # the encoder appends a final chunk for the remaining 0 bits? No:
        # 8 bits = one 5-bit chunk + 3 leftover bits, which become a second
        # character. So two characters total.
        self.assertEqual(encode_bytes(b"\x00"), "yy")

    def test_ff_byte(self):
        # 0xff = 11111111 -> 11111 111?? -> index 31 ('9') then 11100 ->
        # index 28 ('6').
        self.assertEqual(encode_bytes(b"\xff"), "9h")

    def test_foobar(self):
        self.assertEqual(encode_bytes(b"foobar"), "c3zs6aubqe")


class TestDecodeErrors(unittest.TestCase):
    def test_invalid_character_raises(self):
        with self.assertRaises(ValueError):
            decode_to_bytes("y9!z")

    def test_uppercase_rejected(self):
        # The alphabet is lowercase-only by design; uppercase is not accepted.
        with self.assertRaises(ValueError):
            decode_to_bytes("YY")

    def test_space_rejected(self):
        with self.assertRaises(ValueError):
            decode_to_bytes("yy yy")


class TestTypeChecking(unittest.TestCase):
    def test_encode_bytes_rejects_str(self):
        with self.assertRaises(TypeError):
            encode_bytes("not bytes")  # type: ignore[arg-type]

    def test_encode_rejects_bytes(self):
        with self.assertRaises(TypeError):
            encode(b"not str")  # type: ignore[arg-type]

    def test_decode_rejects_bytes(self):
        with self.assertRaises(TypeError):
            decode(b"yy")  # type: ignore[arg-type]


class TestPaddingBehaviour(unittest.TestCase):
    def test_trailing_bits_are_discarded(self):
        # A single zero byte encodes to 'yy'. The second character carries
        # 3 real bits and 2 zero padding bits. Decoding 'yy' must yield the
        # original single byte, proving padding is discarded correctly.
        self.assertEqual(decode_to_bytes("yy"), b"\x00")

    def test_extra_trailing_zero_bits_do_not_produce_extra_byte(self):
        # 'y' alone is 5 zero bits, which is fewer than 8, so it decodes to
        # zero bytes — the trailing bits are dropped.
        self.assertEqual(decode_to_bytes("y"), b"")


if __name__ == "__main__":
    unittest.main()
