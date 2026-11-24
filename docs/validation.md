# Validation — BJT DC Bias Web App

วันที่ตรวจ: 2026-11-10
ผู้ตรวจ: นักศึกษา (คำนวณอิสระด้วยมือ + ตรวจด้วย Web App)

## ข้อมูลทดลอง

| พารามิเตอร์ | ค่า |
|---|---|
| VCC | 12 V |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| RC | 2.2 kΩ |
| RE | 1 kΩ |
| β | 100 |
| VBE | 0.70 V |

## การคำนวณอ้างอิงด้วยมือ

```
VTH = 12 × 22 / (100 + 22)        = 2.164 V
RTH = 100 × 22 / (100 + 22)       = 18.033 kΩ
IB  = (2.164 − 0.70) / (18.033k + 101 × 1k)
    = 1.464 / 119.033k            = 12.30 µA
IC  = 100 × 12.30 µA              = 1.230 mA
IE  = 101 × 12.30 µA              = 1.242 mA
VE  = 1.242 mA × 1 kΩ             = 1.242 V
VB  = 1.242 + 0.70                = 1.942 V
VC  = 12 − (1.230 mA × 2.2 kΩ)    = 9.294 V
VCE = 9.294 − 1.242               = 8.052 V
```

## ผลเทียบกับค่าที่โปรแกรมคำนวณ

| ปริมาณ | ค่าอ้างอิง (มือ) | ค่าจากโปรแกรม | ผลต่าง | ผล |
|---|---|---|---|---|
| VTH | 2.164 V | 2.164 V | 0.000 | ผ่าน |
| RTH | 18.033 kΩ | 18.0328 kΩ | < 0.001 kΩ | ผ่าน |
| IB | 12.30 µA | 12.299 µA | 0.001 µA | ผ่าน |
| IC | 1.230 mA | 1.230 mA | 0.000 | ผ่าน |
| IE | 1.242 mA | 1.242 mA | 0.000 | ผ่าน |
| VE | 1.242 V | 1.242 V | 0.000 | ผ่าน |
| VB | 1.942 V | 1.942 V | 0.000 | ผ่าน |
| VC | 9.294 V | 9.294 V | 0.000 | ผ่าน |
| VCE | 8.052 V | 8.052 V | 0.000 | ผ่าน |

**สถานะ:** VCE = 8.052 V > 0.3 V → อยู่ในย่าน **Forward-Active** และไม่มี warning

## การตรวจสอบกรณีอื่น

| กรณี | ข้อมูลนำเข้า | ผลที่คาดหวัง | ผลจริง |
|---|---|---|---|
| Cutoff | VCC=5, R1=100k, R2=10k | VTH = 0.455 V ≤ VBE → กระแสเป็น 0, เตือน Cutoff | ตรง |
| Saturation | VCC=5, R1=100k, R2=47k, RC=10k | VCE ≤ 0.3 V → เตือน Saturation | ตรง |
| ค่าไม่ใช่ตัวเลข | vcc = `abc` | ข้อความ "ต้องเป็นตัวเลข" ไม่ล้ม | ตรง |
| ค่าตัวต้านทานเป็นศูนย์ | R1 = 0 | ข้อความ "R1 ต้องมากกว่า 0" | ตรง |
| ช่องว่างทั้งหมด | ไม่กรอกอะไรเลย | error ครบทุกช่อง, HTTP 200 | ตรง |
| หน่วย Ω แทน kΩ | r1=100000 Ω, r2=22000 Ω | ผลเหมือนกรอก 100/22 kΩ | ตรง |
| หน่วย mV | vbe=700 mV | เท่ากับ 0.70 V | ตรง |
| หน่วยไม่รู้จัก | r1_unit=`bogus` | ข้อความ "R1 หน่วยไม่ถูกต้อง" | ตรง |

## คำสั่งที่ใช้ตรวจ

```bash
python -m unittest discover -s tests -v
```

ผล: `Ran 25 tests ... OK`

```bash
python -m flask --app app run
```

