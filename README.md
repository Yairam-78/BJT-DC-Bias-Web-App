# BJT DC Bias Calculator

Flask Web App สำหรับคำนวณ **จุดทำงานกระแสตรง (DC Operating Point)** ของวงจรขยาย
BJT NPN Common-Emitter **สามแบบไบอัส** — Voltage Divider, Fixed Bias และ Emitter Bias
แบบแหล่งจ่ายเดียว — ด้วย Forward-Active Approximation (β คงที่, VBE คงที่)

งานนี้เป็นชิ้นงาน Lab 03 ของรายวิชา ENG29 2121 ต่อยอดจาก Lab 02 — โปรแกรมเป็น Web Application
หลายไฟล์ที่มี Python Backend คำนวณจริง ไม่ใช่ HTML ที่ฝังตัวเลขไว้
Lab 04 ต่อยอดแอปเดิมโดยเพิ่ม **CE Amplifier Simulator** ที่รัน ngspice จริง (.op / .ac / .tran)
โดยไม่แก้ผลคำนวณ Lab 03 เดิม

## ภาพรวม

- เลือกวงจรไบอัสได้ 3 แบบ ฟอร์มแสดงเฉพาะช่องที่วงจรนั้นต้องใช้
- หน้าเว็บให้กรอก VCC, RB / R1 / R2, RC, RE, β และ VBE พร้อมเลือกหน่วยของแต่ละช่องได้
  (Ω / kΩ / MΩ สำหรับตัวต้านทาน, V / mV สำหรับแรงดัน)
- Python (`dc_bias.py`) คำนวณ VB, VE, VC, VCE, IC, IB, IE (+ VTH, RTH สำหรับ Divider)
- แสดงหน่วยกำกับทุกค่า และแจ้งสถานะการทำงาน: Forward-Active / Cutoff / Saturation
- ตรวจสอบข้อมูลนำเข้าและแสดงข้อความผิดพลาดที่อ่านได้ (ไม่ทำให้หน้าเว็บล้ม)
- **Lab 04:** แท็บแยกสำหรับกรอก VCC/R1/R2/RC/RE/RL/Cin/Cout/Amplitude/Frequency
  เลือก Source/Analysis/Model แล้วกด **Run ngspice** → แสดง operating point, Bode plot,
  transient waveform, log และ netlist ที่ใช้รันจริง

## โครงสร้างโปรเจกต์

