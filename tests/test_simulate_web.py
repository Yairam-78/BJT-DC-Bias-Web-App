"""HTTP tests for the Lab 04 /simulate route.

The engine is replaced by a stub so no ngspice process is started.
"""

import unittest
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


if __name__ == "__main__":
    unittest.main()
