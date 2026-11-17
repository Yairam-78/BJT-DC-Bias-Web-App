"""DC bias calculation for NPN common-emitter stages.

Three bias topologies share one forward-active approximation with constant
beta and constant VBE:

* voltage-divider bias — :func:`calculate_dc_bias`
* fixed bias — :func:`calculate_fixed_bias`
* emitter bias from a single supply — :func:`calculate_emitter_bias`

All quantities are in SI base units: volts, amperes, ohms. The web layer is
responsible for converting kilo-ohms from the form before calling here.
"""

import math
from dataclasses import dataclass

# The forward-active approximation stops being trustworthy near the knee.
# Lab 02 documented 0.3 V, so every topology keeps the same limit.
SATURATION_LIMIT_V = 0.3

# VTH <= VBE + tiny slack is treated as cutoff so that the boundary case
# (VTH exactly equal to VBE) does not produce a zero or negative base current.
CUTOFF_SLACK_V = 1e-9


@dataclass(frozen=True)
class BiasResult:
    vth: float | None
    rth: float | None
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]
    mode: str = "divider"

    def as_dict(self) -> dict[str, object]:
        """Return the same values as a dict whose keys carry their unit.

        Keys stay in SI units because the module never knows about the units
        chosen on the form; ``rth_ohm`` is ``None`` for topologies that have
        no Thevenin equivalent.
        """
        return {
            "mode": self.mode,
            "vth_v": self.vth,
            "rth_ohm": self.rth,
            "ib_a": self.ib,
            "ic_a": self.ic,
            "ie_a": self.ie,
            "vb_v": self.vb,
            "ve_v": self.ve,
            "vc_v": self.vc,
            "vce_v": self.vce,
            "region": self.region,
            "warnings": list(self.warnings),
        }


def _require_positive(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} ต้องเป็นจำนวนจำกัด (ได้รับ {value})")
    if value <= 0:
        raise ValueError(f"{name} ต้องมากกว่า 0 (ได้รับ {value})")


def _require_vbe(vbe: float) -> None:
    if not math.isfinite(vbe):
        raise ValueError(f"VBE ต้องเป็นจำนวนจำกัด (ได้รับ {vbe})")
    if vbe < 0:
        raise ValueError(f"VBE ต้องไม่ติดลบ (ได้รับ {vbe})")


def _operating_point(
    *,
    mode: str,
    vcc: float,
    rc: float,
    re: float,
    vbe: float,
    beta: float,
    ib: float,
    vth: float | None = None,
    rth: float | None = None,
) -> BiasResult:
    """Turn a base current into the full operating point.

    Fixed bias passes ``re=0`` so that VE is exactly 0 V without a special
    branch; the arithmetic then matches the handout formula.
    """
    ic = beta * ib
    ie = (beta + 1.0) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    outputs = (ib, ic, ie, vb, ve, vc, vce)
    if not all(math.isfinite(value) for value in outputs):
        raise ValueError(
            "ผลลัพธ์ไม่ใช่จำนวนจำกัด — ค่าอุปกรณ์อยู่นอกขอบเขตที่โปรแกรมคำนวณได้"
        )

    if vce <= SATURATION_LIMIT_V:
        region = "saturation"
        warnings = (
            f"Saturation: VCE = {vce:.3f} V ≤ {SATURATION_LIMIT_V:.1f} V — "
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
        mode=mode,
    )


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
    _require_vbe(vbe)

    # Written to stay finite when the resistors are extremely large:
    # vcc * r2 overflows before the division for r2 near 1e308.
    vth = vcc / (1.0 + r1 / r2)
    rth = 1.0 / (1.0 / r1 + 1.0 / r2)

    # Cutoff: the divider cannot forward-bias the base-emitter junction.
    if vth <= vbe + CUTOFF_SLACK_V:
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
            mode="divider",
        )

    ib = (vth - vbe) / (rth + (beta + 1.0) * re)
    return _operating_point(
        mode="divider",
        vcc=vcc,
        rc=rc,
        re=re,
        vbe=vbe,
        beta=beta,
        ib=ib,
        vth=vth,
        rth=rth,
    )


def calculate_fixed_bias(
    vcc: float,
    rb: float,
    rc: float,
    beta: float,
    vbe: float,
) -> BiasResult:
    """Return the DC operating point of a fixed-biased NPN stage.

    RB feeds the base from VCC and the emitter sits on ground, so VE is 0 V
    and only RB, RC and the transistor parameters affect the operating point.
    """
    _require_positive("VCC", vcc)
    _require_positive("RB", rb)
    _require_positive("RC", rc)
    _require_positive("beta", beta)
    _require_vbe(vbe)

    # Nothing can pull the base above VCC, so a supply at or below VBE leaves
    # the junction off and the forward-active model does not apply.
    if vcc <= vbe + CUTOFF_SLACK_V:
        return BiasResult(
            vth=None,
            rth=None,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vcc,
            ve=0.0,
            vc=vcc,
            vce=vcc,
            region="cutoff",
            warnings=(
                f"Cutoff: VCC = {vcc:.3f} V ≤ VBE = {vbe:.2f} V — "
                "ทรานซิสเตอร์ไม่นำกระแส และแบบจำลอง forward-active ใช้ไม่ได้",
            ),
            mode="fixed",
        )

    ib = (vcc - vbe) / rb
    return _operating_point(
        mode="fixed",
        vcc=vcc,
        rc=rc,
        re=0.0,
        vbe=vbe,
        beta=beta,
        ib=ib,
    )


def calculate_emitter_bias(
    vcc: float,
    rb: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> BiasResult:
    """Return the DC operating point of a single-supply emitter-biased stage.

    RB feeds the base from VCC and RE returns the emitter to ground, so the
    base loop sees ``RB + (beta + 1) * RE`` and RE stabilises the bias point.
    """
    _require_positive("VCC", vcc)
    _require_positive("RB", rb)
    _require_positive("RC", rc)
    _require_positive("RE", re)
    _require_positive("beta", beta)
    _require_vbe(vbe)

    if vcc <= vbe + CUTOFF_SLACK_V:
        return BiasResult(
            vth=None,
            rth=None,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vcc,
            ve=0.0,
            vc=vcc,
            vce=vcc,
            region="cutoff",
            warnings=(
                f"Cutoff: VCC = {vcc:.3f} V ≤ VBE = {vbe:.2f} V — "
                "ทรานซิสเตอร์ไม่นำกระแส และแบบจำลอง forward-active ใช้ไม่ได้",
            ),
            mode="emitter",
        )

    ib = (vcc - vbe) / (rb + (beta + 1.0) * re)
    return _operating_point(
        mode="emitter",
        vcc=vcc,
        rc=rc,
        re=re,
        vbe=vbe,
        beta=beta,
        ib=ib,
    )
