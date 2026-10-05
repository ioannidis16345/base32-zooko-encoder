"""Z-Base32 encoding and decoding.

Z-Base32 (designed by Zooko) uses an alphabet chosen so that the resulting
strings are easy for humans to read, dictate, and type. The characters are
selected to avoid visually ambiguous pairs and to be phonetically distinct
over noisy voice channels.

This implementation is a straightforward bit-packing codec: input bytes are
treated as a big-endian bit stream, grouped into 5-bit chunks, and each chunk
indexes into the Z-Base32 alphabet. Decoding is the inverse. No padding
characters are appended; instead the bit stream is truncated to the original
byte length on decode, which is the standard Z-Base32 convention.
"""

from __future__ import annotations

# The Z-Base32 alphabet, as specified by Zooko's original proposal.
# Order matters: the index of a character in this string is its 5-bit value.
# The alphabet is deliberately permuted relative to RFC 4648 base32 so that
# common bit patterns map to characters that are visually and phonetically
# distinct from one another.
Z_BASE32_ALPHABET: str = "ybndrfg8ejkmcpqxot1uwisza345h769"

# Precomputed reverse lookup so decode is O(n) with a single dict access per
# character. Lowercase keys only; the alphabet has no uppercase letters.
_DECODE_TABLE: dict[str, int] = {ch: i for i, ch in enumerate(Z_BASE32_ALPHABET)}


def encode_bytes(data: bytes) -> str:
    """Encode raw bytes into a Z-Base32 string.

    The output contains no padding. The number of output characters is
    ``ceil(len(data) * 8 / 5)``. Because 8 is not a multiple of 5, the final
    character may encode fewer than 5 input bits; that is fine because the
    decoder knows the original byte length is not carried in the string and
    callers must supply it implicitly (see :func:`decode_to_bytes`).

    Args:
        data: The bytes to encode.

    Returns:
        The Z-Base32 encoded string.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"expected bytes or bytearray, got {type(data).__name__}")

    if len(data) == 0:
        return ""

    alphabet = Z_BASE32_ALPHABET
    out_chars: list[str] = []
    buffer = 0
    bits_in_buffer = 0

    for byte in data:
        buffer = (buffer << 8) | byte
        bits_in_buffer += 8
        while bits_in_buffer >= 5:
            bits_in_buffer -= 5
            # Extract the top 5 bits of the current buffer.
            index = (buffer >> bits_in_buffer) & 0x1F
            out_chars.append(alphabet[index])
        # Keep only the remaining low bits to avoid unbounded growth.
        buffer &= (1 << bits_in_buffer) - 1

    if bits_in_buffer > 0:
        # Left-shift the remaining bits into the high part of a 5-bit chunk.
        # The low bits are implicitly zero; the decoder discards them.
        out_chars.append(alphabet[buffer << (5 - bits_in_buffer)])

    return "".join(out_chars)


def encode(data: str) -> str:
    """Encode a UTF-8 string into Z-Base32.

    This is a convenience wrapper around :func:`encode_bytes` for the common
    case where the input is text rather than raw bytes.
    """
    if not isinstance(data, str):
        raise TypeError(f"expected str, got {type(data).__name__}")
    return encode_bytes(data.encode("utf-8"))


def decode_to_bytes(encoded: str) -> bytes:
    """Decode a Z-Base32 string back to bytes.

    The input is case-sensitive: only lowercase characters from the Z-Base32
    alphabet are accepted. This matches the original specification, which
    defines the alphabet in lowercase. Accepting uppercase would introduce
    ambiguity (e.g. between visually similar glyphs) that the alphabet was
    specifically designed to avoid.

    Trailing bits that do not fill a complete byte are discarded. This is the
    inverse of the encoder's behaviour when the input length is not a multiple
    of 5 bits.

    Args:
        encoded: The Z-Base32 string to decode.

    Returns:
        The decoded bytes.

    Raises:
        ValueError: If the string contains a character outside the alphabet.
    """
    if not isinstance(encoded, str):
        raise TypeError(f"expected str, got {type(encoded).__name__}")

    if len(encoded) == 0:
        return b""

    out_bytes = bytearray()
    buffer = 0
    bits_in_buffer = 0

    for ch in encoded:
        value = _DECODE_TABLE.get(ch)
        if value is None:
            raise ValueError(
                f"invalid character {ch!r} at position {len(out_bytes) * 8 // 5 + bits_in_buffer // 5}"
            )
        buffer = (buffer << 5) | value
        bits_in_buffer += 5
        while bits_in_buffer >= 8:
            bits_in_buffer -= 8
            out_bytes.append((buffer >> bits_in_buffer) & 0xFF)
        buffer &= (1 << bits_in_buffer) - 1

    # Any remaining bits (fewer than 8) are padding introduced by the encoder
    # and are intentionally discarded.
    return bytes(out_bytes)


def decode(encoded: str) -> str:
    """Decode a Z-Base32 string to a UTF-8 text string.

    Convenience wrapper around :func:`decode_to_bytes`. Use
    :func:`decode_to_bytes` directly if the original data was not UTF-8 text.
    """
    return decode_to_bytes(encoded).decode("utf-8")
