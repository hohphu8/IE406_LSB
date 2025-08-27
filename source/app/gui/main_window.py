import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ..core.lsb_random_v2 import capacity_bytes_for_image, encode_v2, decode_v2

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSB Stego — Random Pixel + Secret Key (IE406)")
        self.resizable(False, False)

        nb = ttk.Notebook(self)
        self.encode_tab = EncodeTab(nb)
        self.decode_tab = DecodeTab(nb)
        nb.add(self.encode_tab, text="Encode")
        nb.add(self.decode_tab, text="Decode")
        nb.pack(expand=True, fill="both")

class EncodeTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        pad = {"padx": 8, "pady": 6}

        ttk.Label(self, text="Cover image (PNG/BMP):").grid(row=0, column=0, sticky="w", **pad)
        self.cover_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.cover_var, width=60).grid(row=0, column=1, **pad)
        ttk.Button(self, text="Browse", command=self.pick_cover).grid(row=0, column=2, **pad)

        ttk.Label(self, text="Secret file to embed:").grid(row=1, column=0, sticky="w", **pad)
        self.payload_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.payload_var, width=60).grid(row=1, column=1, **pad)
        ttk.Button(self, text="Browse", command=self.pick_payload).grid(row=1, column=2, **pad)

        ttk.Label(self, text="Passphrase:").grid(row=2, column=0, sticky="w", **pad)
        self.pass_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.pass_var, width=40, show="*").grid(row=2, column=1, sticky="w", **pad)

        self.cap_label = ttk.Label(self, text="Capacity: —")
        self.cap_label.grid(row=3, column=1, sticky="w", **pad)
        ttk.Button(self, text="Estimate capacity", command=self.estimate).grid(row=3, column=2, **pad)

        ttk.Label(self, text="Output stego image:").grid(row=4, column=0, sticky="w", **pad)
        self.out_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.out_var, width=60).grid(row=4, column=1, **pad)
        ttk.Button(self, text="Save as...", command=self.pick_output).grid(row=4, column=2, **pad)

        ttk.Button(self, text="Embed", command=self.run_embed).grid(row=5, column=1, sticky="w", **pad)

        self.result_label = ttk.Label(self, text="", foreground="green")
        self.result_label.grid(row=6, column=1, sticky="w", **pad)

    def pick_cover(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.bmp;*.jpg;*.jpeg"), ("All", "*.*")])
        if path:
            self.cover_var.set(path)

    def pick_payload(self):
        path = filedialog.askopenfilename(filetypes=[("All", "*.*")])
        if path:
            self.payload_var.set(path)

    def pick_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.out_var.set(path)

    def estimate(self):
        cover = self.cover_var.get().strip()
        if not cover:
            messagebox.showwarning("Warn", "Chọn cover image trước đã.")
            return
        try:
            cap = capacity_bytes_for_image(cover)
            self.cap_label.configure(text=f"Capacity (approx): {cap} bytes")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_embed(self):
        cover = self.cover_var.get().strip()
        payload = self.payload_var.get().strip()
        out_path = self.out_var.get().strip()
        pw = self.pass_var.get()

        if not cover or not payload or not out_path or not pw:
            messagebox.showwarning("Warn", "Điền đủ Cover, Payload, Passphrase, Output.")
            return
        try:
            res = encode_v2(cover, payload, pw, out_path)
            self.result_label.configure(text=f"OK -> PSNR={res.psnr_db:.2f} dB | used {res.used_bytes}/{res.capacity_bytes} bytes")
            messagebox.showinfo("Done", f"Stego saved: {res.stego_path}\nPSNR={res.psnr_db:.2f} dB")
        except Exception as e:
            messagebox.showerror("Error", str(e))

class DecodeTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        pad = {"padx": 8, "pady": 6}

        ttk.Label(self, text="Stego image:").grid(row=0, column=0, sticky="w", **pad)
        self.stego_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.stego_var, width=60).grid(row=0, column=1, **pad)
        ttk.Button(self, text="Browse", command=self.pick_stego).grid(row=0, column=2, **pad)

        ttk.Label(self, text="Passphrase:").grid(row=1, column=0, sticky="w", **pad)
        self.pass_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.pass_var, width=40, show="*").grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(self, text="Output directory:").grid(row=2, column=0, sticky="w", **pad)
        self.out_dir_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.out_dir_var, width=60).grid(row=2, column=1, **pad)
        ttk.Button(self, text="Choose...", command=self.pick_outdir).grid(row=2, column=2, **pad)

        ttk.Button(self, text="Extract", command=self.run_extract).grid(row=3, column=1, sticky="w", **pad)

        self.result_label = ttk.Label(self, text="", foreground="green")
        self.result_label.grid(row=4, column=1, sticky="w", **pad)

    def pick_stego(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png"), ("All", "*.*")])
        if path:
            self.stego_var.set(path)

    def pick_outdir(self):
        path = filedialog.askdirectory()
        if path:
            self.out_dir_var.set(path)

    def run_extract(self):
        stego = self.stego_var.get().strip()
        out_dir = self.out_dir_var.get().strip()
        pw = self.pass_var.get()

        if not stego or not out_dir or not pw:
            messagebox.showwarning("Warn", "Điền đủ Stego, Passphrase, Output dir.")
            return
        try:
            res = decode_v2(stego, pw, out_dir)
            status = "CRC OK" if res.crc_ok else "CRC FAIL (passphrase sai hoặc dữ liệu hỏng)"
            self.result_label.configure(text=f"Saved! {status} | size={res.payload_len} bytes")
            messagebox.showinfo("Done", f"Extracted: {res.output_path}\n{status}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def run():
    app = App()
    app.mainloop()
