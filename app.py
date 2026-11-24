"""Flask front end for the BJT DC bias calculator.

The HTTP layer only parses the form, converts the chosen units to SI and
renders the template. All engineering lives in :mod:`dc_bias`.
"""

import math

from flask import Flask, render_template, request

import spice_engine
from dc_bias import (
    calculate_dc_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)

app = Flask(__name__)

DEFAULT_MODE = "divider"

# The field list of each mode is also the list of values that mode needs, so
# the form can hide resistors the equation never reads instead of demanding
# them for every circuit.
MODES = {
    "divider": {
        "label": "Voltage Divider Bias",
        "short": "Voltage Divider",
        "parts": "R1 · R2 · RC · RE",
        "fields": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    },
    "fixed": {
        "label": "Fixed Bias",
        "short": "Fixed Bias",
        "parts": "RB · RC",
        "fields": ("vcc", "rb", "rc", "beta", "vbe"),
    },
    "emitter": {
        "label": "Emitter Bias",
        "short": "Emitter Bias",
        "parts": "RB · RC · RE",
        "fields": ("vcc", "rb", "rc", "re", "beta", "vbe"),
    },
}

BIAS_FUNCTIONS = {
    "divider": calculate_dc_bias,
    "fixed": calculate_fixed_bias,
    "emitter": calculate_emitter_bias,
}

# (value, full label, short title, resistor list) — the picker shows the short
# title and the parts so the choice is readable without opening a dropdown.
MODE_OPTIONS = tuple(
    (name, config["label"], config["short"], config["parts"])
    for name, config in MODES.items()
)

DEFAULT_FORM = {
    "vcc": "12",
    "rb": "1000",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.7",
}

FIELD_NAMES = ("vcc", "rb", "r1", "r2", "rc", "re", "beta", "vbe")

