# AGENTS.md — กติกาสำหรับ AI Coding Agent

โปรเจกต์นี้เป็น Flask Web App สำหรับคำนวณ BJT DC Bias (ENG29 2121 Lab 02)
กติกาต่อไปนี้มีผลกับทุกการแก้ไขโค้ดใน repository นี้

## สถาปัตยกรรม

- `dc_bias.py` เป็น **pure Python** — ห้าม import `flask`, `jinja2` หรืออะไรที่เกี่ยวกับ HTTP
- `dc_bias.py` รับและคืนค่าใน **หน่วย SI เท่านั้น** (V, A, Ω) — การแปลงหน่วยที่ผู้ใช้เลือกบนฟอร์ม (Ω/kΩ/MΩ, V/mV) เป็นความรับผิดชอบของ `app.py`
- `templates/index.html` แสดงผลเท่านั้น — **ห้ามใส่สมการฟิสิกส์หรือคำนวณตัวเลขใน template**
- `app.py` ทำหน้าที่ parse ฟอร์ม, แปลงหน่วย, เรียก `dc_bias`, และ render — ไม่มีสมการวิศวกรรม
- ผลลัพธ์ทุกค่าต้องไหลจาก `dc_bias.calculate_dc_bias()` เสมอ **ห้ามฮาร์ดโค้ดตัวเลขผลลัพธ์ใน HTML**

## การทดสอบ

- ทุกฟีเจอร์หรือ bug fix ต้องมี test ก่อนเขียน implementation (TDD)
- รันทั้งชุดด้วย `python -m unittest discover -s tests -v` — ต้องเขียวทั้งหมดก่อน commit
- test ของสมการอยู่ใน `tests/test_dc_bias.py`, test ของ HTTP อยู่ใน `tests/test_web.py`
- test ต้องไม่พึ่ง network หรือ service ภายนอก

## ข้อผิดพลาดและข้อความ

- ข้อมูลนำเข้าไม่ถูกต้อง → คืน **HTTP 200** พร้อมข้อความบนหน้าเดิม (ไม่ใช้ 400/500 กับฟอร์ม)
- ข้อความ error/warning เป็นภาษาไทย และต้องบอกว่าช่องไหนผิด
- ห้ามกลืน exception เงียบ ๆ — ถ้าคำนวณต่อไม่ได้ ให้แสดงข้อความที่ผู้ใช้อ่านรู้เรื่อง

## สไตล์โค้ด

- Python มาตรฐาน ไม่ต้องพึ่ง dependency เพิ่มนอกจาก Flask
- ใช้ type hints ในฟังก์ชันสาธารณะ
- ตั้งชื่อตัวแปรตามสัญลักษณ์วิศวกรรม (`vcc`, `r1`, `vbe`, `vce`)
- คอมเมนต์อธิบาย "ทำไม" ไม่ใช่ "ทำอะไร" และเขียนเป็นภาษาอังกฤษในโค้ด

## ขอบเขต

- งานนี้อยู่ในขอบเขต DC Bias เท่านั้น — ห้ามเพิ่ม AC analysis, Bode plot, Transient,
  SPICE solver หรือ bias topology อื่น unless ผู้ใช้ขอชัดเจน
- อย่าเพิ่ม dependency, build step หรือ JavaScript framework โดยไม่ถาม

## Git

- ห้าม commit `.venv/`, `__pycache__/`, `.env` หรือ credential ใด ๆ
- commit message ใช้รูปแบบ `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
