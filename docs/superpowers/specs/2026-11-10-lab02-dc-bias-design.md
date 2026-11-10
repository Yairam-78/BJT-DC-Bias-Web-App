# Lab 02 — BJT DC Bias Web App · Design

วันที่: 2026-11-10
รายวิชา: ENG29 2121 (2/2569)
สถานะ: รออนุมัติ

## 1. ทำไมต้องสร้าง (Intent)

ส่งงาน Lab 02 ให้ครบ rubric 10 คะแนน และได้เรียนรู้ว่า Web App จริงแยกส่วน
Frontend / Backend / Engineering Logic / Tests ออกจากกันอย่างไร

ผู้ใช้คือนักศึกษาเอง (เดโมต่ออาจารย์ในคาบ) ไม่มีผู้ใช้ภายนอก ไม่มี deployment จริง
รันบนเครื่องตัวเองที่ `http://127.0.0.1:5000/`

## 2. ขอบเขต

**Goals**
- Flask Web App หลายไฟล์ ที่คำนวณ DC Operating Point ของ NPN Common-Emitter
  แบบ Voltage-Divider Bias ด้วย Python จริง (ไม่ฮาร์ดโค้ดผลใน HTML)
- รับ VCC, R1, R2, RC, RE, β, VBE → แสดง VB, VE, VC, VCE, IC (+ IB, IE) พร้อมหน่วย
- Validation: ค่าผิด/ไม่ใช่ตัวเลข → error ที่อ่านได้ ไม่ทำให้เว็บล้ม
- Warning: กรณี Cutoff และ Saturation
- Automated tests: ≥3 ด้าน engineering math + ≥1 ผ่าน Flask test client
- README ที่ทำให้ clone แล้วรันได้ (A7)
- Commit/push ผ่าน GitHub Desktop

**Non-goals (คาบนี้)**
- AC small-signal, Bode, Transient, Signal Generator, Overlay animation
- Bias หลายแบบ (Fixed / Emitter) — ทำ W3
- SPICE / ngspice, DC Load Line — ทำ W4
- ฐานข้อมูล, ระบบ login, deployment, JavaScript framework

**Anti-goals** (ทำงานได้แต่ถือว่าล้มเหลว)
- ตัวเลขในหน้าเว็บมาจากค่าคงที่ใน HTML ไม่ได้ผ่าน `dc_bias.py`
- เงียบเมื่อผลอยู่นอก forward-active แล้วอ้างว่าแม่นยำ
- เปิดด้วย `file://` แล้วใช้งานได้ (จะแปลว่าที่จริงไม่มี backend)

## 3. ข้อจำกัด

- เวลาคาบจำกัด (ช่วง Build ~75 นาที) → ต้องเล็กและเสร็จแน่
- แบบจำลอง: Forward-Active Approximation, β คงที่, VBE คงที่
- ต้องรันด้วย `python -m unittest discover -s tests -v` (ตาม handout)
- ห้าม commit `.venv/`, `.env`, credentials
- repo ปัจจุบันว่าง (มีแค่ `.gitattributes`) และยังไม่มี remote

## 4. แนวทางที่พิจารณา

| แนวทาง | ข้อดี | ข้อเสีย | สรุป |
|---|---|---|---|
| A. Server-rendered form + POST `/calculate` | ตรงกับ handout, ไม่ต้องเขียน JS, test ง่าย | รีเฟรชแล้ว submit ซ้ำ | **เลือก** |
| B. Single route `/` รับทั้ง GET/POST | น้อยที่สุด | ผสมความรับผิดชอบ, GET/POST ปนกันในฟังก์ชันเดียว | ตก |
| C. JSON API `/api/calculate` + JS fetch | ทันสมัย, แยกชัด | เพิ่ม JS/error handling ฝั่ง client, เกินเวลา, ไม่ตรง diagram ใน handout (HTML response) | ตก |

**เลือก A** เพราะตรงกับ acceptance test (A1/A2) และ data flow ที่ handout วาดไว้
(HTML response กลับไปที่ Browser) โดยไม่ต้องเพิ่มชั้น JavaScript ที่ไม่ได้ให้คะแนน

## 5. ข้อตัดสินใจ (ผมเป็นผู้เลือก)

