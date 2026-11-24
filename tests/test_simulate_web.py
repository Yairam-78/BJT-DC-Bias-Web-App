"""HTTP tests for the Lab 04 /simulate route.

The engine is replaced by a stub so no ngspice process is started.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import app as app_module


def valid_form(**overrides):
    form = {
        "svcc": "12",
        "svcc_unit": "v",
        "sr1": "100",
        "sr1_unit": "kohm",
        "sr2": "22",
        "sr2_unit": "kohm",
        "src": "2.2",
        "src_unit": "kohm",
        "sre": "1",
        "sre_unit": "kohm",
        "srl": "10",
        "srl_unit": "kohm",
        "scin": "10",
        "scin_unit": "u",
        "scout": "10",
        "scout_unit": "u",
        "sampl": "10",
        "sampl_unit": "mv",
        "svbe": "0.7",
        "svbe_unit": "v",
        "sfreq": "1",
        "sfreq_unit": "khz",
        "sbeta": "150",
        "ssource": "ac_sine",
        "sanalysis": "all",
        "smodel": "local_reference",
        "smodel_path": "",
        "smodel_name": "",
    }
    form.update(overrides)
    return form


def fake_result():
    return SimpleNamespace(
        op={
            "vcc": 12.0,
            "vb": 2.0,
            "ve": 1.3,
            "vc": 9.05,
            "vbe": 0.7,
            "vce": 7.75,
            "ic_ma": 1.324,
            "ie_ma": 1.333,
            "ib_ua": 11.2,
            "region": "Forward-active",
        },
        ac={
            "midband_gain_db": 4.89,
            "midband_phase_deg": -179.87,
            "f_low_hz": 153.0,
            "f_high_hz": 4_200_000.0,
            "bandwidth_hz": 4_199_847.0,
            "cutoff_note": None,
            "gain_db": [4.0, 4.89, 4.1],
            "phase_deg": [-178.0, -179.87, -181.0],
            "frequency": [100.0, 1000.0, 10000.0],
        },
        tran={
            "vin_pp": 0.02,
            "vout_pp": 0.035,
            "vin_pp_mv": 20.0,
            "vout_pp_mv": 35.0,
            "gain": 1.75,
            "inverted": True,
            "time": [0.0, 0.001],
            "vin": [0.0, 0.01],
            "vout": [0.0, -0.02],
        },
        svg={
            "ac": "<svg data-testid='ac-chart'></svg>",
            "tran": "<svg data-testid='tran-chart'></svg>",
        },
        model_label="Local reference model (not instructor-verified)",
        model_name="Q2N3904",
        version="ngspice-47",
        netlist="* test netlist",
        log="* test log",
    )


class TestSimulatePage(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        self.client = app_module.app.test_client()

    def test_index_exposes_lab04_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("CE Amplifier Simulator", body)
        self.assertIn('name="ssource"', body)
        self.assertIn('name="sanalysis"', body)
        self.assertIn('name="smodel"', body)

    def test_valid_run_renders_spice_results(self):
        with patch.object(app_module.spice_engine, "run_simulation", return_value=fake_result()) as run:
            response = self.client.post("/simulate", data=valid_form())
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        run.assert_called_once()
        self.assertIn("ngspice-47", body)
        self.assertIn("data-testid='ac-chart'", body)
        self.assertIn("data-testid='tran-chart'", body)
        self.assertIn("Local reference", body)
        self.assertIn('20.00 <span class="unit">mV</span>', body)
        self.assertIn('35.00 <span class="unit">mV</span>', body)
        self.assertNotIn("การจำลองล้มเหลว", body)

    def test_zero_re_emits_thai_error_without_running_engine(self):
        with patch.object(app_module.spice_engine, "run_simulation") as run:
            response = self.client.post("/simulate", data=valid_form(sre="0"))
        self.assertEqual(response.status_code, 200)
        run.assert_not_called()
        body = response.get_data(as_text=True)
        self.assertIn("RE", body)
        self.assertIn("ต้องมากกว่า 0", body)
        self.assertNotIn("data-testid='ac-chart'", body)

    def test_engine_failure_is_shown_without_stale_success(self):
        error = app_module.spice_engine.SimulationError("ngspice ไม่พร้อม: program not found")
        with patch.object(app_module.spice_engine, "run_simulation", side_effect=error):
            response = self.client.post("/simulate", data=valid_form())
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("การจำลองล้มเหลว", body)
        self.assertIn("program not found", body)
        self.assertNotIn("data-testid='ac-chart'", body)

    def test_index_exposes_running_hook_and_readable_hints(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="sim-run-state"', body)
        self.assertIn('name="svbe"', body)
        self.assertIn("app.js", body)
        self.assertIn('rel="icon"', body)
        self.assertIn("(Source Amplitude)", body)
        self.assertNotIn("(svcc)", body)
        self.assertNotIn("acceptance cases", body)
        self.assertIn("Lab 03 → Lab 04", body)

    def test_submit_script_sets_running_state(self):
        script = (
            Path(__file__).resolve().parents[1] / "static" / "app.js"
        ).read_text(encoding="utf-8")
        self.assertIn("RUNNING", script)
        self.assertIn("disabled", script)
        self.assertIn("aria-current", script)

    def test_success_renders_success_status_and_provenance(self):
        with patch.object(app_module.spice_engine, "run_simulation", return_value=fake_result()):
            body = self.client.post("/simulate", data=valid_form()).get_data(as_text=True)
        self.assertIn('data-state="SUCCESS"', body)
        self.assertIn(">SUCCESS</span>", body)
        self.assertIn("SPICE / ngspice", body)
        self.assertIn("PROVISIONAL", body)
        self.assertNotIn('data-state="ERROR"', body)

    def test_validation_error_renders_error_status(self):
        body = self.client.post("/simulate", data=valid_form(sre="0")).get_data(as_text=True)
        self.assertIn('data-state="ERROR"', body)
        self.assertIn(">ERROR</span>", body)
        self.assertNotIn('data-state="SUCCESS"', body)

    def test_engine_failure_renders_error_status(self):
        error = app_module.spice_engine.SimulationError("ngspice ไม่พร้อม: program not found")
        with patch.object(app_module.spice_engine, "run_simulation", side_effect=error):
            body = self.client.post("/simulate", data=valid_form()).get_data(as_text=True)
        self.assertIn('data-state="ERROR"', body)
        self.assertIn(">ERROR</span>", body)
        self.assertNotIn('data-state="SUCCESS"', body)

    def test_analytical_reference_is_labelled_and_independent(self):
        with patch.object(app_module.spice_engine, "run_simulation", return_value=fake_result()):
            body = self.client.post("/simulate", data=valid_form()).get_data(as_text=True)
        self.assertIn("Analytical Reference", body)
        self.assertIn("dc_bias.py", body)
        self.assertIn("2.008", body)
        self.assertIn("8.661", body)
        self.assertIn("SPICE / ngspice", body)
        self.assertIn("Bf", body)
        self.assertIn("1.324", body)


if __name__ == "__main__":
    unittest.main()