แล้วเปิด <http://127.0.0.1:5000/> กรอกค่าตามตารางด้านบน กด **Calculate DC Bias**

## ข้อสรุป

โปรแกรมคำนวณตรงกับการคำนวณอิสระภายใต้แบบจำลอง Forward-Active เดียวกัน
ตัวเลขบนหน้าเว็บมาจาก Python Backend ทุกครั้ง ไม่ได้ฝังไว้ใน HTML

---

# Validation — Lab 03 (Fixed Bias และ Emitter Bias)

วันที่ตรวจ: 2026-11-17 (รอบแรก) · 2026-11-24 (ตรวจซ้ำ)
วิธีตรวจ: รอบแรกใช้ **OpenCode Browser** เพราะยังไม่มี Node.js — ภายหลังติดตั้ง Node.js และ
**Playwright MCP** แล้วจึงตรวจซ้ำ A1–A3 อีกครั้งในรอบ Lab 04
สภาพแวดล้อม: Flask 3.1.3 · Python 3.14.2 · `http://127.0.0.1:5000/`

## ค่าคงที่ร่วมของ A1–A5

| พารามิเตอร์ | ค่า |
|---|---|
| VCC | 12 V |
| RC | 2.2 kΩ |
| β | 100 |
| VBE | 0.70 V |

เกณฑ์ยอมรับ: `|ΔIC| ≤ 0.01 mA` และ `|ΔVCE| ≤ 0.02 V` เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ
หน้าเว็บแสดงแรงดัน 3 ตำแหน่งทศนิยม และกระแสเป็น mA/µA 3 ตำแหน่ง

## ค่าอ้างอิงอิสระของโหมดใหม่ (คำนวณมือ)

### A2 · Fixed Bias, RB = 1 MΩ

```
IB  = (12 − 0.70) / 1 000 000          = 11.30 µA
IC  = 100 × 11.30 µA                   = 1.130 mA
IE  = 101 × 11.30 µA                   = 1.141 mA
VE  = 0 V                              (emitter ต่อลงกราวด์โดยตรง)
VB  = 0 + 0.70                         = 0.700 V
VC  = 12 − (1.130 mA × 2.2 kΩ)         = 9.514 V
VCE = 9.514 − 0                        = 9.514 V
```

### A3 · Emitter Bias, RB = 1 MΩ, RE = 1 kΩ

```
IB  = (12 − 0.70) / (1 000 000 + 101 × 1 000)
    = 11.30 / 1 101 000                = 10.263 µA
IC  = 100 × 10.263 µA                  = 1.026 mA
IE  = 101 × 10.263 µA                  = 1.037 mA
VE  = 1.0366 mA × 1 kΩ                 = 1.037 V
VB  = 1.037 + 0.70                     = 1.737 V
VC  = 12 − (1.0263 mA × 2.2 kΩ)        = 9.742 V
VCE = 9.742 − 1.037                    = 8.705 V
```

### A4 · Emitter Bias, RE = 2 kΩ (เปลี่ยนค่าเดียวจาก A3)

```
IB  = 11.30 / (1 000 000 + 101 × 2 000)
    = 11.30 / 1 202 000                = 9.401 µA
IC  = 100 × 9.401 µA                   = 0.940 mA   (ลดลง 8.4 % จาก A3)
IE  = 101 × 9.401 µA                   = 0.950 mA
VE  = 0.9495 mA × 2 kΩ                 = 1.899 V
VC  = 12 − (0.9401 mA × 2.2 kΩ)        = 9.932 V
VCE = 9.932 − 1.899                    = 8.033 V
```

**ทำนายก่อนรัน:** RE ใหญ่ขึ้น → ตัวส่วน `RB + (β+1)RE` ใหญ่ขึ้น → IB และ IC ลดลง
**ผลจริง:** IC ลดจาก 1.026 mA เป็น 0.940 mA → ตรงกับที่ทำนาย

## ตาราง A1–A5 (ผลที่เห็นจริงจากหน้าเว็บ)

