"""DC bias calculation for an NPN common-emitter amplifier.

Voltage-divider bias, forward-active approximation with constant beta and
constant VBE.

All quantities are in SI base units: volts, amperes, ohms. The web layer is
responsible for converting kilo-ohms from the form before calling here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BiasResult:
    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]


def _require_positive(name: str, value: float) -> None:
    if not value > 0:
        raise ValueError(f"{name} ต้องมากกว่า 0 (ได้รับ {value})")


def calculate_dc_bias(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> BiasResult:
    """Return the DC operating point of a voltage-divider biased NPN stage."""
    _require_positive("VCC", vcc)
    _require_positive("R1", r1)
    _require_positive("R2", r2)
    _require_positive("RC", rc)
    _require_positive("RE", re)
    _require_positive("beta", beta)
    if not vbe >= 0:
        raise ValueError(f"VBE ต้องไม่ติดลบ (ได้รับ {vbe})")

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    # Cutoff: the divider cannot forward-bias the base-emitter junction.
    if vth <= vbe + 1e-9:
        return BiasResult(
            vth=vth,
            rth=rth,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vth,
            ve=0.0,
            vc=vcc,
            vce=vcc,
            region="cutoff",
            warnings=(
                f"Cutoff: VTH = {vth:.3f} V ≤ VBE = {vbe:.2f} V — "
                "ทรานซิสเตอร์ไม่นำกระแส และแบบจำลอง forward-active ใช้ไม่ได้",
            ),
        )

    ib = (vth - vbe) / (rth + (beta + 1.0) * re)
    ic = beta * ib
    ie = (beta + 1.0) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    if vce <= 0.3:
        region = "saturation"
        warnings = (
            f"Saturation: VCE = {vce:.3f} V ≤ 0.3 V — "
            "จุดทำงานอยู่ใกล้หรือเกินย่านอิ่มตัว ค่า IC จากแบบจำลอง forward-active "
            "ไม่ใช่ค่าที่เชื่อถือได้",
        )
    else:
        region = "active"
        warnings = ()

    return BiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )
