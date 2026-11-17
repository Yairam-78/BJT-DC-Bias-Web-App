# BJT DC Bias Calculator

Flask Web App สำหรับคำนวณ **จุดทำงานกระแสตรง (DC Operating Point)** ของวงจรขยาย
BJT NPN Common-Emitter **สามแบบไบอัส** — Voltage Divider, Fixed Bias และ Emitter Bias
แบบแหล่งจ่ายเดียว — ด้วย Forward-Active Approximation (β คงที่, VBE คงที่)

งานนี้เป็นชิ้นงาน Lab 03 ของรายวิชา ENG29 2121 ต่อยอดจาก Lab 02 — โปรแกรมเป็น Web Application
หลายไฟล์ที่มี Python Backend คำนวณจริง ไม่ใช่ HTML ที่ฝังตัวเลขไว้

## ภาพรวม

- เลือกวงจรไบอัสได้ 3 แบบ ฟอร์มแสดงเฉพาะช่องที่วงจรนั้นต้องใช้
- หน้าเว็บให้กรอก VCC, RB / R1 / R2, RC, RE, β และ VBE พร้อมเลือกหน่วยของแต่ละช่องได้
  (Ω / kΩ / MΩ สำหรับตัวต้านทาน, V / mV สำหรับแรงดัน)
- Python (`dc_bias.py`) คำนวณ VB, VE, VC, VCE, IC, IB, IE (+ VTH, RTH สำหรับ Divider)
- แสดงหน่วยกำกับทุกค่า และแจ้งสถานะการทำงาน: Forward-Active / Cutoff / Saturation
- ตรวจสอบข้อมูลนำเข้าและแสดงข้อความผิดพลาดที่อ่านได้ (ไม่ทำให้หน้าเว็บล้ม)

## โครงสร้างโปรเจกต์

```
BJT DC Bias Web App/
├── app.py                  # Flask routes, form parsing, unit → SI conversion, mode dispatch
├── dc_bias.py              # สมการวิศวกรรมล้วน (SI units) ไม่รู้จัก HTTP
├── templates/index.html    # ฟอร์มและตารางผลลัพธ์ (Jinja)
├── static/style.css        # หน้าตาเว็บ
├── tests/
│   ├── test_dc_bias.py     # ทดสอบสมการ, validation, operating region
│   └── test_web.py         # ทดสอบ HTTP ด้วย Flask test client
├── opencode.json           # MCP Server (Playwright) สำหรับให้ AI ตรวจเว็บ
├── requirements.txt
└── docs/
    ├── validation.md       # เทียบค่ากับการคำนวณอ้างอิง (A1–A5)
    ├── reflection.md       # สิ่งที่ได้เรียนรู้
    ├── evidence/           # ภาพหน้าจอหลักฐานการตรวจผ่าน Browser
    └── superpowers/        # spec และ plan ของแต่ละสัปดาห์
```

## ความต้องการของระบบ

- Python 3.10 ขึ้นไป (พัฒนาและทดสอบบน Python 3.14.2)
- Flask 3.x (ติดตั้งจาก `requirements.txt`)
- ไม่ต้องใช้ Node.js, JavaScript framework หรือฐานข้อมูล

## การติดตั้ง

```bash
python -m venv .venv
```

เปิดใช้งาน virtual environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

ติดตั้ง dependency:

```bash
python -m pip install -r requirements.txt
```

## การรันเว็บ

```bash
python -m flask --app app run
```

แล้วเปิด <http://127.0.0.1:5000/>

> ต้องเปิดผ่าน Flask Server เท่านั้น การ double-click เปิด `templates/index.html`
> จะใช้ไม่ได้ เพราะไม่มี Python ทำงานอยู่เบื้องหลัง (ตัวไฟล์เป็น Jinja template
> ที่ยังไม่ถูก render และไม่มีใครคำนวณผลให้)

## การทดสอบ

```bash
python -m unittest discover -s tests -v
```

ชุดทดสอบมี 25 tests ครอบคลุม

- สมการ DC bias เทียบค่าอ้างอิง
- การตรวจสอบข้อมูลนำเข้า (R ≤ 0, β ≤ 0, VCC ≤ 0, VBE ติดลบ)
- การตรวจจุดทำงาน Cutoff และ Saturation
- HTTP: `GET /` และ `POST /calculate` ผ่าน Flask test client
- ข้อมูลผิดรูปแบบ เช่น ช่องว่าง, `abc`, `100,000`
- การเลือกหน่วย (Ω / kΩ / MΩ, V / mV) และหน่วยที่ไม่รู้จัก

Lab 03 ไม่ได้เพิ่ม unittest ใหม่ตามใบงาน — การตรวจรับงานทำผ่าน Browser
ด้วยตาราง A1–A5 ใน [`docs/validation.md`](docs/validation.md)

## หน่วยของค่า

