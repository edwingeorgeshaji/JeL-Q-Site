import unittest
from phase2 import audit_counts
from dispatch import build_problem


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        config=dict(block_kwh=10,sources=[dict(name='A',weights=[1,2],cost_per_block_inr=2)])
        self.p=build_problem(config,20)
        self.row=dict(counts={'10':7,'00':3},shots=10,best_feasible_sample=dict(state_index=2,cost_inr=4))

    def test_recompute_quality_from_counts(self):
        result=audit_counts(self.row,self.p)
        self.assertEqual(result['feasible_shots'],7)
        self.assertEqual(result['optimal_shots'],7)

    def test_reject_inconsistent_evidence(self):
        self.row['shots']=11
        with self.assertRaises(ValueError):audit_counts(self.row,self.p)
        self.row['shots']=10
        self.row['best_feasible_sample']['cost_inr']=0
        with self.assertRaises(ValueError):audit_counts(self.row,self.p)