- **Stack:** Python 3.14.2 + venv, Flask 3.x, Jinja2, CSS เขียนเอง, ไม่มี dependency อื่น
- **Test framework:** `unittest` (stdlib) — ตรงกับคำสั่งใน handout, ไม่ต้องลง pytest
- **Routes:** `GET /` แสดงฟอร์ม (ค่าเริ่มต้นเติมไว้ให้กดคำนวณได้ทันที), `POST /calculate` คำนวณแล้ว render หน้าเดิมพร้อมผล
- **หน่วยอินพุตตัวต้านทาน:** ใช้ **kΩ** บนหน้าเว็บ (label ระบุชัด) แล้ว `app.py` แปลง ×1000 ก่อนส่งให้ `dc_bias.py` ซึ่งทำงานในหน่วยฐาน SI (Ω, V, A) เท่านั้น
- **หน่วยเอาต์พุต:** V เป็นโวลต์, กระแสเป็น mA (IB แสดง µA เพิ่ม), ทศนิยม 3 ตำแหน่ง
- **Validation:** field ว่าง/ไม่ใช่ตัวเลข → error ราย field; VCC, R1, R2, RC, RE > 0; β > 0; VBE ≥ 0 — ใช้ HTTP 200 พร้อมข้อความ error (พฤติกรรมฟอร์มปกติของผู้ใช้)
- **Warnings:**
  - `VTH ≤ VBE` → **Cutoff**: IB = IC = IE = 0, VE = 0, VB = VTH, VC = VCC + warning
  - `VCE ≤ 0.3 V` → **Saturation** (รวมกรณี VCE ติดลบ)
  - นอกนั้น → **Forward-Active** (ไม่แสดง warning)
- **ภาษา:** label/หน่วยเป็นอังกฤษ, ข้อความช่วยเหลือและ warning เป็นไทย
- **ไม่อิง ngspice** และระบุข้อจำกัดไว้ในหน้าเว็บ + README

## 6. โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                  # Flask routes + form parsing + unit conversion
├── dc_bias.py              # สมการล้วน (Ω, V, A) ไม่รู้จัก HTTP/HTML
├── templates/index.html    # ฟอร์ม + ตารางผล + warnings
├── static/style.css
├── tests/
│   ├── test_dc_bias.py     # สมการ, cutoff, saturation, invalid input
│   └── test_web.py         # GET/POST ผ่าน Flask test client
├── requirements.txt
├── README.md
├── AGENTS.md
├── .gitignore
└── docs/
    ├── validation.md       # เทียบค่าที่ได้กับการคำนวณอิสระ
    ├── reflection.md       # สิ่งที่เรียนรู้ (มีคะแนนใน rubric)
    └── superpowers/specs/2026-11-10-lab02-dc-bias-design.md
```

`dc_bias.py` ไม่ import Flask และไม่รู้จักหน่วย kΩ — ทดสอบแยกได้ลำดับ

## 7. หน้าจอ

```
┌──────────────────────────────────────────────────────┐
│  BJT DC Bias Calculator                              │
│  Common Emitter · Voltage Divider Bias · NPN         │
├───────────────────────────┬──────────────────────────┤
│  Inputs                   │  DC Operating Point      │
│  VCC (V)      [ 12   ]    │  VB    [  1.942 V ]      │
│  R1 (kΩ)      [ 100  ]    │  VE    [  1.242 V ]      │
│  R2 (kΩ)      [ 22   ]    │  VC    [  9.294 V ]      │
│  RC (kΩ)      [ 2.2  ]    │  VCE   [  8.052 V ]      │
│  RE (kΩ)      [ 1    ]    │  IC    [  1.230 mA]      │
│  β            [ 100  ]    │  IB    [ 12.30 µA ]      │
│  VBE (V)      [ 0.7  ]    │  IE    [  1.242 mA]      │
│                           │                          │
│  [ Calculate DC Bias ]    │  ● Forward-Active        │
│  (error box ถ้าค่าผิด)     │  (warning box ถ้าไม่ผ่าน) │
└───────────────────────────┴──────────────────────────┘
```

## 8. การตรวจสอบ (Validation)

ค่าอ้างอิงจาก handout (VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70):

| ปริมาณ | ค่าอ้างอิง |
|---|---|
| VTH | 2.164 V |
| RTH | 18.03 kΩ |
| IB | 12.30 µA |
| IC | 1.230 mA |
| IE | 1.242 mA |
| VE | 1.242 V |
| VB | 1.942 V |
| VC | 9.294 V |
| VCE | 8.052 V |

เครื่องหมายถูกต้อง: VCE > 0.3 V → แสดงสถานะ Forward-Active โดยไม่มี warning

## 9. สิ่งที่เหลือให้ผู้สร้างตัดสิน

- สี/ฟอนต์/ระยะห่างของ CSS
- ถ้อยคำของข้อความช่วยเหลือ
- จะแยก `BiasResult` เป็น dataclass หรือ dict (เลือก dataclass เพื่ออ่านง่ายและ type ชัด)
