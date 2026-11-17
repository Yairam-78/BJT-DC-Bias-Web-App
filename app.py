"""Flask front end for the BJT DC bias calculator.

The HTTP layer only parses the form, converts the chosen units to SI and
renders the template. All engineering lives in :mod:`dc_bias`.
"""

from flask import Flask, render_template, request

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


def _render(*, mode: str, form: dict, units: dict, result, errors: dict):
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
