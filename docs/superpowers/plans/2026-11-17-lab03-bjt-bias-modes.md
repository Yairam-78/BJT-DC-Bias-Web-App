# Lab 03 — BJT DC Bias Web App · Implementation Plan

วันที่: 2026-11-17
สถานะ: อนุมัติแล้ว (ผู้ใช้ยืนยัน 3 ข้อตัดสิน)
ต่อยอดจาก: `docs/superpowers/plans/2026-11-10-lab02-dc-bias.md`

**Goal:** เพิ่ม Fixed Bias และ Emitter Bias แบบแหล่งจ่ายเดียวในเว็บ Flask เดิม
โดยผลของ Voltage Divider ต้องคงเดิมทุกค่า

**Architecture:** คงเดิม — `dc_bias.py` pure Python หน่วย SI, `app.py` parse/แปลงหน่วย/dispatch,
`templates/index.html` แสดงผลอย่างเดียว ไม่มีสมการ

## ข้อตัดสินใจ

| # | เรื่อง | ข้อสรุป | เหตุผล |
|---|---|---|---|
| D1 | รูปแบบผลลัพธ์ | คง `BiasResult` dataclass + เพิ่ม `as_dict()` | เปลี่ยนเป็น dict ล้วนจะทำให้ test เดิม 12 รายการพัง (attribute access) |
| D2 |  threshold เตือน Saturation | คง `VCE ≤ 0.3 V` ทุกโหมด | ตรงกับ docs/README ของ Lab 02 และเข้มกว่าเกณฑ์ 0.2 V ในใบงาน |
| D3 | unittest ใหม่ | ไม่เพิ่ม | ใบงาน Lab 03 ระบุให้ตรวจผ่าน Browser (ขัดกับ AGENTS.md ที่บังคับ TDD — บันทึกไว้) |
| D4 | วงจรในหน้าเว็บ | Divider ใช้ SVG เดิม, Fixed/Emitter ใช้การ์ดข้อความ | เร็วและไม่เพิ่มโค้ดวาดภาพที่ไม่ได้คะแนน |

## Global Constraints

- `dc_bias.py` ห้าม import flask/jinja และห้ามรู้จัก kΩ/MΩ
- แปลงหน่วยครั้งเดียวที่ `app.py::_read_values`
- ข้อความ error/warning เป็นภาษาไทย ระบุช่องที่ผิด
- error ทั้งหมดคืน HTTP 200
- ห้ามแตะ `tests/` เดิม — 25 tests ต้องเขียวตลอด
- ห้ามฮาร์ดโค้ดผลลัพธ์หรือสมการใน template

## Tasks

### Task 1 · `dc_bias.py` — เพิ่มสองโฟลว์บายแอส
- [x] `calculate_fixed_bias(vcc, rb, rc, beta, vbe)`
- [x] `calculate_emitter_bias(vcc, rb, rc, re, beta, vbe)`
- [x] `_operating_point()` ใช้ร่วมกัน (Fixed ส่ง `re=0` → VE = 0)
- [x] `BiasResult.vth/rth` เป็น `float | None`
- [x] `BiasResult.as_dict()` คีย์มีหน่วย (`vb_v`, `ic_a`, …)
- [x] คงตรรกะ Divider เดิมทุกบรรทัด

### Task 2 · `app.py` — เลือกฟังก์ชันและตรวจอินพุตตามโหมด
- [x] `MODES` เก็บ label + field list ต่อโหมด
- [x] `BIAS_FUNCTIONS` dispatch
- [x] `_read_mode()` — โหมดไม่รู้จัก = error ไม่ fallback
- [x] `_read_form()` แยกจาก `_read_values()` เพื่อคงค่าที่พิมพ์ไว้ตอนสลับโหมด
- [x] `GET /?mode=` รองรับการโหลดฟอร์มใหม่

### Task 3 · `templates/index.html` + `static/style.css`
- [x] ฟอร์มเลือกโหมด (GET) + hidden `mode` ในฟอร์ม POST
- [x] แสดงเฉพาะช่องของโหมด (`mode_fields`)
- [x] ช่อง `rb` + label
- [x] Thevenin แสดงเฉพาะ Divider
- [x] การ์ดวงจรแบบข้อความสำหรับ Fixed/Emitter
- [x] หัวผลระบุโหมด

### Task 4 · เอกสารและ config
- [x] `docs/validation.md` — ค่าอ้างอิงมือ A2–A4 + ตาราง A1–A5
- [x] `docs/evidence/` — ภาพหน้าจอ A4, A5
- [x] `README.md` — 3 โหมด, สมการ, หน่วย, MCP
- [x] `opencode.json` — Playwright MCP (V2)

## Verification

| เกณฑ์ | ผล |
|---|---|
| `python -m unittest discover -s tests -v` | 25/25 OK |
| A1 เท่า Lab 02 | IC 1.230 mA · VCE 8.052 V |
| A2 Fixed RB=1 MΩ | IC 1.130 mA · VCE 9.514 V |
| A3 Emitter RB=1 MΩ, RE=1 kΩ | IC 1.026 mA · VCE 8.705 V |
| A4 Emitter RE=2 kΩ | IC 0.940 mA (ลดลง) · VCE 8.033 V |
| A5 Fixed RB=0 | error `RB ต้องมากกว่า 0` ไม่มีตารางผล |

## ยังไม่ทำ (นอกขอบเขต / ติดข้อจำกัด)

- Playwright MCP รันจริง — เครื่องไม่มี Node.js (บันทึก `NOT RUN`)
- git commit/push — เครื่องไม่มี git/GitHub Desktop
- Skill `browser-acceptance-check` — ยังไม่ติดตั้งในโปรเจกต์
