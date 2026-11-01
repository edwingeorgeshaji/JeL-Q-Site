import unittest
import numpy as np
from resilience import DEFAULT,exact_plan,outage,recovery,validate,quantum


class ResilienceTests(unittest.TestCase):
    def test_cost_reserve_and_battery_carryover(self):
        i=DEFAULT.copy()
        _,_,cheap,_=exact_plan(i,0)
        _,_,ready,_=exact_plan(i,30)
        self.assertEqual(cheap['cost_inr'],110)
        self.assertEqual(ready['cost_inr'],170)
        self.assertEqual(outage(i,cheap)['shortfall'],20)
        self.assertEqual(outage(i,ready)['shortfall'],0)
        self.assertEqual(outage(i,cheap)['remaining_after'],0)

    def test_recovery_minimal_in_tested_set(self):
        r=recovery(DEFAULT,0)
        self.assertEqual(r['added_kwh'],20)
        self.assertEqual([a['success'] for a in r['attempts']],[False,False,True])

    def test_extra_energy_cannot_bypass_power(self):
        i=DEFAULT|{'critical':40}
        self.assertIsNone(recovery(i,0)['added_kwh'])

    def test_capacity_encoding_matches_penalty_and_bounds(self):
        for reserve in [0,10,20,30]:
            cfg,p,_,_=exact_plan(DEFAULT,reserve)
            np.testing.assert_allclose(p['energies'],p['cost']+p['penalty']*(p['supply']-p['demand'])**2)
            for index in np.flatnonzero(p['feasible']):
                from dispatch import allocation
                plan=allocation(int(index),p,cfg)
                self.assertLessEqual(plan['sources_kwh'].get('Battery',0),30-reserve)

    def test_validation_and_impossible_normal_demand(self):
        for i in [DEFAULT|{'reserve':40},DEFAULT|{'critical':-10},DEFAULT|{'power':40},DEFAULT|{'demand':85}]:
            with self.assertRaises(ValueError):validate(i)
        _,_,plan,_=exact_plan(DEFAULT|{'demand':160},0)
        self.assertIsNone(plan)
        self.assertIsNone(outage(DEFAULT,plan))

    def test_qiskit_measurements_are_actual_valid_samples(self):
        cfg,p,_,_=exact_plan(DEFAULT,30)
        t=quantum(cfg,p,iterations=12)
        self.assertEqual(sum(t['counts'].values()),2048)
        self.assertTrue(t['verified'])
        if t['plan']:
            self.assertGreater(t['counts'][t['plan']['bitstring']],0)
            self.assertTrue(t['plan']['feasible'])


if __name__=='__main__':unittest.main()
