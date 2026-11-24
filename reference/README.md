# Lab 04 reference fixture (PROVISIONAL)

โฟลเดอร์นี้คือ **starter แบบชั่วคราว** ที่เตรียมไว้ให้โค้ด Lab 04 รันได้ก่อนที่อาจารย์จะแจก Starter Kit จริง

## สถานะ

| ไฟล์ | สถานะ |
|---|---|
| `ce_divider.cir` | วงจร CE Voltage Divider ตามค่าที่กำหนดในใบงาน (VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, Cin=Cout=10 µF, source 10 mV peak / 1 kHz) |
| `provisional_2n3904.bjt` | **PROVISIONAL** — โมเดล 2N3904 ที่พบได้ทั่วไป ยังไม่ผ่านการยืนยันจากอาจารย์ |

> ห้ามส่งงานโดยระบุว่านี่คือหม้อแปลง/โมเดลที่อาจารย์รับรอง ให้บันทึกใน `docs/validation.md` ว่าใช้โมเดลใดและรอการแทนที่

## รันด้วยมือเพื่อตรวจเครื่อง

```powershell
ngspice -b -o reference\run.log -r reference\run.raw reference\ce_divider.cir
```

สิ่งที่ต้องตรวจหลังรัน:

1. ไม่มี `Error` / `Warning: ...` ใน `run.log`
2. มีค่าจาก `.print dc` — `v(b)`, `v(e)`, `v(c)`, `v(c)-v(e)`, `i(rc)`
3. มีค่าจาก `.print ac` — `vdb(out)-vdb(in)`, `vp(out)-vp(in)` ตามความถี่
4. มีค่าจาก `.print tran` — `v(in)`, `v(out)` ตามเวลา
5. `run.raw` ถูกสร้างจริง (ใช้เป็นแหล่งข้อมูลกราฟ ไม่ใช่กราฟที่วาดจากค่าคงที่)

## เมื่อได้ Starter Kit จริง

1. เปลี่ยนบรรทัด `.include provisional_2n3904.bjt` ใน `ce_divider.cir` ให้ชี้ไปโมเดลที่อาจารย์ให้
2. อัปเดตชื่อโมเดลที่บรรทัด `Q1 c b e <MODEL_NAME>`
3. บันทึกเวอร์ชัน ngspice, ชื่อโมเดล และผลที่เปลี่ยนไปใน `docs/validation.md`
4. ถ้า netlist ของอาจารย์มี `.control ... .endc` ให้ทดสอบกับ `-b -o -r` ก่อนนำมาใช้ (ใบงานเตือนเรื่องนี้)