| กรณี | โหมด · ค่าที่กรอก | คาดหมาย | เห็นจริง | วิธีตรวจ | สถานะ |
|---|---|---|---|---|---|
| **A1** | Divider · R1=100 k, R2=22 k, RE=1 k | ผลเท่า Lab 02: IC 1.230 mA · VCE 8.052 V | IB 12.299 µA · IC **1.230 mA** · IE 1.242 mA · VB 1.942 V · VE 1.242 V · VC 9.294 V · VCE **8.052 V** | OpenCode Browser | **PASS** |
| **A2** | Fixed · RB=1 MΩ (ไม่กรอก RE) | IC 1.130 mA · VCE 9.514 V | IB 11.300 µA · IC **1.130 mA** · IE 1.141 mA · VB 0.700 V · VE 0.000 V · VC 9.514 V · VCE **9.514 V** | OpenCode Browser | **PASS** |
| **A3** | Emitter · RB=1 MΩ, RE=1 kΩ | IC 1.026 mA · VCE 8.705 V | IB 10.263 µA · IC **1.026 mA** · IE 1.037 mA · VB 1.737 V · VE 1.037 V · VC 9.742 V · VCE **8.705 V** | OpenCode Browser | **PASS** |
| **A4** | Emitter · เหมือน A3 แต่ RE=2 kΩ | IC ลดจาก A3 · VCE 8.033 V | IB 9.401 µA · IC **0.940 mA** · IE 0.950 mA · VB 2.599 V · VE 1.899 V · VC 9.932 V · VCE **8.033 V** | OpenCode Browser | **PASS** |
| **A5** | Fixed · RB=0 | มีข้อความให้แก้ RB เว็บไม่ล่ม ไม่โชว์ผลเดิม | ข้อความ `RB ต้องมากกว่า 0 (ได้รับ 0.0)` · ไม่มีตารางผล · HTTP 200 | OpenCode Browser | **PASS** |

**Playwright MCP:** รอบแรก `NOT RUN` (ไม่มี Node.js) — รอบ Lab 04 ตรวจซ้ำ A1–A3 สำเร็จแล้ว
ด้วย MCP Server จริง ดูตาราง B1 ในหัวข้อ Lab 04 ด้านล่าง

### หลักฐานจากหน้าเว็บ

- `docs/evidence/A4-emitter-re2k.jpeg` — หน้า Emitter Bias หลังเปลี่ยน RE เป็น 2 kΩ แสดง IC 0.940 mA / VCE 8.033 V
- `docs/evidence/A5-fixed-rb0.jpeg` — หน้า Fixed Bias เมื่อ RB = 0 แสดง error และไม่มีตารางผล

## การตรวจเพิ่มเติมนอกตาราง A1–A5

| สิ่งที่ตรวจ | ผล |
|---|---|
| Fixed bias ไม่ต้องกรอก RE | ผ่าน — ฟอร์มซ่อน RE และ Flask ไม่ตรวจช่องนี้ |
| โหมดที่ไม่รู้จัก (`mode=bogus`) | ผ่าน — ขึ้น `ไม่รู้จักโหมด 'bogus'` ไม่ fallback เป็น Divider |
| Thevenin equivalent แสดงเฉพาะ Divider | ผ่าน — Fixed/Emitter ซ่อน เพราะไม่มี VTH/RTH |
| หน่วย MΩ บนช่อง RB | ผ่าน — 1 MΩ ให้ผลเท่า 1000 kΩ |
| เปลี่ยนโหมดแล้วฟอร์มโหลดใหม่ | ผ่าน — `GET /?mode=fixed` แสดงเฉพาะช่องที่ใช้ |
| สลับโหมดด้วยการกดการ์ดครั้งเดียว | ผ่าน — กดการ์ด Emitter Bias แล้วไป `?mode=emitter` ทันที (ไม่มีปุ่มโหลดแยก) และการ์ดของโหมดปัจจุบันถูกไฮไลต์ + กดซ้ำไม่ได้ |
| ผลรอบก่อนไม่ค้างหลัง error | ผ่าน — A5 แสดง placeholder แทนตารางผล |

