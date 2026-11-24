"""Tests for the Lab 04 ngspice adapter.

The tests never start ngspice. Raw binary files are synthesised in memory and
subprocess.run is replaced, so the suite stays offline and deterministic.
"""

import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import spice_engine
from spice_engine import SimulationError, SimulationInput


def make_raw(plotname: str, flags: str, variables: list[str], rows: list[list[tuple[float, float] | float]]) -> bytes:
    """Build a small ngspice-style binary raw file for parser tests."""
    header = "\n".join(
        [
            "Title: synthetic",
            "Date: Tue Nov 24 00:00:00  2026",
            f"Plotname: {plotname}",
            f"Flags: {flags}",
            f"No. Variables: {len(variables)}",
            f"No. Points: {len(rows)}",
            "Variables:",
            *[f"\t{i}\t{name}\tvoltage" for i, name in enumerate(variables)],
            "Binary:",
            "",
        ]
    )
    complex_plot = "complex" in flags
    flat: list[float] = []
    for row in rows:
        for value in row:
            if complex_plot:
                real, imag = value
                flat.extend((real, imag))
            else:
                flat.append(value)
    return header.encode("ascii") + struct.pack(f"<{len(flat)}d", *flat)


def sample_input(**overrides) -> SimulationInput:
    values = dict(
        vcc=12.0,
        r1=100_000.0,
        r2=22_000.0,
        rc=2_200.0,
        re=1_000.0,
        rl=10_000.0,
        cin=10e-6,
        cout=10e-6,
        amplitude=10e-3,
        frequency=1_000.0,
        source="ac_sine",
        analysis="all",
        model_source="local_reference",
        model_path="",
        model_name="",
        beta=150.0,
    )
    values.update(overrides)
    return SimulationInput(**values)


class TestParseRaw(unittest.TestCase):
    def test_reads_complex_ac_plot(self):
        blob = make_raw(
            "AC Analysis",
            "complex",
            ["frequency", "v(in)", "v(out)"],
            [
                [(100.0, 0.0), (0.01, 0.0), (-0.1, 0.0)],
                [(1_000.0, 0.0), (0.01, 0.0), (-1.0, 0.0)],
            ],
        )
        plots = spice_engine.parse_raw(blob)
        ac = plots["ac"]
        self.assertEqual(ac.title, "AC Analysis")
        self.assertEqual(ac.variables, ("frequency", "v(in)", "v(out)"))
        self.assertEqual(len(ac.values), 2)
        self.assertAlmostEqual(ac.values[0][0].real, 100.0)
        self.assertAlmostEqual(ac.values[1][2].real, -1.0)

    def test_reads_real_op_and_tran_plots(self):
        op = make_raw(
            "Operating Point",
            "real",
            ["v(b)", "v(c)", "v(e)"],
            [[2.0, 9.0, 1.3]],
        )
        tran = make_raw(
            "Transient Analysis",
            "real",
            ["time", "v(in)", "v(out)"],
            [[0.0, 0.0, 0.0], [0.001, 0.01, -0.02]],
        )
        plots = spice_engine.parse_raw(op + tran)
        self.assertAlmostEqual(plots["op"].values[0][1], 9.0)
        self.assertEqual(len(plots["tran"].values), 2)
        self.assertAlmostEqual(plots["tran"].values[1][2], -0.02)

    def test_missing_binary_marker_is_reported(self):
        with self.assertRaises(SimulationError) as ctx:
            spice_engine.parse_raw(b"Plotname: AC Analysis\nFlags: complex\n")
        self.assertIn("raw", str(ctx.exception).lower())


class TestBuildNetlist(unittest.TestCase):
    def test_netlist_contains_expected_directives_and_scaled_values(self):
        text = spice_engine.build_netlist(sample_input(), "model text", "Q2N3904")
        self.assertIn(".include model.bjt", text)
        self.assertIn(".op", text)
        self.assertIn(".ac dec 100 1 10Meg", text)
        self.assertIn(".tran", text)
        self.assertIn("SIN(0 10m 1k) AC 10m 0", text)
        self.assertIn("R1   vcc b  100k", text)
        self.assertIn("Q1   c b e Q2N3904", text)
        self.assertNotIn(".print", text)
        self.assertNotIn(".control", text)

    def test_pulse_source_has_no_ac_excitation(self):
        text = spice_engine.build_netlist(
            sample_input(source="dc_pulse", amplitude=50e-3, frequency=2_000.0),
            "model text",
            "Q2N3904",
        )
        self.assertIn("PULSE(", text)
        self.assertIn("AC 0 0", text)

    def test_unknown_analysis_is_rejected(self):
        with self.assertRaises(ValueError):
            spice_engine.build_netlist(sample_input(analysis="fourier"), "model", "Q")


