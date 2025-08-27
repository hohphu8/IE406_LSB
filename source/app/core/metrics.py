import numpy as np

def psnr(orig: np.ndarray, stego: np.ndarray) -> float:
    """
    Compute PSNR between two uint8 RGB images (H,W,3).
    """
    orig = orig.astype(np.float64)
    stego = stego.astype(np.float64)
    mse = np.mean((orig - stego) ** 2)
    if mse == 0:
        return float("inf")
    PIXEL_MAX = 255.0
    return 20 * np.log10(PIXEL_MAX) - 10 * np.log10(mse)