## ผล unittest

```bash
python -m unittest discover -s tests -v
# Ran 25 tests ... OK
```

ไม่ได้เพิ่ม test ใหม่ตามใบงาน Lab 03 (ตรวจผ่าน Browser)
test เดิมทั้ง 25 รายการยังผ่านทั้งหมด รวมถึง `test_post_calculates_reference_case` ที่ยืนยัน A1 = 8.052 V / 1.230 mA

## ข้อจำกัดของการตรวจสอบรอบนี้

- Browser tool ที่ใช้ไม่มี node ของ `input[type=number]` ใน accessibility snapshot
  จึงกรอกค่าผ่าน DOM evaluation แล้วส่งฟอร์มจริง (`requestSubmit`)
  การส่งยังเป็น HTTP POST จริงผ่านเบราว์เซอร์ และอ่านผลจากหน้าเว็บที่ render แล้ว
- ยังไม่ได้ตรวจด้วย Playwright MCP ตามเส้นทางหลักของใบงาน เพราะไม่มี Node.js บนเครื่องนี้

---

# Validation — Lab 04 (CE Amplifier Simulator)

วันที่ตรวจ: 2026-11-24
วิธีตรวจ: **Playwright MCP จริง** (`@playwright/mcp@latest`, Chrome headless, stdio) ·
`http://127.0.0.1:5000/` · viewport 1280×900 และ 390×844
สภาพแวดล้อม: Python 3.14.2 · Flask 3.1.3 · ngspice 47 (MSYS2 `mingw-w64-ucrt-x86_64-ngspice`) ·
`solver = C:\msys64\ucrt64\bin\ngspice.exe` · Node.js 22 · MCP server `Playwright 1.66.0-alpha`

**Playwright MCP:** `PASS` — initialize สำเร็จ (25 tools) และขับผ่าน `tools/call` จริง
ผลรอบแรกถูกแจ้งผู้ใช้ก่อนแก้ UI เพิ่มเติม จากนั้นรันรอบสุดท้ายอีกครั้งและเก็บ before/after screenshot
**หมายเหตุ:** MCP tools ไม่โผล่ใน tool catalog ของ session นี้ จึงขับ MCP server ตรงผ่าน stdio ด้วย helper
แต่ทุกค่าอ่านจากเบราว์เซอร์จริงที่โหลด Flask — ไม่ใช่ mock/hard-code

**โมเดลที่ใช้จริง:** `reference/provisional_2n3904.bjt` (`.model Q2N3904`)
สถานะ **PROVISIONAL — อาจารย์ไม่ได้แจกไฟล์ Starter Kit หรือโมเดล BJT ที่รับรองให้ ณ วันที่ส่งงาน**
จึงไม่มีการเลือก `Lab verified model` หรือ `Instructor Starter Kit file` และไม่กล่าวอ้างว่าโมเดลนี้ได้รับจากอาจารย์
หน้าเว็บแสดงป้าย `PROVISIONAL` ใกล้หัวข้อและปุ่ม Run รวมถึง
`Local reference model (not instructor-verified)` ในบรรทัด provenance ทุกครั้ง

> หมายเหตุการส่งงาน: ใบงานระบุให้ใช้โมเดลที่ Instructor Starter Kit กำหนด **ถ้าผู้สอนแจก**
> ในกรณีนี้ไม่มีไฟล์จากผู้สอน จึงใช้โมเดลอ้างอิงภายในโปรเจกต์และรายงานตามตรง
> ผล `.op/.ac/.tran` มาจาก ngspice จริงแต่ขึ้นกับ `Bf` และพารามิเตอร์ของโมเดลชั่วคราว
> เปรียบเทียบกับ Analytical Reference ได้ในฐานะ "คนละแบบจำลอง" ไม่ใช่การเทียบความถูกต้องตรง ๆ
> ถ้าได้รับโมเดลของอาจารย์ภายหลัง ให้แทนที่ไฟล์แล้วรัน B1–B8 ใหม่ก่อนอัปเดตคะแนน

## หลักการตรวจความถูกต้อง

- ค่าทั้งหมดมาจากการรัน `ngspice -b -o run.log -r run.raw circuit.cir` จริง ผ่าน `spice_engine.py`
- อ่านผลจาก **binary raw** (`.op`, complex `.ac`, real `.tran`) ไม่ได้อ่าน `.print` จาก log
- ตรวจว่า HTTP `POST /simulate` คืน 200 และหน้าเว็บ render กราฟ `<polyline>` จากข้อมูลรันนั้น
- เปรียบเทียบก่อน/หลังเมื่อเปลี่ยน RE และ Amplitude เพื่อยืนยันว่าไม่มีค่าหรือกราฟ hard-code
- หน้าเว็บแสดง log/netlist ได้ใน `<details>` เพื่อให้ตรวจ provenance ได้
- อ่าน status จริงสามชั้น: `RUNNING` ขณะ submit (probe จับ `aria-current=step`, `aria-busy=true`,
  ปุ่ม disabled) → `SUCCESS` หรือ `ERROR` หลัง render
- แยกตาราง **Analytical Reference (`dc_bias.py`)** ออกจาก **SPICE / ngspice** ในผลลัพธ์เดียวกัน
- ตรวจ Chrome console และ detector ของ Impeccable: console 0 error และ detector 0 finding ทั้งสอง viewport

## ตาราง B1–B8 (ผลที่เห็นจริงจากหน้าเว็บ)