```
BJT DC Bias Web App/
├── app.py                  # Flask routes, form parsing, unit → SI conversion, mode dispatch
├── dc_bias.py              # สมการวิศวกรรม Lab 03 ล้วน (SI units) ไม่รู้จัก HTTP
├── spice_engine.py         # Lab 04: netlist, subprocess ngspice, binary raw parser, SVG charts
├── templates/index.html    # ฟอร์มและตารางผลลัพธ์ (Jinja)
├── static/style.css        # หน้าตาเว็บ (tokens, status, responsive)
├── static/app.js           # JavaScript เปล่า ๆ สำหรับแสดง RUNNING ทันทีหลัง submit
├── reference/              # netlist ตัวอย่าง + โมเดล 2N3904 แบบ PROVISIONAL
├── tests/
│   ├── test_dc_bias.py     # ทดสอบสมการ, validation, operating region
│   ├── test_web.py         # ทดสอบ HTTP ด้วย Flask test client
│   ├── test_spice_engine.py # ทดสอบ parser/analysis/netlist (mock subprocess)
│   └── test_simulate_web.py # ทดสอบ POST /simulate (mock engine)
├── opencode.json           # MCP Server (Playwright) สำหรับให้ AI ตรวจเว็บ
├── .opencode/              # คำสั่ง/skill Impeccable ที่ติดตั้งแบบ project-scope
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
- **Lab 04:** ngspice (ทดสอบกับ v47 จาก MSYS2 ucrt64) **ต้องอยู่ใน PATH** หรือตำแหน่งที่
  `spice_engine.resolve_ngspice()` รู้จัก; กำหนด `NGSPICE_BIN` เพื่อ override ได้
- ตัวแอปไม่ต้องใช้ Node.js, JavaScript framework หรือฐานข้อมูล (ใช้ vanilla JS ไฟล์เดียวเพื่อแสดงสถานะ)
- Node.js 18+ จำเป็นเฉพาะตอนรัน Playwright MCP สำหรับตรวจรับงาน

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

ชุดทดสอบมี 51 tests (Lab 03 เดิม 25 + Lab 04 เดิม 20 + status/analytical ใหม่ 6) ครอบคลุม

- สมการ DC bias เทียบค่าอ้างอิง
- การตรวจสอบข้อมูลนำเข้า (R ≤ 0, β ≤ 0, VCC ≤ 0, VBE ติดลบ)
- การตรวจจุดทำงาน Cutoff และ Saturation
- HTTP: `GET /` และ `POST /calculate` ผ่าน Flask test client
- ข้อมูลผิดรูปแบบ เช่น ช่องว่าง, `abc`, `100,000`
- การเลือกหน่วย (Ω / kΩ / MΩ, V / mV) และหน่วยที่ไม่รู้จัก
- Lab 04: netlist, binary raw parser, `.op/.ac/.tran` analysis และ SVG chart (`spice_engine.py`)
- Lab 04: `POST /simulate` ทั้งกรณีสำเร็จ, input ผิด และ ngspice ล้มเหลว
- Lab 04: status `RUNNING/SUCCESS/ERROR`, provenance, analytical reference แยกจาก SPICE

Lab 03 ไม่ได้เพิ่ม unittest ใหม่ตามใบงาน — รอบแรกตรวจด้วย OpenCode Browser ตามตาราง A1–A5
ส่วน Lab 04 ตรวจ B1–B8 ด้วย **Playwright MCP จริง** และบันทึกผล/ภาพก่อน-หลังใน
[`docs/validation.md`](docs/validation.md)

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

รอบ Lab 04 ใช้ **Playwright MCP จริง** ผ่าน `tools/call` (`browser_navigate`, `browser_fill_form`,
`browser_select_option`, `browser_click`, `browser_evaluate`, `browser_take_screenshot`) บน Flask
ที่รันอยู่จริง ไม่ใช่ mock/curl ใน session นี้ MCP tools ไม่ปรากฏใน tool catalog จึงขับ MCP server
ตรงผ่าน stdio ด้วย helper ชั่วคราว และเก็บผลดิบไว้ใน `docs/evidence/playwright_*_results.json`
ผล B1–B8, viewport 1280×900/390×844 และภาพ before/after อยู่ใน [`docs/validation.md`](docs/validation.md)

> ถ้าไม่มี Node.js ให้ใช้ browser tool ที่มีใน OpenCode หรือตรวจด้วยมือแล้วบันทึกวิธีที่ใช้จริง
> ห้ามใช้ `curl` หรืออ่านโค้ดแทนการรัน Browser

## Lab 04: CE Amplifier Simulator

แท็บ Lab 04 เรียก `/simulate` แยกจาก `/calculate` ของ Lab 03 และรัน ngspice จริงด้วยคำสั่ง
`ngspice -b -o run.log -r run.raw circuit.cir` ใน temporary directory ผลกราฟอ่านจาก binary raw
(`.op`, complex `.ac`, real `.tran`) ไม่ได้อ่าน `.print` จาก log และไม่มีค่าผลลัพธ์ฝังไว้ใน HTML
หน้าเว็บแสดงสถานะ `RUNNING → SUCCESS/ERROR`, engine badge, provenance ของ solver และตาราง
**Analytical Reference (`dc_bias.py`)** แยกต่างหากจาก **SPICE / ngspice** — β/VBE ในฟอร์ม Lab 04
ใช้เฉพาะตารางอ้างอิง ส่วน solver ใช้ `Bf` จากไฟล์โมเดล

โมเดลเริ่มต้นคือ `reference/provisional_2n3904.bjt` ซึ่งกำกับไว้ชัดเจนว่า **PROVISIONAL**
อาจารย์ไม่ได้แจก Starter Kit หรือโมเดล BJT ที่รับรองให้ ณ วันที่ส่งงาน จึงใช้โมเดลภายในโปรเจกต์
และไม่เลือกตัวเลือก `Lab verified model` / `Instructor Starter Kit file`
หน้าเว็บแสดงป้าย `PROVISIONAL` ใกล้หัวข้อและปุ่ม Run รวมถึง
`Local reference model (not instructor-verified)` ในบรรทัดผลลัพธ์เสมอ
ถ้าได้รับไฟล์จากอาจารย์ภายหลังจึงเปลี่ยน path และชื่อ `.model` ในฟอร์มแล้วรัน B1–B8 ใหม่
รายละเอียดและข้อควรระวังอยู่ใน [`reference/README.md`](reference/README.md)

## สมมติฐานและข้อจำกัด

- โหมด Lab 03 ใช้ **Forward-Active Approximation**: β คงที่ และ VBE คงที่ ไม่คำนึงถึงอุณหภูมิ
- โหมด Lab 03 **ไม่ใช่ SPICE/ngspice** ไม่มีการแก้สมการแบบ nonlinear หรือ model ของผู้ผลิต
  (Lab 04 เป็นคนละแท็บและรัน ngspice จริงตามที่อธิบายข้างต้น)
- ถ้า `VTH ≤ VBE` (Divider) หรือ `VCC ≤ VBE` (Fixed/Emitter) ถือเป็น **Cutoff**
  (กระแสเป็นศูนย์) และแจ้งว่าแบบจำลองใช้ไม่ได้
- ถ้า `VCE ≤ 0.3 V` ถือว่า **Saturation** — ค่า IC จากสมการ forward-active
  **ไม่ใช่ค่าที่เชื่อถือได้** โปรแกรมจะแสดง warning กำกับเสมอ
- ผลลัพธ์ใช้อ้างอิงทางการศึกษา ไม่ใช่สำหรับออกแบบวงจรจริง

## เอกสารเพิ่มเติม

- [`docs/validation.md`](docs/validation.md) — ตาราง A1–A5, B1–B8 และผล Impeccable
- [`docs/evidence/`](docs/evidence/) — ภาพ before/after, ผล Playwright ดิบ และหลักฐาน A4/A5
- [`docs/reflection.md`](docs/reflection.md) — สิ่งที่ได้เรียนรู้จาก Lab นี้
