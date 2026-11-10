"""Flask front end for the BJT DC bias calculator.

The HTTP layer only parses the form, converts the chosen units to SI and
renders the template. All engineering lives in :mod:`dc_bias`.
"""

from flask import Flask, render_template, request

from dc_bias import calculate_dc_bias

app = Flask(__name__)

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.7",
}

FIELD_NAMES = tuple(DEFAULT_FORM)

FIELD_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

RESISTOR_FIELDS = ("r1", "r2", "rc", "re")
VOLTAGE_FIELDS = ("vcc", "vbe")

RESISTOR_UNITS = {"ohm": 1.0, "kohm": 1e3, "mohm": 1e6}
VOLTAGE_UNITS = {"v": 1.0, "mv": 1e-3}

DEFAULT_UNITS = {
    "vcc": "v",
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


def _read_form(form_data) -> tuple[dict, dict, dict, dict]:
    """Return (raw values, chosen units, SI values, errors) per field."""
    raw = {name: (form_data.get(name) or "").strip() for name in FIELD_NAMES}
    units = {
        name: (form_data.get(f"{name}_unit") or DEFAULT_UNITS[name])
        for name in FIELD_NAMES
    }
    values = {}
    errors = {}

    for name, text in raw.items():
        label = FIELD_LABELS[name]
        allowed = _allowed_units(name)

        if allowed is not None and units[name] not in allowed:
            errors[name] = f"{label} หน่วยไม่ถูกต้อง"
            continue

        if text == "":
            errors[name] = f"{label} ต้องกรอก"
            continue

        try:
            number = float(text)
        except ValueError:
            errors[name] = f"{label} ต้องเป็นตัวเลข"
            continue

        values[name] = number * (allowed[units[name]] if allowed else 1.0)

    return raw, units, values, errors


@app.get("/")
def index():
    return render_template(
        "index.html",
        form=dict(DEFAULT_FORM),
        units=dict(DEFAULT_UNITS),
        result=None,
        errors={},
        status=None,
    )


@app.post("/calculate")
def calculate():
    raw, units, values, errors = _read_form(request.form)
    result = None
    status = None

    if not errors:
        try:
            result = calculate_dc_bias(**values)
        except ValueError as exc:
            errors["_form"] = str(exc)
        else:
            status = result.region

    return render_template(
        "index.html",
        form=raw,
        units=units,
        result=result,
        errors=errors,
        status=status,
    )