| Case | Method (Playwright MCP) | Input | Expected / Reference | Observed (final run) | Evidence | Status |
|---|---|---|---|---|---|---|
| **B1** | `browser_navigate ?mode=fixed/emitter/divider` → `browser_fill_form` → `browser_click`Calculate | ค่า Lab 03 เดิม: VCC 12 V, RC 2.2 kΩ, β 100, VBE 0.7 V, RB 1 MΩ / R1 100 k, R2 22 k, RE 1 k | ผลเดิมตรง A1–A3 | Fixed: IC **1.130 mA**, VCE **9.514 V** · Emitter: IC **1.026 mA**, VCE **8.705 V** · Divider: IC **1.230 mA**, VCE **8.052 V** | rows ที่อ่านจาก DOM จริง | **PASS** |
| **B2** | `browser_select_option sanalysis=op` → Run ngspice | 12 V / 100 k / 22 k / 2.2 k / 1 k, β 150, VBE 0.7 V, local reference model | มี `SUCCESS`, engine/model, status และผล `.op` แยกจาก analytical | `SUCCESS · ngspice (version unknown) · Q2N3904 (Bf จาก .model) · Local reference model (not instructor-verified)`; **Analytical** VB 2.008 / VE 1.308 / VC 9.142 / VCE 7.834 V, IB 8.661 µA, IC 1.299 mA · **SPICE** VB 2.004 / VE 1.333 / VC 9.087 / VCE 7.754 V, IB 8.887 µA, IC 1.324 mA · `PROVISIONAL` แสดงใกล้หัวข้อ | `docs/evidence/playwright_final_results.json`, `docs/evidence/playwright_final_desktop.png` | **PASS** |
| **B3** | เปลี่ยนเฉพาะ `sre=2` แล้ว Run `.op` ซ้ำ | RE 1 kΩ → 2 kΩ (ค่าอื่นคงเดิม) | Operating point ต้องเปลี่ยน ไม่ใช่ค่าค้าง | Analytical เปลี่ยน IC 1.299 → **0.686 mA**, VC 9.142 → **10.490 V** · SPICE เปลี่ยน IC 1.324 → **0.704 mA**, VE 1.333 → **1.419 V**, VC 9.087 → **10.450 V**, IB 8.887 → **5.060 µA** | ผลก่อน/หลังจาก DOM จริง | **PASS** |
| **B4** | `sanalysis=all` → Run → อ่านตารางและ `svg.plot` | AC 1 Hz–10 MHz, 10 mV @ 1 kHz | แกน Frequency พร้อมหน่วย, Gain dB, Phase deg จากรันจริง | Midband gain **4.89 dB**, phase **179.99°** (อ้างอิงเฟสของ source; `.tran` ยืนยันกลับเฟส), fL **1.785 Hz**, fH `not determined in sweep range`; `<polyline>` **4** เส้น; แกน `Frequency (Hz, log10)` / `Gain (dB)` / `Phase (deg)` | `docs/evidence/playwright_final_results.json` | **PASS** |
| **B5** | อ่าน transient จากรัน B4 เดียวกัน | 10 mV peak @ 1 kHz, no bypass capacitor | เห็น Vin/Vout ตามเวลา มีป้ายเวลา/แรงดัน และสัญญาณกลับเฟส | Vin pp **20.00 mV**, Vout pp **35.12 mV**, \|Vout/Vin\| **1.756**, `Phase: Inverted (≈180°)`; แกน `Time (ms)` / `Voltage (V)`, legend `Vin`, `Vout` | `docs/evidence/playwright_final_desktop.png` | **PASS** |
| **B6** | เปลี่ยน `sampl=20` แล้ว Run ซ้ำ | Amplitude 20 mV, ความถี่ 1 kHz, ค่าอื่นคงเดิม | Waveform ต้องเปลี่ยนตามค่า ไม่ใช่กราฟ hard-code | Vin pp 20.00 → **40.00 mV**, Vout pp 35.12 → **70.23 mV**, gain ยัง **1.756** → ขยาย 2× ตามอินพุต | ผลก่อน/หลังจาก DOM จริง | **PASS** |
| **B7** | ใส่ `sre=0` แล้ว Run | `sre=0` | แจ้ง error ภาษาไทย ไม่ค้าง ไม่โชว์ผลสำเร็จปลอม | `data-state="ERROR"`, `ERROR`, `กรุณาแก้ไขค่าที่ไม่ถูกต้อง (1 รายการ)`, `RE ต้องมากกว่า 0`; ไม่มี badge SUCCESS ไม่มี `<polyline>` | `docs/evidence/playwright_final_results.json` | **PASS** |
| **B8** | `browser_resize 390x844` → `browser_navigate` → วัด `getBoundingClientRect` | viewport จริง 390 CSS px ไม่ใช่ iframe | ปุ่ม/หน่วย/กราฟอ่านได้ ไม่ตัดเนื้อหาสำคัญ | `innerWidth=390`, `.lab04__layout` เป็น 1 คอลัมน์ `362px`, ปุ่ม/กราฟทุกตัว `right <= innerWidth + 1`, สลับโหมดและ Run สำเร็จ | `docs/evidence/playwright_final_mobile.png` | **PASS** |

### หลักฐานเสริมจาก Playwright MCP

| สิ่งที่ตรวจ | ผลจริง |
|---|---|
| `RUNNING` feedback | ขณะ submit พบ `state=RUNNING`, `label=RUNNING`, `aria-current=step`, `aria-busy=true`, `button.disabled=true`; หลัง render เป็น `SUCCESS` |
| Chrome console | `Total messages: 0 (Errors: 0, Warnings: 0)` หลังเพิ่ม `<link rel="icon" href="data:,">` |
| Duplicate IDs / Jinja ค้าง | ไม่พบใน desktop และ mobile |
| Impeccable detect | exit `0`, `[]` ที่ 1280×900 และ 390×844 (หลังแก้ contrast/hint/straggler) |
| Results provenance | ตาราง Analytical มีป้าย `dc_bias.py` + คำอธิบาย β/VBE คงที่; ตาราง SPICE อยู่ใต้ divider `SPICE / ngspice` และมี log/netlist ใน `<details>` |

### ภาพหน้าจอ before / after (Playwright MCP จริง)