| ปริมาณ | หน่วยที่กรอกบนหน้าเว็บ | หน่วยภายใน `dc_bias.py` | หน่วยที่แสดง |
|---|---|---|---|
| VCC, VBE | เลือกได้: V หรือ mV (ค่าเริ่มต้น V) | V | V |
| RB, R1, R2, RC, RE | เลือกได้: Ω, kΩ หรือ MΩ (ค่าเริ่มต้น kΩ) | Ω | — |
| β | ไม่มีหน่วย | ไม่มีหน่วย | — |
| VB, VE, VC, VCE, VTH | — | V | V (3 ตำแหน่ง) |
| IC, IE | — | A | mA (3 ตำแหน่ง) |
| IB | — | A | µA (3 ตำแหน่ง) |
| RTH | — | Ω | kΩ (1 ตำแหน่ง) |

`app.py` เป็นผู้แปลงค่าที่ผู้ใช้เลือกหน่วยมาเป็นหน่วยฐาน SI
(Ω, V) ก่อนเรียก `dc_bias.py`
โมดูลคำนวณจึงทำงานในหน่วยฐาน SI เสมอ และทดสอบแยกได้โดยไม่ต้องมี Flask

## โหมดที่รองรับ

| โหมด | อินพุตที่ใช้ | ตำแหน่งตัวต้านทาน |
|---|---|---|
| **Voltage Divider Bias** | VCC, R1, R2, RC, RE, β, VBE | R1 จาก VCC ไป Base, R2 จาก Base ลงกราวด์, RE จาก Emitter ลงกราวด์ |
| **Fixed Bias** | VCC, RB, RC, β, VBE | RB จาก VCC ไป Base, Emitter ต่อลงกราวด์โดยตรง |
| **Emitter Bias** | VCC, RB, RC, RE, β, VBE | RB จาก VCC ไป Base, RE จาก Emitter ลงกราวด์ |

กดการ์ดวงจรที่ต้องการได้เลย (ไม่ต้องกดปุ่มโหลด) ฟอร์มจะแสดงเฉพาะช่องที่โหมดนั้นใช้
และไฮไลต์การ์ดของโหมดปัจจุบันไว้
โหมดที่ไม่รู้จักจะแจ้งข้อผิดพลาด ไม่ถูกตีความเป็น Voltage Divider

## สมการที่ใช้

```
Voltage Divider Bias
  VTH = VCC × R2 / (R1 + R2)
  RTH = R1·R2 / (R1 + R2)
  IB  = (VTH − VBE) / (RTH + (β+1)·RE)

Fixed Bias
  IB  = (VCC − VBE) / RB

Emitter Bias (แหล่งจ่ายเดียว)
  IB  = (VCC − VBE) / (RB + (β+1)·RE)

ทุกโหมด
  IC  = β·IB
  IE  = (β+1)·IB
  VE  = IE·RE       (Fixed: VE = 0 V)
  VB  = VE + VBE
  VC  = VCC − IC·RC
  VCE = VC − VE
```

ค่าคงที่ทุกโหมด: `VCC`, `RC`, `β`, `VBE` — หน่วย SI ภายในคือ V, A, Ω

## การตรวจรับงานผ่าน Browser (Playwright MCP)

ไฟล์ `opencode.json` ที่รากโปรเจกต์เปิด MCP Server ชื่อ `playwright` (OpenCode V2):

```json
{
  "mcp": {
    "servers": {
      "playwright": {
        "type": "local",
        "command": ["npx", "-y", "@playwright/mcp@latest", "--browser", "chrome", "--isolated"]
      }
    }
  }
}
```

- ต้องมี **Node.js 18+** และ Google Chrome บนเครื่องที่รัน OpenCode
- `type: local` ทำให้ OpenCode เริ่ม MCP Server เป็นโปรเซสในเครื่อง สื่อสารผ่าน `stdio`
  พอร์ต `5000` ยังเป็นของ Flask
- ตรวจว่าเชื่อมต่อได้ด้วย `/mcps` ในแอป หรือ `opencode mcp list` ใน terminal

ถ้าไม่มี Node.js ให้ใช้ browser tool ที่มีใน OpenCode หรือตรวจด้วยมือ
แล้วบันทึกวิธีที่ใช้จริงใน `docs/validation.md` — ห้ามใช้ `curl` หรืออ่านโค้ดแทนการรัน Browser

## สมมติฐานและข้อจำกัด

- ใช้ **Forward-Active Approximation**: β คงที่ และ VBE คงที่ ไม่คำนึงถึงอุณหภูมิ
- **ไม่ใช่ SPICE/ngspice** ไม่มีการแก้สมการแบบ nonlinear หรือ model ของผู้ผลิต
- ถ้า `VTH ≤ VBE` (Divider) หรือ `VCC ≤ VBE` (Fixed/Emitter) ถือเป็น **Cutoff**
  (กระแสเป็นศูนย์) และแจ้งว่าแบบจำลองใช้ไม่ได้
- ถ้า `VCE ≤ 0.3 V` ถือว่า **Saturation** — ค่า IC จากสมการ forward-active
  **ไม่ใช่ค่าที่เชื่อถือได้** โปรแกรมจะแสดง warning กำกับเสมอ
- ผลลัพธ์ใช้อ้างอิงทางการศึกษา ไม่ใช่สำหรับออกแบบวงจรจริง

## เอกสารเพิ่มเติม

- [`docs/validation.md`](docs/validation.md) — เทียบค่าที่โปรแกรมคำนวณกับการคำนวณอิสระ
- [`docs/reflection.md`](docs/reflection.md) — สิ่งที่ได้เรียนรู้จาก Lab นี้
