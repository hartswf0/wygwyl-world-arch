"""python3 shots/suite/lib/tests/test_scale.py  (same cases as test_scale.mjs)"""
import json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import scale as S  # noqa: E402

C = json.load(open(os.path.join(HERE, 'scale_cases.json')))
E, SET = C['expect'], C['set']


class T(unittest.TestCase):
    def near(self, a, b, eps=1e-3):
        self.assertLessEqual(abs(a - b), eps, f'{a} != {b}')

    def test_camera(self):
        self.near(S.camera_height_cm(SET), E['camera_height_cm'])

    def test_ppc(self):
        self.near(S.px_per_cm_at(SET, 1050), E['ppc_at_ground'])
        self.near(S.px_per_cm_at(SET, 867), E['ppc_at_horizon'])
        self.near(S.px_per_cm_at(SET, 958.5), E['ppc_at_958_5'])

    def test_depth(self):
        self.near(S.foot_y_for_depth(SET, 12), E['foot_y_at_12m'])
        self.near(S.depth_for_foot_y(SET, 958.5), E['depth_at_958_5'])

    def test_horizon_rule(self):
        cam = dict(height_cm=S.camera_height_cm(SET), build_height_cm=1)
        for y in (900, 958.5, 1050, 1200):
            self.near(S.place(cam, SET, 0, y)['head_top_y'], E['camera_tall_head_on_horizon'])

    def test_place(self):
        self.near(S.place(C['poet'], SET, 500, 1050)['height_px'], E['poet_height_px_at_ground'])
        with self.assertRaises(ValueError):
            S.place(C['poet'], SET, 0, 800)

    def test_part_and_reach(self):
        self.near(S.part_scale(C['thigh'], C['poet'], S.px_per_cm_at(SET, 1050)), E['thigh_scale_at_ground'], 1e-4)
        self.near(S.reach_top_cm(C['poet']), E['poet_reach_top_cm'])
        self.near(S.reach_top_cm(C['child']), E['child_reach_top_cm'])
        self.near(S.prop_scale(C['child'], 'action', 94.8), E['child_chair_scale'], 1e-4)
        self.assertEqual(S.prop_scale(C['child'], 'set'), 1.0)

    def test_check(self):
        want = S.place(C['poet'], SET, 0, 1050)['height_px']
        self.assertFalse(S.check_placed(C['poet'], SET, 1050, want * 1.06)['ok'])
        self.assertTrue(S.check_placed(C['poet'], SET, 1050, want * 1.02)['ok'])


if __name__ == '__main__':
    unittest.main()
