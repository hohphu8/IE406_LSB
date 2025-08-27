import os, time, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

from app.core.lsb_random_v2 import capacity_bytes_for_image as cap_random, encode_v2 as encode_random, decode_v2 as decode_random
from app.core.lsb_sequential import capacity_bytes_for_image as cap_seq, encode_sequential, decode_sequential

def gen_cover_images(base_dir: Path):
    base_dir.mkdir(parents=True, exist_ok=True)
    covers = []

    # Gradient 512x512
    w, h = 512, 512
    x = np.linspace(0, 255, w, dtype=np.uint8)
    grad = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        grad[y, :, 0] = x
        grad[y, :, 1] = y % 256
        grad[y, :, 2] = (y//2) % 256
    p1 = base_dir / "cover_gradient_512.png"
    Image.fromarray(grad).save(p1); covers.append(p1)

    # Checkerboard 512x512
    tile = 32
    cb = np.zeros((h, w, 3), dtype=np.uint8)
    for yy in range(h):
        for xx in range(w):
            val = 255 if ((xx//tile + yy//tile) % 2 == 0) else 0
            cb[yy, xx] = [val, 255-val, (xx*3 + yy*2) % 256]
    p2 = base_dir / "cover_checker_512.png"
    Image.fromarray(cb).save(p2); covers.append(p2)

    # Noise 1024x768
    w2, h2 = 1024, 768
    noise = np.random.default_rng(0).integers(0, 256, size=(h2, w2, 3), dtype=np.uint8)
    p3 = base_dir / "cover_noise_1024x768.png"
    Image.fromarray(noise).save(p3); covers.append(p3)

    return covers

def lsb_plane_image(img_path: Path, out_path: Path):
    arr = np.array(Image.open(img_path).convert("RGB"), dtype=np.uint8)
    bits = arr & 1
    plane = (bits.sum(axis=2) * 85).clip(0,255).astype(np.uint8)
    Image.fromarray(plane).save(out_path)

def run_benchmark(out_dir: Path, passphrase: str = "ie406-demo"):
    out_dir.mkdir(parents=True, exist_ok=True)
    covers_dir = out_dir / "covers_gen"
    stego_dir = out_dir / "stego"
    stego_dir.mkdir(exist_ok=True, parents=True)
    covers = gen_cover_images(covers_dir)

    rows = []
    rng = np.random.default_rng(42)

    for cover in covers:
        cap = cap_random(str(cover))
        sizes = [max(1024, int(cap * r)) for r in [0.1, 0.3, 0.5, 0.8] if int(cap * r) > 0]

        for size in sizes:
            payload = rng.integers(0, 256, size=size, dtype=np.uint8).tobytes()
            tmp_payload = out_dir / f"payload_{cover.stem}_{size}.bin"
            with open(tmp_payload, "wb") as f:
                f.write(payload)

            # Sequential
            out_seq = stego_dir / f"{cover.stem}_seq_{size}.png"
            t0 = time.perf_counter()
            enc_seq = encode_sequential(str(cover), str(tmp_payload), str(out_seq))
            t1 = time.perf_counter()

            t2 = time.perf_counter()
            dec_seq = decode_sequential(str(out_seq), str(out_dir))
            t3 = time.perf_counter()

            rows.append({
                "cover": cover.name, "size": str(Image.open(cover).size),
                "method": "sequential",
                "payload_bytes": size,
                "percent_capacity": round(100*size/max(1, enc_seq.capacity_bytes),2),
                "psnr_db": enc_seq.psnr_db,
                "encode_ms": round((t1-t0)*1000,2),
                "decode_ms": round((t3-t2)*1000,2),
                "crc_ok": dec_seq.crc_ok
            })

            # Random
            out_rand = stego_dir / f"{cover.stem}_rand_{size}.png"
            t0 = time.perf_counter()
            enc_rand = encode_random(str(cover), str(tmp_payload), passphrase, str(out_rand))
            t1 = time.perf_counter()

            t2 = time.perf_counter()
            dec_rand = decode_random(str(out_rand), passphrase, str(out_dir))
            t3 = time.perf_counter()

            rows.append({
                "cover": cover.name, "size": str(Image.open(cover).size),
                "method": "random",
                "payload_bytes": size,
                "percent_capacity": round(100*size/max(1, enc_rand.capacity_bytes),2),
                "psnr_db": enc_rand.psnr_db,
                "encode_ms": round((t1-t0)*1000,2),
                "decode_ms": round((t3-t2)*1000,2),
                "crc_ok": dec_rand.crc_ok
            })

            # LSB-plane for mid size
            mid = sizes[len(sizes)//2]
            if size == mid:
                lsb_plane_image(out_seq, out_dir / f"{cover.stem}_lsbplane_seq.png")
                lsb_plane_image(out_rand, out_dir / f"{cover.stem}_lsbplane_rand.png")

            try: os.remove(tmp_payload)
            except: pass

    # DataFrame & CSV
    df = pd.DataFrame(rows)
    csv_path = out_dir / "benchmark_results.csv"
    df.to_csv(csv_path, index=False)

    # Charts for first cover
    first = covers[0].name
    sub = df[df["cover"] == first]

    # PSNR vs capacity
    fig1 = plt.figure()
    for m in ["sequential", "random"]:
        d = sub[sub["method"] == m].sort_values("percent_capacity")
        plt.plot(d["percent_capacity"], d["psnr_db"], marker="o", label=m)
    plt.xlabel("% capacity used")
    plt.ylabel("PSNR (dB)")
    plt.title(f"PSNR vs capacity — {first}")
    plt.legend()
    fig1_path = out_dir / "psnr_vs_capacity.png"
    plt.savefig(fig1_path, bbox_inches="tight")
    plt.close(fig1)

    # Encode time vs payload
    fig2 = plt.figure()
    for m in ["sequential", "random"]:
        d = sub[sub["method"] == m].sort_values("payload_bytes")
        plt.plot(d["payload_bytes"], d["encode_ms"], marker="o", label=m)
    plt.xlabel("Payload size (bytes)")
    plt.ylabel("Encode time (ms)")
    plt.title(f"Encode time vs payload — {first}")
    plt.legend()
    fig2_path = out_dir / "encode_time_vs_payload.png"
    plt.savefig(fig2_path, bbox_inches="tight")
    plt.close(fig2)

    return {
        "csv": str(csv_path),
        "psnr_plot": str(fig1_path),
        "time_plot": str(fig2_path),
        "covers": [str(p) for p in covers]
    }

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parents[2] / "results" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    info = run_benchmark(out_dir, passphrase="ie406-demo")
    print("Done. CSV:", info["csv"])
    print("PSNR plot:", info["psnr_plot"])
    print("Time plot:", info["time_plot"])
