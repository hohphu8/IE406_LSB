import hashlib

SALT_LEN = 16
KDF_ITERS = 200_000

def kdf_seed(passphrase: str, salt: bytes, out_bytes: int = 16) -> bytes:
    """
    PBKDF2-HMAC-SHA256 -> seed bytes.
    """
    if isinstance(passphrase, str):
        passphrase = passphrase.encode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha256", passphrase, salt, KDF_ITERS, dklen=out_bytes)
    return dk

def crc32_bytes(data: bytes) -> int:
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF
