# Nội dung báo cáo

## 1. Giới thiệu

* **Mục tiêu**: Ẩn dữ liệu trong ảnh sao cho khó phát hiện, vẫn giữ chất lượng hình ảnh cao.
* **Vấn đề**: LSB truyền thống nhúng dữ liệu tuần tự (từ pixel đầu → cuối). Dễ bị tấn công phân tích (statistical steganalysis, RS analysis).
* **Ý tưởng cải tiến**:

  1. Chọn vị trí pixel ngẫu nhiên dựa vào PRNG (Pseudo Random Number Generator).
  2. PRNG seed sinh từ **khóa bí mật** (passphrase + salt → PBKDF2).
     → Giúp kẻ tấn công khó đoán được vị trí bit bị thay đổi.

---

## 2. Kiến thức nền

* **LSB cơ bản**: thay bit ít quan trọng (Least Significant Bit) trong mỗi kênh màu R, G, B.
* **Hạn chế**:

  * Pattern thay đổi rõ (tuần tự từ đầu đến cuối ảnh).
  * Dễ lộ khi dùng test thống kê.
* **PRNG + Key**:

  * PRNG: sinh dãy số giả ngẫu nhiên (ở đây dùng PCG64).
  * Khóa bí mật + salt → seed PRNG → sinh ra dãy chỉ số pixel.
  * Tính bảo mật tăng: không có khóa thì không tái tạo được thứ tự nhúng.

---

## 3. Thuật toán đề xuất

* **Nhúng**:

  1. Ghi header (MAGIC + length + CRC + salt) tuần tự đầu ảnh.
  2. Sinh PRNG với seed từ passphrase+salt.
  3. Trộn dãy pixel còn lại → chọn ra vị trí để nhúng payload.
* **Tách**:

  1. Đọc header tuần tự (lấy salt, payload\_len).
  2. Tái tạo PRNG từ passphrase+salt.
  3. Giải nhúng payload tại vị trí đã trộn.
  4. Kiểm tra CRC.

**Khác biệt so với LSB tuần tự**:

* LSB thường: pixel \[0..N] lần lượt bị thay đổi.
* LSB cải tiến: vị trí nhúng được random → giảm khả năng phát hiện.

---

## 4. Cài đặt & Giao diện

* Ngôn ngữ: Python, Tkinter GUI.
* Lib: Pillow, NumPy.
* Flow GUI: Tab Encode, Tab Decode, hiển thị PSNR.
* Output: ảnh stego + file payload giải nhúng.

---

## 5. Thí nghiệm

### Dữ liệu

* Bộ ảnh PNG: 512×512, 1024×1024, 1920×1080.
* Payload: text 10KB, 100KB, 500KB.
* Môi trường: Windows 11, Python 3.11.

### Metric

* **PSNR** (Peak Signal-to-Noise Ratio).
* **SSIM** (Structural Similarity, optional).
* **Capacity** (bytes có thể nhúng).
* **Thời gian encode/decode**.

### Kết quả mẫu (bảng)

| Ảnh      | Size (px) | Payload | %Capacity | PSNR (dB) | SSIM  | Time (s) |
| -------- | --------- | ------- | --------- | --------- | ----- | -------- |
| Lena.png | 512×512   | 10KB    | 10%       | 52.3      | 0.998 | 0.12     |
| Lena.png | 512×512   | 100KB   | 90%       | 40.8      | 0.985 | 0.15     |
| HD.png   | 1920×1080 | 500KB   | 50%       | 47.2      | 0.992 | 0.44     |

---

## 6. So sánh LSB tuần tự vs cải tiến

* **PSNR**: gần như tương đương (cùng thay LSB 1 bit).
* **Bảo mật**:

  * Tuần tự → dễ phát hiện khi plot LSB plane.
  * Random → pattern bị phân tán đều, khó thống kê.

Đây chính là điểm **cải tiến** quan trọng: phân tán bit thay đổi.

### Biểu đồ minh họa

* Biểu đồ PSNR theo dung lượng nhúng (so sánh tuần tự vs random).
* Biểu đồ thời gian encode (hai thuật toán gần như ngang nhau).
* Hình ảnh minh họa: LSB-plane của ảnh tuần tự vs ảnh random (tuần tự hiện rõ vùng đầu ảnh bị thay đổi, random thì nhiễu đều).

---

## 7. Kết luận & Hướng phát triển

* Đề xuất giúp tăng tính bảo mật chống phân tích mà vẫn giữ chất lượng ảnh.
* Cải tiến nhỏ nhưng thực tế, dễ áp dụng.
* Hạn chế: vẫn không chống được nén JPEG.
* Hướng phát triển: XOR payload bằng stream cipher, kết hợp kênh chọn lọc (ví dụ chỉ nhúng vào vùng có nhiều texture).