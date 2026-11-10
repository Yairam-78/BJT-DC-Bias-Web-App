"""Flask front end for the BJT DC bias calculator.

The HTTP layer only parses the form, converts kilo-ohms to ohms and renders
the template. All engineering lives in :mod:`dc_bias`.
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


def _read_form(form_data) -> tuple[dict, dict, dict]:
    """Return (raw text per field, values in SI units, errors per field)."""
    raw = {name: (form_data.get(name) or "").strip() for name in FIELD_NAMES}
    values = {}
    errors = {}

    for name, text in raw.items():
        label = FIELD_LABELS[name]
        if text == "":
            errors[name] = f"{label} ต้องกรอก"
            continue
        try:
            number = float(text)
        except ValueError:
            errors[name] = f"{label} ต้องเป็นตัวเลข"
            continue
        values[name] = number * 1000.0 if name in RESISTOR_FIELDS else number

    return raw, values, errors


@app.get("/")
def index():
    return render_template(
        "index.html",
        form=dict(DEFAULT_FORM),
        result=None,
        errors={},
        status=None,
    )


@app.post("/calculate")
def calculate():
    raw, values, errors = _read_form(request.form)
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
        result=result,
        errors=errors,
        status=status,
    )
