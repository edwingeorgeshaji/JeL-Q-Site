import json
import unittest

import numpy as np
from scipy.linalg import expm

from dispatch import ROOT, build_problem, qaoa_state, solve_qaoa


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/'scenarios.json').read_text())

    def test_qubo_matches_physical_objective_all_states(self):
        p = build_problem(self.config, 80)
        direct = p['cost'] + p['penalty']*(p['supply']-p['demand'])**2
        np.testing.assert_allclose(p['energies'], direct)
        self.assertTrue(p['feasible'][np.argmin(p['energies'])])
        # 3 solar blocks * 8 + 3 wind * 12 + 2 battery * 25.
        self.assertEqual(p['cost'][np.argmin(p['energies'])], 110)

    def test_statevector_matches_independent_dense_unitary(self):
        energies = np.array([1., 2., 4., 8.])
        params = [.37, .29, .14, .51]
        x = np.array([[0, 1], [1, 0]])
        mixer = np.kron(x, np.eye(2)) + np.kron(np.eye(2), x)
        state = np.ones(4, dtype=complex)/2
        for gamma, beta in np.array(params).reshape(-1, 2):
            state = expm(-1j*beta*mixer) @ (np.exp(-1j*gamma*energies)*state)
        actual = qaoa_state(params, energies, 2)
        np.testing.assert_allclose(actual, state, atol=1e-12)
        self.assertAlmostEqual(float(np.vdot(actual, actual).real), 1)

    def test_capacity_and_demand_validation(self):
        self.assertFalse(build_problem(self.config, 160)['feasible'].any())
        for demand in [-10, 15]:
            with self.assertRaises(ValueError):
                build_problem(self.config, demand)

    def test_sampling_reproducible_and_selected_only_from_counts(self):
        tiny = dict(block_kwh=10, sources=[dict(name='A',cost_per_block_inr=2,weights=[1,2])])
        p = build_problem(tiny, 20)
        a = solve_qaoa(p, depth=1, starts=1, maxiter=30, shots=256)
        b = solve_qaoa(p, depth=1, starts=1, maxiter=30, shots=256)
        np.testing.assert_array_equal(a['counts'], b['counts'])
        self.assertEqual(int(a['counts'].sum()), 256)
        if a['selected'] is not None:
            self.assertGreater(a['counts'][a['selected']], 0)
            self.assertTrue(p['feasible'][a['selected']])


if __name__ == '__main__':
    unittest.main()
