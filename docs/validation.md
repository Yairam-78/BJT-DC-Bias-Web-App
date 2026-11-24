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

วันที่ตรวจ: 2026-11-17
วิธีตรวจ: **OpenCode Browser** (เบราว์เซอร์จริงบนเครื่องนี้) — ไม่ได้ใช้ Playwright MCP
เพราะเครื่องที่ตรวจยังไม่มี Node.js (บันทึกเป็น `NOT RUN` ตามใบงาน)
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

**Playwright MCP:** `NOT RUN` — เครื่องที่ตรวจไม่มี Node.js (`node --version` ไม่พบ) จึงรัน MCP Server ไม่ได้

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
วิธีตรวจ: **OpenCode Browser** (เบราว์เซอร์จริงที่เชื่อมกับ session นี้) · `http://127.0.0.1:5000/`
สภาพแวดล้อม: Python 3.14.2 · Flask 3.1.3 · ngspice 47 (MSYS2 `mingw-w64-ucrt-x86_64-ngspice`) ·
`solver = C:\msys64\ucrt64\bin\ngspice.exe`

**Playwright MCP:** `NOT RUN` — แม้ตอนนี้จะติดตั้ง Node.js แล้ว แต่ยังไม่ได้ตั้งค่า/ยืนยัน MCP server
ตามเส้นทางของใบงาน ผู้ตรวจเลือกใช้ OpenCode Browser ตามที่ตกลงกัน จึงไม่กล่าวอ้างว่าเป็นผล Playwright MCP

**โมเดลที่ใช้จริง:** `reference/provisional_2n3904.bjt` (`.model Q2N3904`)
สถานะ **PROVISIONAL — ยังไม่ใช่ Starter Kit / โมเดลที่อาจารย์รับรอง**
หน้าเว็บแสดงป้าย `Local reference model (not instructor-verified)` ทุกครั้ง

## หลักการตรวจความถูกต้อง

- ค่าทั้งหมดมาจากการรัน `ngspice -b -o run.log -r run.raw circuit.cir` จริง ผ่าน `spice_engine.py`
- อ่านผลจาก **binary raw** (`.op`, complex `.ac`, real `.tran`) ไม่ได้อ่าน `.print` จาก log
- ตรวจว่า HTTP `POST /simulate` คืน 200 และหน้าเว็บ render กราฟ `<polyline>` จากข้อมูลรันนั้น
- เปรียบเทียบก่อน/หลังเมื่อเปลี่ยน RE และ Amplitude เพื่อยืนยันว่าไม่มีค่าหรือกราฟ hard-code
- หน้าเว็บแสดง log/netlist ได้ใน `<details>` เพื่อให้ตรวจ provenance ได้

## ตาราง B1–B8 (ผลที่เห็นจริงจากหน้าเว็บ)

