# IE406 — LSB Steganography with Random Pixel Selection & Secret Key (Tkinter GUI)

## Features
- PNG/BMP RGB support (auto-convert to RGB).
- Randomized LSB embedding using PRNG seeded from passphrase (PBKDF2-HMAC-SHA256 + 16-byte salt).
- Header includes: MAGIC 'ST', version, salt length, payload length, CRC32, salt.
- Decode validates CRC; wrong passphrase -> CRC fail.
- Simple GUI with Encode/Decode tabs (Tkinter).
- PSNR after embedding.

## Install
```bash
python -m venv venv

# For Windows: 
venv\Scripts\activate
# For Linux/Mac: 
source venv/bin/activate

pip install -r source/requirements.txt
```

## Run
```bash
cd source
python -m app.main # to run the application
python -m tools.benchmark # to run the benchmark
```

## Notes
- Use PNG or BMP for cover image. JPEG will destroy LSBs.
- Capacity = floor(W * H * 3 / 8) - 28 (28 bytes header). GUI shows estimate.
- Keep payload smaller than capacity (recommend <= 80%).
