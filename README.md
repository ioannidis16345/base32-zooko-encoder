# base32-zooko-encoder

Encode and decode bytes using the Z-Base32 alphabet (Zooko's human-optimised base32).

```python
from base32_zooko_encoder import encode, decode, encode_bytes, decode_to_bytes

encoded = encode("hello")          # -> str
decoded = decode(encoded)           # -> "hello"
raw = encode_bytes(b"\x00\xff")    # -> str
data = decode_to_bytes(raw)         # -> b'\x00\xff'
```

## Why

Standard base32 (RFC 4648) uses an alphabet that produces strings people misread and mistype: `0` vs `O`, `1` vs `I` vs `l`, and characters that sound identical over a bad phone line. Z-Base32 permutes the alphabet to avoid these failure modes, which makes it a better choice when a human will transcribe the output — verification codes, shared secrets read aloud, that sort of thing.

The trade-off: it is not RFC 4648 base32. You cannot swap this in where a system already expects standard base32. This library exists for the case where human readability is the point.

## Edge cases

The input length in bits is rarely a multiple of 5, so the encoder's final character carries some zero padding bits. The decoder discards those trailing bits. This means `decode_to_bytes("y")` returns `b""` — a single `y` is 5 zero bits, which is fewer than 8, so nothing survives. This is correct and is the standard Z-Base32 behaviour, but it means the codec is not injective on strings of arbitrary trailing-bit patterns. If you need round-trip fidelity, encode bytes and decode the full string; do not truncate encoded strings.

The alphabet is lowercase only. Uppercase input is rejected on decode, not normalised, because accepting uppercase would reintroduce exactly the visual ambiguity the alphabet was designed to eliminate.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