FIELD_LABELS = {
    "vcc": "VCC",
    "rb": "RB",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

RESISTOR_FIELDS = ("rb", "r1", "r2", "rc", "re")
VOLTAGE_FIELDS = ("vcc", "vbe")

RESISTOR_UNITS = {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6}
VOLTAGE_UNITS = {"v": 1.0, "mv": 1e-3}

DEFAULT_UNITS = {
    "vcc": "v",
    "rb": "kohm",
    "r1": "kohm",
    "r2": "kohm",
    "rc": "kohm",
    "re": "kohm",
    "beta": "",
    "vbe": "v",
}

# Lab 04 uses separate field names so the original Lab 03 form parser and its
# tests remain untouched. Values are converted to SI here before reaching the
# solver adapter.
SIM_FIELDS = (
    "svcc", "sr1", "sr2", "src", "sre", "srl",
    "scin", "scout", "sampl", "sfreq", "sbeta",
)

SIM_FIELD_LABELS = {
    "svcc": "VCC",
    "sr1": "R1",
    "sr2": "R2",
    "src": "RC",
    "sre": "RE",
    "srl": "RL",
    "scin": "Cin",
    "scout": "Cout",
    "sampl": "Amplitude",
    "sfreq": "Frequency",
    "sbeta": "β",
}

SIM_UNIT_FACTORS = {
    "svcc": {"v": 1.0, "mv": 1e-3},
    "sr1": {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6},
    "sr2": {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6},
    "src": {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6},
    "sre": {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6},
    "srl": {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6},
    "scin": {"f": 1.0, "u": 1e-6, "n": 1e-9, "p": 1e-12},
    "scout": {"f": 1.0, "u": 1e-6, "n": 1e-9, "p": 1e-12},
    "sampl": {"v": 1.0, "mv": 1e-3},
    "sfreq": {"hz": 1.0, "khz": 1e3, "mhz": 1e6},
    "sbeta": {},
}

SIM_DEFAULT_FORM = {
    "svcc": "12",
    "sr1": "100",
    "sr2": "22",
    "src": "2.2",
    "sre": "1",
    "srl": "10",
    "scin": "10",
    "scout": "10",
    "sampl": "10",
    "sfreq": "1",
    "sbeta": "150",
    "ssource": "ac_sine",
    "sanalysis": "all",
    "smodel": "local_reference",
    "smodel_path": "",
    "smodel_name": "",
}

SIM_DEFAULT_UNITS = {
    "svcc": "v",
    "sr1": "kohm",
    "sr2": "kohm",
    "src": "kohm",
    "sre": "kohm",
    "srl": "kohm",
    "scin": "u",
    "scout": "u",
    "sampl": "mv",
    "sfreq": "khz",
    "sbeta": "",
}

SIM_SELECT_FIELDS = ("ssource", "sanalysis", "smodel")
SIM_OPTIONS = {
    "ssource": (("ac_sine", "AC sine (10 mV @ 1 kHz)"), ("dc_pulse", "DC pulse")),
    "sanalysis": (("all", ".op + .ac + .tran"), ("op", ".op only"), ("ac", ".ac only"), ("tran", ".tran only")),
    "smodel": (
        ("local_reference", "Local reference (not instructor-verified)"),
        ("lab_reference", "Lab verified model (when supplied)"),
        ("starter_kit", "Instructor Starter Kit file"),
    ),
}


def _allowed_units(name: str):
    if name in RESISTOR_FIELDS:
        return RESISTOR_UNITS
    if name in VOLTAGE_FIELDS:
        return VOLTAGE_UNITS
    return None


def _read_mode(form_data) -> tuple[str, str | None]:
    """Return the requested mode and an error message when it is unknown.

    An unknown mode is reported instead of silently falling back to the
    voltage divider, otherwise a typo would produce plausible but unrelated
    numbers.
    """
    requested = (form_data.get("mode") or DEFAULT_MODE).strip()
    if requested not in MODES:
        known = ", ".join(MODES)
        return DEFAULT_MODE, f"ไม่รู้จักโหมด '{requested}' (รองรับ: {known})"
    return requested, None


def _read_form(form_data) -> tuple[dict, dict]:
    """Return the raw text and chosen unit of every field.

    Every field is read even when the mode ignores it, so switching modes does
    not wipe what the user already typed.
    """
    raw = {name: (form_data.get(name) or "").strip() for name in FIELD_NAMES}
    units = {
        name: (form_data.get(f"{name}_unit") or DEFAULT_UNITS[name])
        for name in FIELD_NAMES
    }
    return raw, units


def _read_values(raw: dict, units: dict, mode: str) -> tuple[dict, dict]:
    """Convert the fields this mode needs to SI and report per-field errors."""
    values = {}
    errors = {}

    for name in MODES[mode]["fields"]:
        label = FIELD_LABELS[name]
        allowed = _allowed_units(name)

        if allowed is not None and units[name] not in allowed:
            errors[name] = f"{label} หน่วยไม่ถูกต้อง"
            continue

        text = raw[name]
        if text == "":
            errors[name] = f"{label} ต้องกรอก"
            continue

        try:
            number = float(text)
        except ValueError:
            errors[name] = f"{label} ต้องเป็นตัวเลข"
            continue

        values[name] = number * (allowed[units[name]] if allowed else 1.0)

    return values, errors


def _read_sim_form(form_data) -> tuple[dict, dict]:
    """Read both Lab 04 numeric fields and selection fields without losing them."""
    raw = {name: (form_data.get(name) or "").strip() for name in SIM_FIELDS + SIM_SELECT_FIELDS}
    raw["smodel_path"] = (form_data.get("smodel_path") or "").strip()
    raw["smodel_name"] = (form_data.get("smodel_name") or "").strip()
    units = {
        name: (form_data.get(f"{name}_unit") or SIM_DEFAULT_UNITS[name])
        for name in SIM_FIELDS
    }
    return raw, units


def _read_sim_values(raw: dict, units: dict) -> tuple[dict, dict]:
    """Convert the Lab 04 form to SI and collect per-field Thai errors."""
    values: dict[str, float] = {}
    errors: dict[str, str] = {}

    for name in SIM_FIELDS:
        label = SIM_FIELD_LABELS[name]
        allowed = SIM_UNIT_FACTORS[name]
        # β has no unit selector; an empty factor map means dimensionless.
        if allowed:
            if units[name] not in allowed:
                errors[name] = f"{label} หน่วยไม่ถูกต้อง"
                continue
            factor = allowed[units[name]]
        else:
            factor = 1.0
        text = raw[name]
        if text == "":
            errors[name] = f"{label} ต้องกรอก"
            continue
        try:
            number = float(text)
        except ValueError:
            errors[name] = f"{label} ต้องเป็นตัวเลข"
            continue
        if not math.isfinite(number):
            errors[name] = f"{label} ต้องเป็นตัวเลขที่จำกัด"
            continue
        if name == "sampl":
            if number < 0:
                errors[name] = f"{label} ต้องไม่ติดลบ"
        elif number <= 0:
            errors[name] = f"{label} ต้องมากกว่า 0"
        if name not in errors:
            values[name] = number * factor

    for name, options in SIM_OPTIONS.items():
        if raw[name] not in dict(options):
            errors[name] = f"{SIM_FIELD_LABELS.get(name, name)} ไม่ถูกต้อง"

    return values, errors


def _make_sim_input(values: dict, raw: dict) -> spice_engine.SimulationInput:
    return spice_engine.SimulationInput(
        vcc=values["svcc"],
        r1=values["sr1"],
        r2=values["sr2"],
        rc=values["src"],
        re=values["sre"],
        rl=values["srl"],
        cin=values["scin"],
        cout=values["scout"],
        amplitude=values["sampl"],
        frequency=values["sfreq"],
        beta=values["sbeta"],
        source=raw["ssource"],
        analysis=raw["sanalysis"],
        model_source=raw["smodel"],
        model_path=raw["smodel_path"],
        model_name=raw["smodel_name"],
    )


def _render(
    *,
    mode: str,
    form: dict,
    units: dict,
    result,
    errors: dict,
    sim_form: dict | None = None,
    sim_units: dict | None = None,
    sim_result=None,
    sim_errors: dict | None = None,
):
    config = MODES[mode]
    return render_template(
        "index.html",
        mode=mode,
        mode_label=config["label"],
        mode_fields=config["fields"],
        mode_options=MODE_OPTIONS,
        form=form,
        units=units,
        result=result,
        errors=errors,
        status=result.region if result else None,
        sim_form=dict(SIM_DEFAULT_FORM) if sim_form is None else sim_form,
        sim_units=dict(SIM_DEFAULT_UNITS) if sim_units is None else sim_units,
        sim_result=sim_result,
        sim_errors=sim_errors or {},
        sim_fields=SIM_FIELDS,
        sim_labels=SIM_FIELD_LABELS,
        sim_units_map=SIM_UNIT_FACTORS,
        sim_options=SIM_OPTIONS,
    )


@app.get("/")
def index():
    mode, mode_error = _read_mode(request.args)
    errors = {"_form": mode_error} if mode_error else {}
    return _render(
        mode=mode,
        form=dict(DEFAULT_FORM),
        units=dict(DEFAULT_UNITS),
        result=None,
        errors=errors,
    )


@app.post("/calculate")
def calculate():
    mode, mode_error = _read_mode(request.form)
    raw, units = _read_form(request.form)

    if mode_error:
        values, errors = {}, {"_form": mode_error}
    else:
        values, errors = _read_values(raw, units, mode)

    result = None
    if not errors:
        try:
            result = BIAS_FUNCTIONS[mode](**values)
        except ValueError as exc:
            errors["_form"] = str(exc)

    return _render(mode=mode, form=raw, units=units, result=result, errors=errors)


@app.post("/simulate")
def simulate():
    """Run the CE amplifier solver without touching the Lab 03 calculation path."""
    raw, units = _read_sim_form(request.form)
    values, errors = _read_sim_values(raw, units)
    result = None

    if not errors:
        try:
            result = spice_engine.run_simulation(_make_sim_input(values, raw))
        except ValueError as exc:
            errors["_sim"] = str(exc)
        except spice_engine.SimulationError as exc:
            errors["_sim"] = f"การจำลองล้มเหลว: {exc}"

    return _render(
        mode=DEFAULT_MODE,
        form=dict(DEFAULT_FORM),
        units=dict(DEFAULT_UNITS),
        result=None,
        errors={},
        sim_form=raw,
        sim_units=units,
        sim_result=result,
        sim_errors=errors,
    )
