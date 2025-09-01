# Nội dung chi tiết thuyết trình

## Slide 1: Giới thiệu – Kỹ thuật LSB cơ bản

* **LSB (Least Significant Bit)**: thay thế bit ít quan trọng nhất trong mỗi kênh màu (R, G, B).
* Với ảnh 24-bit (RGB), mỗi pixel có 3 byte → có thể giấu được 3 bit.
* **Ví dụ code (sequential)** – file `lsb_sequential.py`:

```python
flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | bits
```

→ Thay thế LSB của dãy pixel từ đầu đến cuối bằng bit dữ liệu.

* **Ưu điểm:** đơn giản, dung lượng chứa lớn.
* **Hạn chế:** nhúng **theo thứ tự tuần tự** → dễ bị phân tích.

---

## Slide 2: Vấn đề – Dễ bị phát hiện

* Kỹ thuật LSB cơ bản để lại **pattern rõ rệt** khi phân tích thống kê.
* **Ví dụ: LSB-plane** (ảnh chỉ giữ lại bit thấp nhất mỗi kênh):

  * Sequential: vùng đầu ảnh bị thay đổi nhiều → dễ nhìn ra.
* Tấn công bằng **RS analysis** hoặc quan sát trực quan có thể phát hiện dữ liệu ẩn.

Vì vậy cần **cải tiến cách chọn vị trí nhúng** để phân tán dấu vết.

---

## Slide 3: Giải pháp – Random pixel + Khóa bí mật

* **Ý tưởng cải tiến:**

  * Header (28 byte) nhúng tuần tự ở đầu ảnh → lưu thông tin payload\_len, CRC, salt.
  * Payload nhúng vào **pixel ngẫu nhiên** trên toàn ảnh.
  * Dãy vị trí được sinh ra từ **PRNG (PCG64)** seed bởi passphrase + salt.

* **Code minh họa (random)** – file `lsb_random_v2.py`:

```python
seed = kdf_seed(passphrase, salt, out_bytes=16)
rng = _rng_from_seed(seed)
rng.shuffle(remaining_slots)
payload_bit_indices = remaining_slots[:len(payload_bits)]
flat[payload_bit_indices] = (flat[payload_bit_indices] & 0xFE) | payload_bits
```

* **Lợi ích:**

  * Dữ liệu phân tán đều → khó nhận biết pattern.
  * Có khóa bí mật → giải mã sai pass = CRC FAIL.

---

## Slide 4: Demo giao diện Encode/Decode

* Ứng dụng viết bằng **Python Tkinter GUI** (`main_window.py`).

* **Tab Encode**:

  * Chọn ảnh cover, file cần giấu, nhập passphrase.
  * Xem dung lượng chứa (capacity).
  * Nhúng → tạo ảnh stego + báo PSNR.

* **Tab Decode**:

  * Chọn ảnh stego + nhập passphrase.
  * Giải mã → xuất payload (`extracted_payload.bin`).
  * Nếu sai pass → báo “CRC FAIL”.

Demo quay video: giấu 1 file `.txt` nhỏ, sau đó giải mã thành công.

---

## Slide 5: Kết quả Benchmark – PSNR

* **So sánh Sequential vs Random** (ảnh gradient 512×512).
* **PSNR theo %capacity:**

  * 10% → \~52 dB (ảnh gần như không đổi).
  * 80% → \~40 dB (vẫn chấp nhận được).
* **Biểu đồ:** `psnr_vs_capacity.png`

Chất lượng ảnh **không khác biệt đáng kể** giữa sequential và random.

---

## Slide 6: Kết quả Benchmark – Thời gian

* **Encode time vs Payload** (ảnh gradient 512×512).
* Sequential nhanh nhất (nhúng tuần tự).
* Random chậm hơn chút (shuffle vị trí) → chênh lệch <5 ms.
* **Biểu đồ:** `encode_time_vs_payload.png`

Thời gian thực thi **không ảnh hưởng nhiều**, vẫn đủ nhanh.

---

## Slide 7: Kết quả Benchmark – LSB-plane

* Quan sát trực quan:

  * Sequential → LSB-plane lộ pattern ở đầu ảnh.
  * Random → LSB-plane nhiễu phân tán đều.
* **Ảnh minh họa:**

  * `*_lsbplane_seq.png`
  * `*_lsbplane_rand.png`

Random + key giúp dữ liệu “ẩn sâu hơn” trong nhiễu.

---

## Slide 8: Kết luận & Hướng phát triển

* **Kết luận:**

  * Cải tiến LSB bằng random pixel + khóa bí mật giúp tăng tính bảo mật.
  * PSNR, chất lượng ảnh giữ nguyên.
  * Thời gian thực thi chấp nhận được.
* **Hướng phát triển:**

  * Tiền xử lý payload bằng mã hóa (AES, ChaCha20).
  * Nhúng chọn lọc vào vùng nhiều texture để giảm nguy cơ phát hiện.
  * Mở rộng sang video/audio.


# Chia slide thuyết trình

## **Phần 1 – Giới thiệu**

* **Slide 1:** Giới thiệu nhóm (tên, MSSV, phân công).
* **Slide 2:** Đề tài: *“Cải tiến kỹ thuật LSB với lựa chọn Pixel ngẫu nhiên và khóa bí mật”*.

  * Nói ngắn gọn về mục tiêu và ý nghĩa.

---

## **Phần 2 – Cơ sở lý thuyết**

* **Slide 3:** *Kỹ thuật LSB cơ bản – Nền tảng*

  * Giải thích LSB là gì.
  * Ví dụ thay bit LSB trong pixel.
  * Công thức PSNR.
* **Slide 4:** *Điểm yếu của LSB tuần tự – Dễ bị phát hiện*

  * Minh họa LSB-plane.
  * Nêu một số phương pháp tấn công (RS, histogram…).

---

## **Phần 3 – Giải pháp cải tiến**

* **Slide 5:** *Cải tiến: Random pixel + Khóa bí mật*

  * Ý tưởng: phân tán bit nhúng, dựa trên passphrase.
  * Header 28 byte, PRNG (PCG64).
  * Lợi ích: tăng tính ẩn, khó phát hiện.

---

## **Phần 4 – Demo + Kết quả + Kết luận (Hồ Hoàng Phú)**

* **Slide 6:** *Demo – Giao diện ứng dụng Encode/Decode*

  * Encode: chọn ảnh cover + payload + passphrase → stego.
  * Decode: nhập passphrase → trích xuất.
  * Nếu sai pass → CRC FAIL.

* **Slide 7:** *Kết quả Benchmark – PSNR*

  * Biểu đồ PSNR vs % capacity.
  * Nhận xét: random ≈ sequential về chất lượng.

* **Slide 8:** *Kết quả Benchmark – Thời gian*

  * Encode random chậm hơn 2–5 ms.
  * Không ảnh hưởng thực tế.

* **Slide 9:** *Kết quả Benchmark – LSB-plane*

  * Sequential: pattern rõ.
  * Random: nhiễu phân tán, khó phát hiện.

* **Slide 10:** *Hướng phát triển*

  * Giấu chọn lọc vào vùng texture cao.
  * Kết hợp mã hóa AES/ChaCha20.
  * Mở rộng sang video/audio.

* **Slide 11 (kết thúc):** *Tóm tắt & Cảm ơn*

  * Kỹ thuật cải tiến đạt mục tiêu: **tăng tính ẩn giấu mà không ảnh hưởng chất lượng**.
  * Cảm ơn thầy và các bạn đã lắng nghe.

---

* **Một người:** 1–2
* **Một người:** 3–4
* **Một người:** 5
* **Phú:** Còn lại