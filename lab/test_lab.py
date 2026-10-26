import concurrent.futures
import json
from pathlib import Path
import tempfile
import unittest
from lab import Store, ToolError, evaluate, grade, run_task, wilson, calculate_cost, compare
from gradient_lab import ce_training, preference_training
TASKS=json.loads((Path(__file__).parent/'tasks.json').read_text())
def task(s): return next(t for t in TASKS if t['scenario']==s)
class BusinessInvariants(unittest.TestCase):
    def setUp(self):
        self.store=Store(); self.store.seed(task('valid'))
    def tearDown(self): self.store.close()
    def test_requires_identity(self):
        with self.assertRaises(ToolError): self.store.refund('O-102','U-99',True,'x')
        self.assertEqual(self.store.snapshot()['refunds'],[])
    def test_requires_confirmation(self):
        with self.assertRaises(ToolError): self.store.refund('O-102','U-8',False,'x')
    def test_blocks_expired(self):
        self.store.seed(task('expired'))
        with self.assertRaises(ToolError): self.store.refund('O-102','U-8',True,'x')
    def test_same_key_returns_same_result(self):
        a=self.store.refund('O-102','U-8',True,'x')
        b=self.store.refund('O-102','U-8',True,'x')
        self.assertEqual(a['refund_id'],b['refund_id']); self.assertTrue(b['replayed'])
        self.assertEqual(len(self.store.snapshot()['refunds']),1)
    def test_key_parameter_conflict(self):
        self.store.refund('O-102','U-8',True,'x',1000)
        with self.assertRaisesRegex(ToolError,'IDEMPOTENCY_CONFLICT'):
            self.store.refund('O-102','U-8',True,'x',2000)
    def test_new_key_cannot_exceed_balance(self):
        self.store.refund('O-102','U-8',True,'x')
        with self.assertRaisesRegex(ToolError,'AMOUNT_DENIED'):
            self.store.refund('O-102','U-8',True,'y')
    def test_partial_refund_remaining(self):
        self.store.seed(task('partial'))
        self.assertEqual(self.store.refund('O-102','U-8',True,'x')['amount_cents'],5000)
    def test_response_lost_is_committed(self):
        with self.assertRaises(TimeoutError):
            self.store.refund('O-102','U-8',True,'x',lose_response=True)
        self.assertEqual(len(self.store.snapshot()['refunds']),1)
        self.assertTrue(self.store.refund('O-102','U-8',True,'x',lose_response=True)['replayed'])
    def test_rejects_invalid_amount(self):
        for amount in [-1,0,1.5,True]:
            with self.assertRaises(ToolError): self.store.refund('O-102','U-8',True,'x',amount)
    def test_concurrent_retry_one_side_effect(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'state.db'; seed=Store(path); seed.seed(task('valid')); seed.close()
            def call():
                s=Store(path)
                try: return s.refund('O-102','U-8',True,'same')
                finally: s.close()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                results=list(ex.map(lambda _:call(),range(2)))
            s=Store(path)
            self.assertEqual(len(s.snapshot()['refunds']),1)
            self.assertEqual(results[0]['refund_id'],results[1]['refund_id']); s.close()
class Measurement(unittest.TestCase):
    def test_reference_contracts(self):
        self.assertEqual(evaluate('safe',TASKS)['summary']['passed'],len(TASKS))
    def test_naive_can_fail_despite_success_message(self):
        t=task('response_lost'); r=run_task(t,'naive')
        self.assertEqual(r['utterance'],'completed')
        self.assertFalse(grade(t,r)['checks']['ledger_count'])
    def test_grader_rejects_tampered_ledger(self):
        t=task('valid'); r=run_task(t,'safe'); r['snapshot']['refunds'][0]['amount']=1
        self.assertFalse(grade(t,r)['passed'])
    def test_pending_not_completed(self):
        t=task('pending'); r=run_task(t,'safe'); r['utterance']='completed'
        self.assertFalse(grade(t,r)['checks']['communication'])
    def test_compare_rejects_different_tasks(self):
        with self.assertRaises(ValueError): compare(evaluate('safe',TASKS),evaluate('safe',TASKS[:-1]))
    def test_wilson_edges(self):
        low,high=wilson(0,100); self.assertEqual(low,0); self.assertGreater(high,.03)
        low,high=wilson(100,100); self.assertLess(low,.97); self.assertEqual(high,1)
    def test_cost_accounting(self):
        self.assertAlmostEqual(calculate_cost(2000,8000,1000,1,.1,4),.0068)
    def test_toy_losses_decrease(self):
        ce=ce_training()['history']; pref=preference_training()['history']
        self.assertLess(ce[-1]['cross_entropy'],ce[0]['cross_entropy'])
        self.assertLess(pref[-1]['dpo_loss'],pref[0]['dpo_loss'])
if __name__=='__main__': unittest.main()