class TestAnalysis(unittest.TestCase):
    def test_operating_point_derives_currents_from_spice_nodes(self):
        plot = spice_engine.Plot(
            "Operating Point",
            ("v(b)", "v(e)", "v(c)", "v(vcc)"),
            "real",
            ((2.0, 1.3, 9.0, 12.0),),
        )
        op = spice_engine.analyze_op(plot, sample_input())
        self.assertAlmostEqual(op["vbe"], 0.7)
        self.assertAlmostEqual(op["vce"], 7.7)
        self.assertAlmostEqual(op["ic_ma"], 1.363636, places=4)
        self.assertAlmostEqual(op["ie_ma"], 1.3)

    def test_ac_gain_phase_and_cutoffs(self):
        freqs = [10.0, 100.0, 1_000.0, 10_000.0, 100_000.0]
        gains_db = [0.0, 38.0, 40.0, 38.0, 0.0]
        rows = []
        for f, gain_db in zip(freqs, gains_db):
            vin = 0.01
            mag = vin * 10 ** (gain_db / 20)
            rows.append([complex(f, 0.0), complex(vin, 0.0), complex(-mag, 0.0)])
        plot = spice_engine.Plot(
            "AC Analysis",
            ("frequency", "v(in)", "v(out)"),
            "complex",
            tuple(tuple(row) for row in rows),
        )
        ac = spice_engine.analyze_ac(plot)
        self.assertAlmostEqual(ac["midband_gain_db"], 40.0)
        self.assertAlmostEqual(ac["midband_phase_deg"], -180.0, places=3)
        self.assertLess(ac["f_low_hz"], 100.0)
        self.assertGreater(ac["f_high_hz"], 10_000.0)
        self.assertEqual(len(ac["gain_db"]), 5)

    def test_transient_peak_to_peak_and_inversion(self):
        plot = spice_engine.Plot(
            "Transient Analysis",
            ("time", "v(in)", "v(out)"),
            "real",
            (
                (0.0, 0.0, 0.0),
                (0.00025, 0.01, -0.02),
                (0.0005, 0.0, 0.0),
                (0.00075, -0.01, 0.02),
                (0.001, 0.0, 0.0),
            ),
        )
        tran = spice_engine.analyze_tran(plot)
        self.assertAlmostEqual(tran["vin_pp"], 0.02)
        self.assertAlmostEqual(tran["vout_pp"], 0.04)
        self.assertAlmostEqual(tran["vin_pp_mv"], 20.0)
        self.assertAlmostEqual(tran["vout_pp_mv"], 40.0)
        self.assertTrue(tran["inverted"])
        self.assertAlmostEqual(tran["gain"], 2.0)


class TestResolveNgspice(unittest.TestCase):
    def test_env_override_takes_priority(self):
        with patch.dict(spice_engine.os.environ, {"NGSPICE_BIN": "custom-ngspice"}):
            self.assertEqual(spice_engine.resolve_ngspice(), "custom-ngspice")

    def test_windows_fallback_list_contains_installed_msys2_binary(self):
        self.assertIn(r"C:\msys64\ucrt64\bin\ngspice.exe", spice_engine.NGSPICE_FALLBACKS)


class TestSvg(unittest.TestCase):
    def test_line_chart_embeds_data_and_axis_labels(self):
        svg = spice_engine.line_chart_svg(
            [("Vin", [0.0, 1.0], [0.0, 0.01]), ("Vout", [0.0, 1.0], [0.0, -0.02])],
            x_label="Time (ms)",
            y_label="Voltage (V)",
        )
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("Time (ms)", svg)
        self.assertIn("Voltage (V)", svg)
        self.assertIn("Vin", svg)
        self.assertIn("Vout", svg)
        self.assertIn("<polyline", svg)


class TestRunSimulation(unittest.TestCase):
    def test_success_reads_raw_and_passes_safe_command(self):
        raw = make_raw(
            "Operating Point",
            "real",
            ["v(b)", "v(e)", "v(c)", "v(vcc)"],
            [[2.0, 1.3, 9.0, 12.0]],
        )
        log = "Note: No compatibility mode selected!\nCommand: ngspice-47, Build Mon Sep  7 2026\n"

        def fake_run(args, **kwargs):
            cwd = Path(kwargs["cwd"])
            (cwd / "run.raw").write_bytes(raw)
            (cwd / "run.log").write_text(log, encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch.object(spice_engine.subprocess, "run", side_effect=fake_run) as run_mock:
            result = spice_engine.run_simulation(sample_input(analysis="op"))

        args = run_mock.call_args.args[0]
        self.assertIsInstance(args, list)
        self.assertEqual(args[1:5], ["-b", "-o", "run.log", "-r"])
        self.assertFalse(run_mock.call_args.kwargs.get("shell", False))
        self.assertGreater(run_mock.call_args.kwargs["timeout"], 0)
        self.assertAlmostEqual(result.op["vce"], 7.7)
        self.assertIn("ngspice-47", result.version)
        self.assertEqual(result.model_label, "Local reference model (not instructor-verified)")

    def test_failed_process_reports_log_tail(self):
        def fake_run(args, **kwargs):
            cwd = Path(kwargs["cwd"])
            (cwd / "run.log").write_text("Error: model not found\n", encoding="utf-8")
            return SimpleNamespace(returncode=1, stdout="", stderr="")

        with patch.object(spice_engine.subprocess, "run", side_effect=fake_run):
            with self.assertRaises(SimulationError) as ctx:
                spice_engine.run_simulation(sample_input())
        self.assertIn("model not found", str(ctx.exception))

    def test_timeout_is_reported(self):
        with patch.object(
            spice_engine.subprocess,
            "run",
            side_effect=spice_engine.subprocess.TimeoutExpired(["ngspice"], 30),
        ):
            with self.assertRaises(SimulationError) as ctx:
                spice_engine.run_simulation(sample_input())
        self.assertIn("timeout", str(ctx.exception).lower())

    def test_missing_lab_model_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(spice_engine, "PROJECT_ROOT", Path(tmp)):
                with self.assertRaises(SimulationError) as ctx:
                    spice_engine.resolve_model(sample_input(model_source="lab_reference"))
        self.assertIn("lab_reference", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
