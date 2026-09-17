"""Reversible cluster masks and base-three pair discriminators."""

from io import BytesIO

from .core import CLUSTER_TABLE, signature


POWERS_OF_THREE = (1, 3, 9, 27, 81)
BYTE_RANKS = []
INVERSE = [[0] * (3 ** state.bit_count()) for state in range(16)]
for byte_value in range(256):
    byte_rank = 0
    for shift in (6, 4, 2, 0):
        pair = (byte_value >> shift) & 3
        if pair:
            byte_rank = byte_rank * 3 + pair - 1
    BYTE_RANKS.append(byte_rank)
    INVERSE[CLUSTER_TABLE[byte_value] - 1][byte_rank] = byte_value


def unsigned(value):
    if type(value) is not int or not 0 <= value < 2 ** 448:
        raise ValueError("unsigned value must fit 448 bits")
    encoded = bytearray()
    while value >= 128:
        encoded.append((value & 127) | 128)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def read_unsigned(stream):
    value = 0
    for position in range(64):
        chunk = stream.read(1)
        if not chunk:
            raise ValueError("truncated unsigned integer")
        byte_value = chunk[0]
        value |= (byte_value & 127) << (7 * position)
        if byte_value < 128:
            if position and byte_value == 0:
                raise ValueError("noncanonical unsigned integer")
            return value
    raise ValueError("unsigned integer exceeds 448 bits")


def encode_signature(values):
    return b"".join(unsigned(value) for value in values)


def decode_signature(payload):
    stream = BytesIO(payload)
    values = [read_unsigned(stream) for _ in range(5)]
    if stream.read(1):
        raise ValueError("trailing signature data")
    return values


def encode_micro(data):
    if not 1 <= len(data) <= 1024:
        raise ValueError("exact MICRO must contain 1..1024 bytes")
    packed_masks = bytearray((len(data) + 1) // 2)
    rank = 0
    active_count = 0
    for position, value in enumerate(data):
        state = CLUSTER_TABLE[value] - 1
        packed_masks[position // 2] |= state << (4 if position % 2 == 0 else 0)
        active = state.bit_count()
        rank = rank * POWERS_OF_THREE[active] + BYTE_RANKS[value]
        active_count += active
    rank_width = ((3 ** active_count - 1).bit_length() + 7) // 8
    math_state = signature(data)
    payload = encode_signature(math_state) + packed_masks + rank.to_bytes(rank_width, "big")
    return payload, math_state


def decode_micro(payload, expected_length):
    if not 1 <= expected_length <= 1024:
        raise ValueError("invalid exact MICRO length")
    stream = BytesIO(payload)
    math_state = [read_unsigned(stream) for _ in range(5)]
    if math_state[0] != expected_length:
        raise ValueError("MICRO length does not match hierarchy")
    packed_masks = stream.read((expected_length + 1) // 2)
    if len(packed_masks) != (expected_length + 1) // 2:
        raise ValueError("truncated cluster masks")
    if expected_length % 2 and packed_masks[-1] & 15:
        raise ValueError("nonzero mask padding")
    states = [(packed_masks[position // 2] >> (4 if position % 2 == 0 else 0)) & 15
              for position in range(expected_length)]
    active_count = sum(state.bit_count() for state in states)
    capacity = 3 ** active_count
    rank_width = ((capacity - 1).bit_length() + 7) // 8
    rank_bytes = stream.read()
    if len(rank_bytes) != rank_width:
        raise ValueError("invalid discriminator width")
    rank = int.from_bytes(rank_bytes, "big")
    if rank >= capacity:
        raise ValueError("discriminator out of range")
    decoded = bytearray(expected_length)
    for position in range(expected_length - 1, -1, -1):
        state = states[position]
        rank, byte_rank = divmod(rank, POWERS_OF_THREE[state.bit_count()])
        decoded[position] = INVERSE[state][byte_rank]
    data = bytes(decoded)
    if signature(data) != math_state:
        raise ValueError("MICRO signature mismatch")
    return data, math_state
