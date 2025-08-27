from dataclasses import dataclass
import numpy as np
from PIL import Image
from .crypto_utils import SALT_LEN, crc32_bytes
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
    return np.unpackbits(arr)

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

def capacity_bytes_for_image(path: str) -> int:
    img = _open_rgb(path)
    w, h = img.size
    total_slots = w * h * 3
    return max(0, (total_slots // 8) - HEADER_FIXED_LEN)

def _build_header(payload: bytes, salt: bytes) -> bytes:
    payload_len = len(payload)
    crc = crc32_bytes(payload)
    header = bytearray()
    header += b"ST"
    header += bytes([ALG_VER])
    header += bytes([SALT_LEN])
    header += payload_len.to_bytes(4, "big")
    header += crc.to_bytes(4, "big")
    header += salt
    return bytes(header)

def _parse_header(header_bytes: bytes):
    magic = header_bytes[0:2]
    ver = header_bytes[2]
    salt_len = header_bytes[3]
    payload_len = int.from_bytes(header_bytes[4:8], "big")
    crc = int.from_bytes(header_bytes[8:12], "big")
    salt = header_bytes[12:12+salt_len]
    return magic, ver, salt_len, payload_len, crc, salt

def encode_sequential(cover_path: str, payload_path: str, out_path: str) -> EncodeResult:
    cover_img = _open_rgb(cover_path)
    arr = _img_to_array(cover_img)
    H, W, C = arr.shape
    assert C == 3

    with open(payload_path, "rb") as f:
        payload = f.read()

    total_slots = H * W * 3
    cap_bytes = (total_slots // 8) - HEADER_FIXED_LEN
    if len(payload) > cap_bytes:
        raise ValueError(f"Payload too large. Capacity ~{cap_bytes} bytes (excludes 28B header).")

    salt = bytes([0]*SALT_LEN)  # sequential variant uses fixed zero salt (no key)
    header = _build_header(payload, salt)
    stream = header + payload
    bits = _to_bits(stream)

    flat = arr.reshape(-1)
    flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | bits

    from PIL import Image as _I
    _I.fromarray(flat.reshape(H, W, C), "RGB").save(out_path, format="PNG")
    return EncodeResult(out_path, cap_bytes, len(stream), float(psnr(arr, flat.reshape(H, W, C))))

def decode_sequential(stego_path: str, out_dir: str) -> DecodeResult:
    img = _open_rgb(stego_path)
    arr = _img_to_array(img)
    H, W, C = arr.shape
    flat = arr.reshape(-1)

    header_bits_len = HEADER_FIXED_LEN * 8
    header_bits = flat[:header_bits_len] & 1
    header = _bits_to_bytes(header_bits.astype(np.uint8))

    magic, ver, salt_len, payload_len, crc, salt = _parse_header(header)
    if magic != b"ST" or ver != 1:
        raise ValueError("Invalid header.")

    payload_bits = flat[header_bits_len:header_bits_len + payload_len*8] & 1
    payload = _bits_to_bytes(payload_bits.astype(np.uint8))

    import os
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "extracted_payload_seq.bin")
    with open(out_path, "wb") as f:
        f.write(payload)

    crc_ok = (crc32_bytes(payload) == crc)
    return DecodeResult(out_path, payload_len, crc_ok)
