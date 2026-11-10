import unittest

from app import app


class TestWeb(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_get_index_shows_form(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', res.get_data(as_text=True))

    def test_post_calculates_reference_case(self):
        res = self.client.post("/calculate", data={
            "vcc": "12", "r1": "100", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        })
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("8.052", body)   # VCE
        self.assertIn("1.230", body)   # IC (mA)

    def test_empty_form_shows_errors_for_every_field(self):
        res = self.client.post("/calculate", data={})
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body.count("ต้องกรอก"), 7)

    def test_non_numeric_value_is_reported(self):
        res = self.client.post("/calculate", data={
            "vcc": "abc", "r1": "100", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        })
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("ตัวเลข", body)

    def test_value_with_comma_is_reported_not_crash(self):
        res = self.client.post("/calculate", data={
            "vcc": "12", "r1": "100,000", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("ตัวเลข", res.get_data(as_text=True))

    def test_zero_resistor_error_comes_from_core(self):
        res = self.client.post("/calculate", data={
            "vcc": "12", "r1": "0", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        })
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("R1", body)

    def test_cutoff_warning_is_shown(self):
        res = self.client.post("/calculate", data={
            "vcc": "5", "r1": "100", "r2": "10",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        })
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Cutoff", body)

    def test_extreme_values_do_not_crash(self):
        res = self.client.post("/calculate", data={
            "vcc": "12", "r1": "1000000000000", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "1000000", "vbe": "0.7",
        })
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("nan", body)
        self.assertNotIn("inf", body)

    def test_huge_resistors_give_finite_result(self):
        res = self.client.post("/calculate", data={
            "vcc": "12", "r1": "1e305", "r2": "1e305",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        })
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("nan", body)
        self.assertNotIn("inf", body)

    def test_infinite_input_is_rejected(self):
        res = self.client.post("/calculate", data={
            "vcc": "1e309", "r1": "100", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        })
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("จำนวนจำกัด", body)
        self.assertNotIn("status--ok", body)


class TestUnitSelection(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _post(self, **overrides):
        data = {
            "vcc": "12", "r1": "100", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7",
        }
        data.update(overrides)
        return self.client.post("/calculate", data=data)

    def test_index_renders_unit_selectors(self):
        body = self.client.get("/").get_data(as_text=True)
        for field in ("r1", "r2", "rc", "re"):
            self.assertIn(f'name="{field}_unit"', body)
            for unit in ("ohm", "kohm", "mohm"):
                self.assertIn(f'value="{unit}"', body)
        for field in ("vcc", "vbe"):
            self.assertIn(f'name="{field}_unit"', body)
            for unit in ("v", "mv"):
                self.assertIn(f'value="{unit}"', body)
        self.assertNotIn('name="beta_unit"', body)

    def test_ohm_unit_matches_kohm_result(self):
        res = self._post(
            r1="100000", r1_unit="ohm",
            r2="22000", r2_unit="ohm",
            rc="2200", rc_unit="ohm",
            re="1000", re_unit="ohm",
        )
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("8.052", body)   # VCE
        self.assertIn("1.230", body)   # IC (mA)

    def test_mohm_unit_scales_correctly(self):
        res = self._post(
            r1="0.1", r1_unit="mohm",
            r2="0.022", r2_unit="mohm",
            rc="0.0022", rc_unit="mohm",
            re="0.001", re_unit="mohm",
        )
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("8.052", body)
        self.assertIn("1.230", body)

    def test_millivolt_unit_scales_correctly(self):
        res = self._post(vcc="12000", vcc_unit="mv", vbe="700", vbe_unit="mv")
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("8.052", body)
        self.assertIn("1.230", body)

    def test_invalid_unit_is_reported(self):
        res = self._post(r1_unit="bogus")
        body = res.get_data(as_text=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("R1 หน่วยไม่ถูกต้อง", body)
        self.assertNotIn("status--ok", body)

    def test_selected_unit_is_kept_after_submit(self):
        body = self._post(r1="100000", r1_unit="ohm").get_data(as_text=True)
        self.assertIn('value="ohm" selected', body)
        self.assertIn('value="100000"', body)
