from dataclasses import dataclass
import os
import numpy as np
from PIL import Image

from .crypto_utils import SALT_LEN, kdf_seed, crc32_bytes
from .metrics import psnr

MAGIC = b"ST"
ALG_VER = 1
HEADER_FIXED_LEN = 2 + 1 + 1 + 4 + 4 + SALT_LEN  # 28 bytes

@dataclass
class EncodeResult:
    stego_path: str
    capacity_bytes: int
    used_bytes: int
    psnr_db: float

@dataclass
class DecodeResult:
    output_path: str
    payload_len: int
    crc_ok: bool

def _to_bits(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    bits = np.unpackbits(arr)
    return bits

def _bits_to_bytes(bits: np.ndarray) -> bytes:
    if len(bits) % 8 != 0:
        pad = 8 - (len(bits) % 8)
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    arr = np.packbits(bits)
    return arr.tobytes()

def _open_rgb(path: str) -> Image.Image:
    img = Image.open(path)
    return img.convert("RGB")

def _img_to_array(img: Image.Image) -> np.ndarray:
    return np.array(img, dtype=np.uint8)

def _array_to_img(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(arr, mode="RGB")

def _rng_from_seed(seed_bytes: bytes) -> np.random.Generator:
    if len(seed_bytes) < 16:
        seed_bytes = seed_bytes.ljust(16, b"\x00")
    s0 = int.from_bytes(seed_bytes[:8], "little")
    s1 = int.from_bytes(seed_bytes[8:16], "little")
    bitgen = np.random.PCG64(seed=(s0, s1))
    return np.random.Generator(bitgen)

def capacity_bytes_for_image(path: str) -> int:
    img = _open_rgb(path)
    w, h = img.size
    total_slots = w * h * 3  # 1 bit per channel
    cap_bytes = (total_slots // 8) - HEADER_FIXED_LEN
    return max(0, cap_bytes)

def _build_header(payload: bytes, salt: bytes) -> bytes:
    payload_len = len(payload)
    crc = crc32_bytes(payload)
    header = bytearray()
    header += b"ST"                          # 2B
    header += bytes([ALG_VER])               # 1B
    header += bytes([SALT_LEN])              # 1B
    header += payload_len.to_bytes(4, "big") # 4B
    header += crc.to_bytes(4, "big")         # 4B
    header += salt                           # 16B
    return bytes(header)

def _parse_header(header_bytes: bytes):
    magic = header_bytes[0:2]
    ver = header_bytes[2]
    salt_len = header_bytes[3]
    payload_len = int.from_bytes(header_bytes[4:8], "big")
    crc = int.from_bytes(header_bytes[8:12], "big")
    salt = header_bytes[12:12+salt_len]
    return magic, ver, salt_len, payload_len, crc, salt

def _lsb_embed_at_indices(flat, bit_indices, bits):
    flat[bit_indices] = (flat[bit_indices] & 0xFE) | bits

def _lsb_read_at_indices(flat, bit_indices):
    return flat[bit_indices] & 1

def encode_v2(cover_path: str, payload_path: str, passphrase: str, out_path: str) -> EncodeResult:
    cover_img = _open_rgb(cover_path)
    arr = _img_to_array(cover_img)
    H, W, C = arr.shape
    assert C == 3

    with open(payload_path, "rb") as f:
        payload = f.read()

    total_slots = H * W * C
    flat = arr.reshape(-1)

    salt = os.urandom(SALT_LEN)
    header = _build_header(payload, salt)
    header_bits = _to_bits(header)

    cap_bytes = (total_slots // 8) - len(header)
    if len(payload) > cap_bytes:
        raise ValueError(f"Payload too large. Capacity ~{cap_bytes} bytes (excludes 28B header).")

    # Stage 1: header sequential at the beginning
    header_bit_indices = np.arange(len(header_bits), dtype=np.int64)
    _lsb_embed_at_indices(flat, header_bit_indices, header_bits)

    # Stage 2: payload randomized after header region
    payload_bits = _to_bits(payload)
    remaining_slots = np.arange(len(flat), dtype=np.int64)[len(header_bits):]
    seed = kdf_seed(passphrase, salt, out_bytes=16)
    rng = _rng_from_seed(seed)
    rng.shuffle(remaining_slots)
    payload_bit_indices = remaining_slots[:len(payload_bits)]
    _lsb_embed_at_indices(flat, payload_bit_indices, payload_bits)

    stego_arr = flat.reshape(H, W, C)
    p = psnr(arr, stego_arr)
    Image.fromarray(stego_arr, "RGB").save(out_path, format="PNG")

    used_bytes = len(header) + len(payload)
    return EncodeResult(stego_path=out_path, capacity_bytes=cap_bytes, used_bytes=used_bytes, psnr_db=float(p))

def decode_v2(stego_path: str, passphrase: str, out_dir: str) -> DecodeResult:
    stego_img = _open_rgb(stego_path)
    arr = _img_to_array(stego_img)
    H, W, C = arr.shape
    assert C == 3

    flat = arr.reshape(-1)

    # Stage 1: read header sequentially
    header_bits_len = (2 + 1 + 1 + 4 + 4 + 16) * 8
    header_bit_indices = np.arange(header_bits_len, dtype=np.int64)
    header_bits = _lsb_read_at_indices(flat, header_bit_indices).astype(np.uint8)
    header = _bits_to_bytes(header_bits)

    magic, ver, salt_len, payload_len, crc, salt = _parse_header(header)
    if magic != b"ST":
        raise ValueError("Not a valid stego image (MAGIC mismatch).")
    if ver != 1 or salt_len != 16:
        raise ValueError("Unsupported version or salt length.")

    # Stage 2: read payload with PRNG
    seed = kdf_seed(passphrase, salt, out_bytes=16)
    rng = _rng_from_seed(seed)

    remaining_slots = np.arange(len(flat), dtype=np.int64)[header_bits_len:]
    rng.shuffle(remaining_slots)

    payload_bits = _lsb_read_at_indices(flat, remaining_slots[:payload_len * 8]).astype(np.uint8)
    payload = _bits_to_bytes(payload_bits)

    calc_crc = crc32_bytes(payload)
    crc_ok = (calc_crc == crc)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "extracted_payload.bin")
    with open(out_path, "wb") as f:
        f.write(payload)

    from dataclasses import dataclass
    return DecodeResult(output_path=out_path, payload_len=payload_len, crc_ok=crc_ok)
