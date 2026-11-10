import unittest

from dc_bias import calculate_dc_bias


class TestForwardActive(unittest.TestCase):
    def test_reference_case_from_handout(self):
        r = calculate_dc_bias(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        )
        self.assertAlmostEqual(r.vth, 2.164, places=3)
        self.assertAlmostEqual(r.rth, 18_032.787, places=1)
        self.assertAlmostEqual(r.ib, 12.30e-6, delta=0.005e-6)
        self.assertAlmostEqual(r.ic, 1.230e-3, delta=0.0005e-3)
        self.assertAlmostEqual(r.ie, 1.242e-3, delta=0.0005e-3)
        self.assertAlmostEqual(r.ve, 1.242, places=3)
        self.assertAlmostEqual(r.vb, 1.942, places=3)
        self.assertAlmostEqual(r.vc, 9.294, places=3)
        self.assertAlmostEqual(r.vce, 8.052, places=3)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())


class TestValidation(unittest.TestCase):
    def _call(self, **over):
        args = dict(vcc=12.0, r1=100_000.0, r2=22_000.0,
                    rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        args.update(over)
        return calculate_dc_bias(**args)

    def test_zero_resistor_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._call(r1=0.0)
        self.assertIn("R1", str(ctx.exception))

    def test_negative_vcc_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._call(vcc=-1.0)
        self.assertIn("VCC", str(ctx.exception))

    def test_zero_beta_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._call(beta=0.0)
        self.assertIn("beta", str(ctx.exception))

    def test_negative_vbe_is_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self._call(vbe=-0.1)
        self.assertIn("VBE", str(ctx.exception))


class TestOperatingRegion(unittest.TestCase):
    def test_cutoff_when_vth_below_vbe(self):
        r = calculate_dc_bias(vcc=5.0, r1=100_000.0, r2=10_000.0,
                              rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ve, 0.0)
        self.assertAlmostEqual(r.vb, r.vth, places=6)
        self.assertAlmostEqual(r.vc, 5.0, places=6)
        self.assertTrue(r.warnings)

    def test_cutoff_when_vth_equals_vbe(self):
        # VTH = 12*R2/(R1+R2) = 0.70  ->  R2 = 70000/11.3
        r = calculate_dc_bias(vcc=12.0, r1=100_000.0, r2=70000.0 / 11.3,
                              rc=1_000.0, re=1_000.0, beta=100.0, vbe=0.70)
        self.assertAlmostEqual(r.vth, 0.70, places=6)
        self.assertEqual(r.region, "cutoff")

    def test_saturation_when_vce_at_or_below_0v3(self):
        r = calculate_dc_bias(vcc=5.0, r1=100_000.0, r2=47_000.0,
                              rc=10_000.0, re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(r.region, "saturation")
        self.assertLessEqual(r.vce, 0.3)
        self.assertTrue(r.warnings)

    def test_no_warning_in_active_region(self):
        r = calculate_dc_bias(vcc=12.0, r1=100_000.0, r2=22_000.0,
                              rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())