| ไฟล์ | รอบ | viewport |
|---|---|---|
| `docs/evidence/playwright_initial_desktop.png` | ก่อนแก้ Impeccable P1/P2 | 1280×900 |
| `docs/evidence/playwright_initial_mobile.png` | ก่อนแก้ Impeccable P1/P2 | 390×844 |
| `docs/evidence/playwright_final_desktop.png` | หลังแก้ status/analytical/PROVISIONAL/hint/focus | 1280×900 |
| `docs/evidence/playwright_final_mobile.png` | หลังแก้ status/analytical/PROVISIONAL/hint/focus | 390×844 |
| `docs/evidence/playwright_initial_results.json` | ผล B1–B8 รอบแรก (ก่อนแก้) | — |
| `docs/evidence/playwright_final_results.json` | ผล B1–B8 รอบสุดท้าย | — |

## ผล unittest รอบ Lab 04

```bash
.venv\Scripts\python -m unittest discover -s tests -v
# Ran 51 tests ... OK
```

แยกเป็น: 25 test เดิมของ Lab 03 ยังผ่าน + 20 test เดิมของ Lab 04 (`spice_engine.py` และ `/simulate`)
+ 6 test ใหม่สำหรับ status hook, `RUNNING` script, SUCCESS/ERROR, engine failure และ analytical reference

## รอบ Impeccable critique → polish → audit

- Critique แบบ dual-agent ได้ **24/40** และแจ้งผู้ใช้ก่อนแก้ UI
  snapshot: `.impeccable/critique/2026-11-24T11-22-51Z__templates-index-html.md`
- P1 ที่แก้แล้ว: `RUNNING → SUCCESS/ERROR` + ปุ่ม disabled, ตาราง Analytical แยกจาก SPICE,
  ป้าย PROVISIONAL ย้ายขึ้นใกล้หัวข้อและปุ่ม Run
- P2 ที่แก้แล้ว: hint เป็นภาษามนุษย์ (`Source Amplitude`, `Analytical VBE` ...),
  `.goal` เปลี่ยนจาก assignment-speak เป็น “ภาพรวมการใช้งาน”, focus ring ใช้ `:focus-visible`
  แทนการซ่อนด้วย `outline: none`, favicon 404 หายไป
- ตรวจซ้ำด้วย detector ที่ 1280×900 และ 390×844: `[]` ทั้งสองรอบ
- Audit รอบสุดท้ายได้ **17/20 (Good)** — P0/P1 = 0, P2 = 3, P3 = 1
  report: `.impeccable/audit/2026-11-24T11-42-22Z__project.md`
- เนื่องจากแก้ `templates/index.html` หลัง critique ทำให้ fingerprint เปลี่ยน จึงไม่ปิด snapshot เดิม
  (ตามกติกา polish) และใช้ผล detect/browser รอบสุดท้ายเป็นหลักฐานแทน

## ความคลาดเคลื่อน / ข้อจำกัดที่ยังรู้

- หน้าเว็บแสดง `ngspice (version unknown)` เพราะ log แบบ `-b -o` ไม่พบบรรทัด banner เวอร์ชัน
  แต่ binary ที่รันจริงคือ ngspice 47 จาก MSYS2 ucrt64 (ตรวจจาก package และ header ของ executable)
- Phase ของ AC ที่ความถี่ midband ออกมา **+179.99°** ไม่ใช่ −180° เนื่องจากทิศทางอ้างอิงเฟสของ AC source
  ความหมายทางฟิสิกส์เหมือนกัน และ `.tran` ยืนยัน `Inverted` แล้ว
- fH อยู่นอกช่วง sweep 1 Hz–10 MHz จึงแสดง `not determined in sweep range` ตามตรง ไม่ได้สร้างตัวเลขขึ้นเอง
- ผล DC SPICE ต่างจากผล Forward-Active Approximation ของ Lab 03 เพราะคนละแบบจำลอง (SPICE ใช้ Bf ของโมเดล)
- อาจารย์ไม่ได้แจก Starter Kit / โมเดลที่รับรองให้ ณ วันที่ส่งงาน ผลทั้งหมดจึงเป็น **PROVISIONAL**
  และต้องเปลี่ยนโมเดล + รัน B1–B8 ใหม่เฉพาะเมื่อได้รับไฟล์จากอาจารย์ภายหลัง