| Case | Method | Input | Expected / Reference | Observed | Evidence | Status |
|---|---|---|---|---|---|---|
| **B1** | OpenCode Browser · กดการ์ด Fixed → Emitter → Divider แล้วกด Calculate | ค่า Lab 03 เดิม: VCC 12 V, RC 2.2 kΩ, β 100, VBE 0.7 V, RB 1 MΩ / R1 100 k, R2 22 k, RE 1 k | ผลเดิมตรง A1–A3 ใน validation เดิม | Fixed: IC 1.130 mA, VCE 9.514 V · Emitter: IC 1.026 mA, VCE 8.705 V · Divider: IC 1.230 mA, VCE 8.052 V | ข้อความที่อ่านจากหน้าเว็บ + `docs/validation.md` ชุด A1–A3 | **PASS** |
| **B2** | เลือก Analysis `.op only` → Run ngspice | 12 V / 100 k / 22 k / 2.2 k / 1 k, model local reference | มี `RUN OK`, model, status และ VB/VE/VC/VCE/IC จาก ngspice | `RUN OK · Local reference model (not instructor-verified) · Q2N3904`; VB 2.004 V · VE 1.333 V · VC 9.087 V · VCE 7.754 V · IB 8.887 µA · IC 1.324 mA · IE 1.333 mA · Forward-active | หน้า Simulation Results + log/netlist ใน `<details>` | **PASS** |
| **B3** | เปลี่ยนเฉพาะ RE แล้ว Run `.op` ซ้ำ | RE 1 kΩ → 2 kΩ (ค่าอื่นคงเดิม) | Operating point ต้องเปลี่ยน ไม่ใช่ค่าค้าง | ก่อน: VE 1.333 V, VC 9.087 V, IC 1.324 mA · หลัง: VE 1.419 V, VC 10.450 V, IC 0.704 mA, IB 5.060 µA | ผลก่อน/หลังจากหน้าเว็บ | **PASS** |
| **B4** | เลือก Analysis `.op + .ac + .tran` → Run → อ่านกราฟ Bode | AC 1 Hz–10 MHz, 10 mV @ 1 kHz | แกน Frequency พร้อมหน่วย, Gain dB, Phase deg จากรันจริง | Midband gain **4.89 dB**, phase **179.99°** (เทียบเท่า ≈ −180°, CE กลับเฟส), fL **1.785 Hz**, fH `not determined in sweep range`; กราฟ 2 รูปมีแกน `Frequency (Hz, log10)` / `Gain (dB)` / `Phase (deg)` | DOM: `svg.plot` มี `<polyline>` จริง 3 รูป + `POST /simulate` status 200 | **PASS** |
| **B5** | อ่านกราฟ transient จากรันเดียวกัน | 10 mV peak @ 1 kHz, no bypass capacitor | เห็น Vin/Vout ตามเวลา มีป้ายเวลา/แรงดัน และสัญญาณกลับเฟส | Vin pp **20.00 mV**, Vout pp **35.12 mV**, \|Vout/Vin\| **1.756**, `Phase: Inverted (≈180°)`; แกน `Time (ms)` / `Voltage (V)`, legend `Vin`, `Vout`, polyline 2 เส้น | `docs/evidence/desktop_lab04.png` + ข้อความจากหน้าเว็บ | **PASS** |
| **B6** | เปลี่ยน Amplitude 10 → 20 mV แล้ว Run ซ้ำ | Amplitude 20 mV, ความถี่ 1 kHz, ค่าอื่นคงเดิม | Waveform ต้องเปลี่ยนตามค่า ไม่ใช่กราฟ hard-code | Vin pp 20.00 → **40.00 mV**, Vout pp 35.12 → **70.23 mV**, gain ยัง ≈ **1.756** → waveform ขยาย 2× ตามค่าที่ป้อน | ผลก่อน/หลังจากหน้าเว็บ | **PASS** |
| **B7** | ใส่ RE = 0 แล้ว Run | `sre=0` | แจ้ง error เป็นภาษาไทย ไม่ค้าง ไม่โชว์ผลสำเร็จปลอม | ข้อความ `RE ต้องมากกว่า 0` + `กรุณาแก้ไขค่าที่ไม่ถูกต้อง (1 รายการ)`; ไม่มี `RUN OK`, ไม่มี `<polyline>` | `docs/evidence/error_re_zero.png` | **PASS** |
| **B8** | UI | เปิดหน้าเว็บจริงแบบ desktop และแบบ viewport กว้าง 390 px (iframe ในเบราว์เซอร์จริง) แล้วสลับโหมด | ปุ่ม/หน่วย/กราฟอ่านได้ ไม่ตัดเนื้อหาสำคัญ | Desktop: layout 2 คอลัมน์, กราฟ 3 รูปแสดงครบ · 390 px: `matchMedia('(max-width: 1080px)')` และ `(max-width: 560px)` = true, `.lab04__layout` เป็น 1 คอลัมน์ (347 px), สลับไป Fixed Bias สำเร็จ, Run ngspice สำเร็จและมีกราฟ 3 รูป | `docs/evidence/desktop_lab04.png`, `docs/evidence/mobile_lab04.png`, `docs/evidence/mobile_frame.html` | **PASS** |

> หมายเหตุ B8: OpenCode Browser ไม่มีเครื่องมือปรับ viewport โดยตรง จึงใช้หน้า `mobile_frame.html`
> ที่ฝังแอปใน `<iframe width=390>` — iframe มี viewport จริง 390 CSS px และ media query ทำงานจริง
> จึงไม่ใช่แค่การย่อภาพ screenshot

## ผล unittest รอบ Lab 04

```bash
python -m unittest discover -s tests -v
# Ran 45 tests ... OK
```

แยกเป็น: 25 test เดิมของ Lab 03 ยังผ่าน + 20 test ใหม่สำหรับ `spice_engine.py` และ `/simulate`
(ในจำนวนนี้มี 2 test ที่ครอบ `resolve_ngspice()` fallback)

## ความคลาดเคลื่อน / ข้อจำกัดที่ยังรู้

- หน้าเว็บแสดง `ngspice (version unknown)` เพราะ log แบบ `-b -o` ไม่พบบรรทัด banner เวอร์ชัน
  แต่ binary ที่รันจริงคือ ngspice 47 จาก MSYS2 ucrt64 (ตรวจจาก package และ header ของ executable)
- Phase ของ AC ที่ความถี่ midband ออกมา **+179.99°** ไม่ใช่ −180° เนื่องจากทิศทางอ้างอิงเฟสของ AC source
  ความหมายทางฟิสิกส์เหมือนกัน และ `.tran` ยืนยัน `Inverted` แล้ว
- fH อยู่นอกช่วง sweep 1 Hz–10 MHz จึงแสดง `not determined in sweep range` ตามตรง ไม่ได้สร้างตัวเลขขึ้นเอง
- ผล DC SPICE ต่างจากผล Forward-Active Approximation ของ Lab 03 เพราะคนละแบบจำลอง (SPICE ใช้ Bf ของโมเดล)
- ยังไม่มี Starter Kit / โมเดลที่อาจารย์รับรอง ผลทั้งหมดจึงเป็น **PROVISIONAL** และต้องเปลี่ยนโมเดลก่อนส่งคะแนนจริง

