import json
from pathlib import Path
import unittest
from agent_loop import Executor, ReplayModel, run
from lab import Store, ToolError
class LoopTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(); self.store.seed(json.loads((Path(__file__).parent/'tasks.json').read_text())[0])
    def tearDown(self): self.store.close()
    def executor(self,confirmed=True): return Executor(self.store,'U-8',confirmed,'op1',target_order_id='O-102',approved_amount_cents=8000 if confirmed else None)
    def test_replay_with_confirmation(self):
        r=run(ReplayModel(),self.executor(),'refund')
        self.assertEqual(len(r['verified_state']['refunds']),1)
    def test_no_confirmation_no_write(self):
        r=run(ReplayModel(),self.executor(False),'refund')
        self.assertEqual(r['verified_state']['refunds'],[])
        self.assertTrue(any('CONFIRMATION_REQUIRED' in str(e) for e in r['events']))
    def test_unavailable_tool(self):
        with self.assertRaises(ToolError): self.executor().call('export_all',{})
    def test_model_cannot_choose_principal(self):
        with self.assertRaises(ToolError): self.executor().call('get_order',{'order_id':'O-102','user_id':'admin'})
    def test_budget_stops_loop(self):
        r=run(ReplayModel(),self.executor(),'refund',max_steps=1)
        self.assertEqual(r['status'],'budget_exhausted');self.assertEqual(r['verified_state']['refunds'],[])
    def test_bad_json_is_observation(self):
        class Bad:
            def complete(self,m): return {'role':'assistant','tool_calls':[{'id':'x','type':'function','function':{'name':'get_order','arguments':'{'}}]},{}
        r=run(Bad(),self.executor(),'refund',max_steps=1)
        self.assertFalse(r['events'][-1]['result']['ok'])
    def test_duplicate_ids_rejected_before_execution(self):
        class Bad:
            def complete(self,m):
                c={'id':'x','type':'function','function':{'name':'request_refund','arguments':'{"order_id":"O-102"}'}}
                return {'role':'assistant','tool_calls':[c,c]},{}
        with self.assertRaises(ValueError): run(Bad(),self.executor(),'refund')
        self.assertEqual(self.store.snapshot()['refunds'],[])
if __name__=='__main__': unittest.main()
