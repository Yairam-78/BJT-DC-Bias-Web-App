"""ngspice adapter for the Lab 04 CE amplifier simulator.

This module owns everything that talks to the solver: validation of the SI
values, netlist generation, the external process call, binary raw parsing and
the derivation of engineering metrics. It has no Flask dependency and knows
nothing about HTML forms.
"""

from __future__ import annotations

import html
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
NGSPICE_BIN = os.environ.get("NGSPICE_BIN", "ngspice")
NGSPICE_FALLBACKS = (
    r"C:\msys64\ucrt64\bin\ngspice.exe",
    r"C:\msys64\mingw64\bin\ngspice.exe",
)
RUN_TIMEOUT_SECONDS = 30
MAX_MODEL_BYTES = 1_000_000

ANALYSES = ("op", "ac", "tran", "all")
SOURCES = ("ac_sine", "dc_pulse")
MODEL_SOURCES = ("lab_reference", "local_reference", "starter_kit")


class SimulationError(Exception):
    """A solver or setup failure that is safe to show to the user."""


@dataclass(frozen=True)
class SimulationInput:
    """Validated SI inputs for one CE voltage-divider run."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    cin: float
    cout: float
    amplitude: float
    frequency: float
    source: str = "ac_sine"
    analysis: str = "all"
    model_source: str = "local_reference"
    model_path: str = ""
    model_name: str = ""
    beta: float | None = None


@dataclass(frozen=True)
class Plot:
    """One plot section from an ngspice binary raw file."""

    title: str
    variables: tuple[str, ...]
    flags: str
    values: tuple[tuple[complex | float, ...], ...]


@dataclass(frozen=True)
class SimulationResult:
    """Everything the browser needs after one successful solver run."""

    source: SimulationInput
    netlist: str
    log: str
    plots: dict[str, Plot]
    op: dict
    ac: dict
    tran: dict
    svg: dict[str, str]
    model_label: str
    model_name: str
    version: str


# SPICE uses "Meg" for 10^6; plain "M" means milli.
_SI_SUFFIXES = (
    (1e12, "T"),
    (1e9, "G"),
    (1e6, "Meg"),
    (1e3, "k"),
    (1.0, ""),
    (1e-3, "m"),
    (1e-6, "u"),
    (1e-9, "n"),
    (1e-12, "p"),
)


def format_si(value: float) -> str:
    """Render an SI value with a SPICE-recognised engineering suffix."""
    if value == 0:
        return "0"
    for factor, suffix in _SI_SUFFIXES:
        scaled = value / factor
        if 1.0 <= abs(scaled) < 1000.0:
            return f"{scaled:g}{suffix}"
    return f"{value:g}"


def validate_input(source: SimulationInput) -> None:
    """Reject impossible or unsupported values before a netlist is built."""
    positives = {
        "VCC": source.vcc,
        "R1": source.r1,
        "R2": source.r2,
        "RC": source.rc,
        "RE": source.re,
        "RL": source.rl,
        "Cin": source.cin,
        "Cout": source.cout,
    }
    for label, value in positives.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label} ต้องเป็นตัวเลขที่มากกว่า 0")
    if not math.isfinite(source.amplitude) or source.amplitude < 0:
        raise ValueError("Amplitude ต้องเป็นตัวเลขที่ไม่ติดลบ")
    if not math.isfinite(source.frequency) or not 1.0 <= source.frequency <= 10e6:
        raise ValueError("Frequency ต้องอยู่ระหว่าง 1 Hz ถึง 10 MHz")
    if source.beta is not None and (not math.isfinite(source.beta) or source.beta <= 0):
        raise ValueError("β ต้องมากกว่า 0")
    if source.source not in SOURCES:
        raise ValueError(f"ไม่รู้จักแหล่งสัญญาณ '{source.source}'")
    if source.analysis not in ANALYSES:
        raise ValueError(f"ไม่รู้จักการวิเคราะห์ '{source.analysis}'")
    if source.model_source not in MODEL_SOURCES:
        raise ValueError(f"ไม่รู้จักแหล่งโมเดล '{source.model_source}'")


def _model_name_from_text(text: str) -> str:
    match = re.search(r"^\s*\.model\s+([A-Za-z0-9_]+)", text, re.IGNORECASE | re.MULTILINE)
    if not match:
        raise SimulationError("ไม่พบชื่อ .model ในไฟล์โมเดลที่เลือก")
    return match.group(1)


def resolve_model(source: SimulationInput) -> tuple[str, str, str]:
    """Return (model text, model name, human-readable provenance label)."""
    if source.model_source == "starter_kit":
        if not source.model_path.strip():
            raise SimulationError("Starter Kit: กรอก path ไฟล์โมเดลด้วย")
        path = Path(source.model_path).expanduser()
        label = "Instructor Starter Kit model (user-supplied)"
    elif source.model_source == "lab_reference":
        path = PROJECT_ROOT / "models" / "lab_reference.bjt"
        label = "Instructor-verified lab model (lab_reference)"
    else:
        path = PROJECT_ROOT / "reference" / "provisional_2n3904.bjt"
        label = "Local reference model (not instructor-verified)"

    if not path.is_file():
        raise SimulationError(f"ไม่พบไฟล์โมเดลของ {source.model_source}: {path}")
    if path.stat().st_size > MAX_MODEL_BYTES:
        raise SimulationError("ไฟล์โมเดลใหญ่เกิน 1 MB")

    text = path.read_text(encoding="utf-8", errors="replace")
    name = source.model_name.strip() or _model_name_from_text(text)
    return text, name, label


def build_netlist(source: SimulationInput, model_text: str, model_name: str) -> str:
    """Create the complete netlist. Model text is written separately as model.bjt."""
    validate_input(source)
    lines = [
        "* Lab 04 CE amplifier - generated from validated form values",
        ".include model.bjt",
        f"VCC  vcc 0  DC {format_si(source.vcc)}",
    ]

    amp = format_si(source.amplitude)
    freq = format_si(source.frequency)
    if source.source == "ac_sine":
        lines.append(f"VIN  in  0  DC 0  SIN(0 {amp} {freq}) AC {amp} 0")
    else:
        period = 1.0 / source.frequency
        edge = format_si(period / 100.0)
        on_time = format_si(period / 2.0)
        lines.append(
            f"VIN  in  0  DC 0  PULSE(0 {amp} 0 {edge} {edge} {on_time} {freq}) AC 0 0"
        )

    lines.extend(
        [
            f"R1   vcc b  {format_si(source.r1)}",
            f"R2   b   0  {format_si(source.r2)}",
            f"RC   vcc c  {format_si(source.rc)}",
            f"RE   e   0  {format_si(source.re)}",
            f"CIN  in  b  {format_si(source.cin)}",
            f"COUT c   out {format_si(source.cout)}",
            f"RL   out 0  {format_si(source.rl)}",
            f"Q1   c b e {model_name}",
        ]
    )

    if source.analysis in ("op", "all"):
        lines.append(".op")
    if source.analysis in ("ac", "all"):
        lines.append(".ac dec 100 1 10Meg")
    if source.analysis in ("tran", "all"):
        period = 1.0 / source.frequency
        step = min(period / 200.0, 10e-6)
        step = max(step, 1e-9)
        lines.append(f".tran {format_si(step)} {format_si(5.0 * period)}")
    lines.append(".end")
    return "\n".join(lines) + "\n"


def parse_raw(blob: bytes) -> dict[str, Plot]:
    """Parse every plot section of an ngspice binary raw file."""
    plots: dict[str, Plot] = {}
    position = 0
    while True:
        header_start = blob.find(b"Plotname:", position)
        if header_start < 0:
            break
        binary_start = blob.find(b"Binary:", header_start)
        if binary_start < 0:
            raise SimulationError("ไม่พบจุดเริ่มข้อมูล Binary ในไฟล์ raw ของ ngspice")

        header = blob[header_start:binary_start].decode("ascii", errors="replace")
        fields: dict[str, str] = {}
        variables: list[str] = []
        for line in header.splitlines():
            stripped = line.strip()
            if ":" in stripped and not stripped[:1].isdigit():
                key, value = stripped.split(":", 1)
                fields[key.strip()] = value.strip()
            match = re.match(r"^\d+\s+(\S+)", stripped)
            if match:
                variables.append(match.group(1))

        try:
            count = int(fields["No. Points"])
            var_count = int(fields["No. Variables"])
        except (KeyError, ValueError) as exc:
            raise SimulationError("header ของไฟล์ raw ไม่สมบูรณ์") from exc
        if len(variables) != var_count:
            raise SimulationError("จำนวนตัวแปรในไฟล์ raw ไม่ตรงกับ header")

        values_per_var = 2 if "complex" in fields.get("Flags", "").lower() else 1
        data_start = binary_start + len(b"Binary:")
        while blob[data_start : data_start + 1] in (b"\r", b"\n"):
            data_start += 1
        frame_size = var_count * values_per_var * 8
        expected = frame_size * count
        payload = blob[data_start : data_start + expected]
        if len(payload) != expected:
            raise SimulationError("ข้อมูลในไฟล์ raw สั้นกว่าที่ header ระบุ")

        rows: list[tuple[complex | float, ...]] = []
        for index in range(count):
            numbers = struct.unpack_from(f"<{var_count * values_per_var}d", payload, index * frame_size)
            if values_per_var == 2:
                row: tuple[complex | float, ...] = tuple(
                    complex(numbers[i * 2], numbers[i * 2 + 1]) for i in range(var_count)
                )
            else:
                row = tuple(float(value) for value in numbers)
            rows.append(row)

        title = fields.get("Plotname", "Unknown")
        key = "ac" if "ac" in title.lower() else (
            "op" if "operating" in title.lower() else (
                "tran" if "transient" in title.lower() else title.lower()
            )
        )
        plots[key] = Plot(title, tuple(variables), fields.get("Flags", ""), tuple(rows))
        position = data_start + expected

    if not plots:
        raise SimulationError("ไฟล์ raw ไม่มี plot ที่อ่านได้")
    return plots


def _index(variables: tuple[str, ...], name: str) -> int:
    try:
        return variables.index(name)
    except ValueError as exc:
        raise SimulationError(f"ngspice ไม่ได้บันทึกตัวแปร {name}") from exc


def _as_float(value: complex | float) -> float:
    return float(value.real) if isinstance(value, complex) else float(value)


def _normalise_degrees(value: float) -> float:
    """Keep phase in [-180, 180); inversion is shown as -180, not +180."""
    while value >= 180.0:
        value -= 360.0
    while value < -180.0:
        value += 360.0
    return value


def analyze_op(plot: Plot, source: SimulationInput) -> dict:
    """Derive DC operating point quantities from saved SPICE node voltages."""
    row = plot.values[0]
    vcc = _as_float(row[_index(plot.variables, "v(vcc)")])
    vb = _as_float(row[_index(plot.variables, "v(b)")])
    vc = _as_float(row[_index(plot.variables, "v(c)")])
    ve = _as_float(row[_index(plot.variables, "v(e)")])
    vbe = vb - ve
    vce = vc - ve
    ic_ma = (vcc - vc) / source.rc * 1e3
    ie_ma = ve / source.re * 1e3
    ib_ua = ((vcc - vb) / source.r1 - vb / source.r2) * 1e6
    if vce <= 0.2:
        region = "Saturation"
    elif ic_ma <= 0.001:
        region = "Cutoff"
    else:
        region = "Forward-active"
    return {
        "vcc": vcc,
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vbe": vbe,
        "vce": vce,
        "ic_ma": ic_ma,
        "ie_ma": ie_ma,
        "ib_ua": ib_ua,
        "region": region,
    }


def _crossing(f1: float, g1: float, f2: float, g2: float, target: float) -> float:
    """Log-frequency interpolation where a gain curve crosses a threshold."""
    if f1 <= 0 or f2 <= 0 or g1 == g2:
        return f1
    ratio = (target - g1) / (g2 - g1)
    return 10 ** (math.log10(f1) + ratio * (math.log10(f2) - math.log10(f1)))


def analyze_ac(plot: Plot) -> dict:
    """Compute |Vout/Vin|, phase and -3 dB corners from an AC plot."""
    fi = _index(plot.variables, "frequency")
    vi = _index(plot.variables, "v(in)")
    vo = _index(plot.variables, "v(out)")
    frequency: list[float] = []
    gain_db: list[float] = []
    phase_deg: list[float] = []
    for row in plot.values:
        vin = row[vi]
        vout = row[vo]
        f = _as_float(row[fi])
        if not isinstance(vin, complex) or not isinstance(vout, complex):
            raise SimulationError("AC plot ไม่ใช่ข้อมูลแบบ complex")
        if abs(vin) == 0:
            gain_db.append(-math.inf)
            phase_deg.append(0.0)
        else:
            gain_db.append(20.0 * math.log10(abs(vout) / abs(vin)))
            delta = math.atan2(vout.imag, vout.real) - math.atan2(vin.imag, vin.real)
            phase_deg.append(_normalise_degrees(math.degrees(delta)))
        frequency.append(f)

    finite = [gain for gain in gain_db if math.isfinite(gain)]
    midband = max(finite) if finite else -math.inf
    threshold = midband - 3.0
    f_low: float | None = None
    f_high: float | None = None
    for i in range(len(frequency) - 1):
        g1, g2 = gain_db[i], gain_db[i + 1]
        if f_low is None and g1 < threshold <= g2:
            f_low = _crossing(frequency[i], g1, frequency[i + 1], g2, threshold)
        if g1 >= threshold > g2:
            f_high = _crossing(frequency[i], g1, frequency[i + 1], g2, threshold)

    mid_index = gain_db.index(midband) if finite else 0
    note = None
    if f_low is None or f_high is None:
        note = "not determined in sweep range"
    return {
        "frequency": frequency,
        "gain_db": gain_db,
        "phase_deg": phase_deg,
        "midband_gain_db": midband,
        "midband_phase_deg": phase_deg[mid_index],
        "f_low_hz": f_low,
        "f_high_hz": f_high,
        "bandwidth_hz": (f_high - f_low) if f_low is not None and f_high is not None else None,
        "cutoff_note": note,
    }


def analyze_tran(plot: Plot) -> dict:
    """Compute peak-to-peak levels and inversion from a transient plot."""
    ti = _index(plot.variables, "time")
    vi = _index(plot.variables, "v(in)")
    vo = _index(plot.variables, "v(out)")
    time = [_as_float(row[ti]) for row in plot.values]
    vin = [_as_float(row[vi]) for row in plot.values]
    vout = [_as_float(row[vo]) for row in plot.values]
    vin_pp = max(vin) - min(vin) if vin else 0.0
    vout_pp = max(vout) - min(vout) if vout else 0.0
    mean_in = sum(vin) / len(vin) if vin else 0.0
    mean_out = sum(vout) / len(vout) if vout else 0.0
    covariance = sum((a - mean_in) * (b - mean_out) for a, b in zip(vin, vout))
    return {
        "time": time,
        "vin": vin,
        "vout": vout,
        "vin_pp": vin_pp,
        "vout_pp": vout_pp,
        "vin_pp_mv": vin_pp * 1000.0,
        "vout_pp_mv": vout_pp * 1000.0,
        "gain": (vout_pp / vin_pp) if vin_pp > 0 else None,
        "inverted": covariance < 0,
    }


def line_chart_svg(
    series: list[tuple[str, list[float], list[float]]],
    x_label: str,
    y_label: str,
    width: int = 720,
    height: int = 260,
) -> str:
    """Build a compact inline SVG chart without any chart dependency."""
    left, right, top, bottom = 62, 18, 18, 46
    plot_w = width - left - right
    plot_h = height - top - bottom
    clean: list[tuple[str, list[float], list[float]]] = []
    for label, xs, ys in series:
        pairs = [
            (x, y)
            for x, y in zip(xs, ys)
            if math.isfinite(x) and math.isfinite(y)
        ]
        if pairs:
            clean.append((label, [p[0] for p in pairs], [p[1] for p in pairs]))

    parts = [
        f'<svg class="plot" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{html.escape(x_label)} against {html.escape(y_label)}">'
    ]
    if not clean:
        parts.append(
            f'<text x="{width / 2:g}" y="{height / 2:g}" text-anchor="middle">No data in this run</text>'
        )
        parts.append("</svg>")
        return "".join(parts)

    all_x = [x for _, xs, _ in clean for x in xs]
    all_y = [y for _, _, ys in clean for y in ys]
    xmin, xmax = min(all_x), max(all_x)
    ymin, ymax = min(all_y), max(all_y)
    if xmin == xmax:
        xmax = xmin + 1.0
    if ymin == ymax:
        ymin -= 1.0
        ymax += 1.0
    y_pad = (ymax - ymin) * 0.08
    ymin -= y_pad
    ymax += y_pad

    def px(x: float) -> float:
        return left + (x - xmin) / (xmax - xmin) * plot_w

    def py(y: float) -> float:
        return top + (ymax - y) / (ymax - ymin) * plot_h

    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>')
    parts.append(
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>'
    )
    for fraction in (0.0, 0.5, 1.0):
        y = top + fraction * plot_h
        value = ymax - fraction * (ymax - ymin)
        parts.append(
            f'<line class="grid" x1="{left}" y1="{y:g}" x2="{left + plot_w}" y2="{y:g}"/>'
        )
        parts.append(
            f'<text class="tick" x="{left - 8}" y="{y + 4:g}" text-anchor="end">{value:.3g}</text>'
        )
    parts.append(
        f'<text class="axis-label" x="{left + plot_w / 2:g}" y="{height - 6}" text-anchor="middle">'
        f"{html.escape(x_label)}</text>"
    )
    parts.append(
        f'<text class="axis-label" transform="translate(14 {top + plot_h / 2:g}) rotate(-90)" '
        f'text-anchor="middle">{html.escape(y_label)}</text>'
    )

    colors = ("#0c8e83", "#c77a35", "#5b6ee1")
    for index, (label, xs, ys) in enumerate(clean):
        color = colors[index % len(colors)]
        points = " ".join(f"{px(x):.2f},{py(y):.2f}" for x, y in zip(xs, ys))
        parts.append(
            f'<polyline class="series" fill="none" stroke="{color}" stroke-width="2" points="{points}"/>'
        )
        legend_x = left + 12 + index * 160
        parts.append(
            f'<text class="legend" x="{legend_x}" y="{top + 12}" fill="{color}">{html.escape(label)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def _log_tail(log: str, limit: int = 1200) -> str:
    return log[-limit:] if len(log) > limit else log


def resolve_ngspice() -> str:
    """Find the solver even when the desktop PATH was not refreshed."""
    configured = os.environ.get("NGSPICE_BIN")
    if configured:
        return configured
    found = shutil.which("ngspice")
    if found:
        return found
    for candidate in NGSPICE_FALLBACKS:
        if Path(candidate).is_file():
            return candidate
    return NGSPICE_BIN


def run_simulation(
    source: SimulationInput,
    *,
    ngspice_bin: str | None = None,
    timeout: int = RUN_TIMEOUT_SECONDS,
) -> SimulationResult:
    """Run one ngspice batch job and return parsed, display-ready results."""
    validate_input(source)
    model_text, model_name, model_label = resolve_model(source)
    netlist = build_netlist(source, model_text, model_name)
    executable = ngspice_bin or resolve_ngspice()

    with tempfile.TemporaryDirectory(prefix="lab04_ngspice_") as tmp:
        workdir = Path(tmp)
        (workdir / "model.bjt").write_text(model_text, encoding="utf-8")
        (workdir / "circuit.cir").write_text(netlist, encoding="utf-8")
        command = [executable, "-b", "-o", "run.log", "-r", "run.raw", "circuit.cir"]
        try:
            completed = subprocess.run(
                command,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SimulationError(f"ngspice timeout หลัง {timeout} วินาที") from exc
        except FileNotFoundError as exc:
            raise SimulationError("ไม่พบ ngspice ใน PATH — ตรวจการติดตั้งก่อนรัน") from exc

        log_path = workdir / "run.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        if not log:
            log = f"{completed.stdout}\n{completed.stderr}".strip()
        if completed.returncode != 0:
            raise SimulationError(
                f"ngspice run ไม่สำเร็จ (exit {completed.returncode}):\n{_log_tail(log)}"
            )

        raw_path = workdir / "run.raw"
        if not raw_path.is_file() or raw_path.stat().st_size == 0:
            raise SimulationError("ngspice ไม่ได้สร้างไฟล์ run.raw — ไม่มีข้อมูลกราฟให้แสดง")
        plots = parse_raw(raw_path.read_bytes())

    op = analyze_op(plots["op"], source) if "op" in plots else {}
    ac = analyze_ac(plots["ac"]) if "ac" in plots else {}
    tran = analyze_tran(plots["tran"]) if "tran" in plots else {}

    svg: dict[str, str] = {}
    if ac:
        log_x = [math.log10(f) if f > 0 else 0.0 for f in ac["frequency"]]
        svg["ac"] = line_chart_svg(
            [("Gain", log_x, ac["gain_db"])], "Frequency (Hz, log10)", "Gain (dB)"
        )
        svg["ac_phase"] = line_chart_svg(
            [("Phase", log_x, ac["phase_deg"])], "Frequency (Hz, log10)", "Phase (deg)"
        )
    if tran:
        time_ms = [t * 1e3 for t in tran["time"]]
        svg["tran"] = line_chart_svg(
            [("Vin", time_ms, tran["vin"]), ("Vout", time_ms, tran["vout"])],
            "Time (ms)",
            "Voltage (V)",
        )

    version_match = re.search(r"ngspice[- ]?(\d+(?:\.\d+)?)", log)
    version = version_match.group(0) if version_match else "ngspice (version unknown)"
    return SimulationResult(
        source=source,
        netlist=netlist,
        log=log,
        plots=plots,
        op=op,
        ac=ac,
        tran=tran,
        svg=svg,
        model_label=model_label,
        model_name=model_name,
        version=version,
    )
