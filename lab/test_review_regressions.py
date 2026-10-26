"""Publication review regressions: adversarial cases missed by the original suite."""
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
from agent_loop import Executor, CompatibleAPI, run
from lab import Store, ToolError, grade, run_task, evaluate, compare
from gradient_lab import softmax
import math
TASKS=json.loads((Path(__file__).parent/'tasks.json').read_text())
def call(cid,name='get_order',args='{"order_id":"O-102"}'):
    return {'id':cid,'type':'function','function':{'name':name,'arguments':args}}
class Script:
    def __init__(self,steps): self.steps=iter(steps)
    def complete(self,messages): return next(self.steps),{'total_tokens':7}
def reply(calls): return {'role':'assistant','tool_calls':calls}
class ReviewRegressions(unittest.TestCase):
    def setUp(self): self.store=Store(); self.store.seed(TASKS[0])
    def tearDown(self): self.store.close()
    def executor(self): return Executor(self.store,'U-8',True,'op1',target_order_id='O-102',approved_amount_cents=8000)
    def test_cross_turn_conflict_preflight_prevents_earlier_write(self):
        model=Script([reply([call('old')]),reply([call('new','request_refund'),call('old','get_policy','{}')])])
        with self.assertRaises(ValueError): run(model,self.executor(),'refund')
        self.assertEqual(self.store.snapshot()['refunds'],[])
    def test_bad_call_shape_rejected_before_any_write(self):
        model=Script([reply([call('write','request_refund'),{'id':'bad','function':None}])])
        with self.assertRaises(ValueError): run(model,self.executor(),'refund')
        self.assertEqual(self.store.snapshot()['refunds'],[])
    def test_confirmation_cannot_transfer_to_second_order(self):
        self.store.db.execute("INSERT INTO orders VALUES('O-103','U-8',6000,0,2)"); self.store.db.commit()
        with self.assertRaises(ToolError): self.executor().call('request_refund',{'order_id':'O-103'})
        self.assertEqual(self.store.snapshot()['refunds'],[])
    def test_final_call_usage_is_recorded(self):
        result=run(Script([{'role':'assistant','content':'done'}]),self.executor(),'refund')
        events=[e for e in result['events'] if e['event']=='model_response']
        self.assertEqual(sum(e['usage']['total_tokens'] for e in events),7)
    def test_trace_contains_action_arguments(self):
        result=run(Script([reply([call('one')])]),self.executor(),'refund',max_steps=1)
        self.assertTrue(any(e.get('event')=='tool_call' and e.get('arguments')=={'order_id':'O-102'} for e in result['events']))
    def test_grader_checks_status_in_ledger(self):
        task=TASKS[-1]; result=run_task(task,'safe'); result['snapshot']['refunds'][0]['status']='completed'
        self.assertFalse(grade(task,result)['passed'])
    def test_grader_checks_balance_reconciliation(self):
        task=TASKS[0]; result=run_task(task,'safe'); result['snapshot']['orders'][0]['refunded']=0
        self.assertFalse(grade(task,result)['passed'])
    def test_grader_rejects_missing_order_snapshot(self):
        task=TASKS[0]; result=run_task(task,'safe'); result['snapshot']['orders']=[]
        self.assertFalse(grade(task,result)['passed'])
    def test_compare_detects_changed_content_with_same_ids(self):
        changed=copy.deepcopy(TASKS); changed[0]['input']='different request'
        with self.assertRaises(ValueError): compare(evaluate('safe',TASKS),evaluate('safe',changed))
    def test_compare_rejects_duplicate_ids(self):
        report=evaluate('safe',TASKS); report['runs'].append(copy.deepcopy(report['runs'][0]))
        with self.assertRaises(ValueError): compare(report,report)
    def test_confirmation_must_be_boolean(self):
        with self.assertRaises(ToolError): self.store.refund('O-102','U-8','false','x')
        self.assertEqual(self.store.snapshot()['refunds'],[])
    def test_api_rejects_unknown_finish_reason(self):
        env={'AGENT_API_BASE':'https://example.invalid/v1','AGENT_API_KEY':'dummy-test-value','AGENT_MODEL':'fixture'}
        data={'choices':[{'finish_reason':'future_unknown','message':reply([call('x','request_refund')])}]}
        with patch.dict('os.environ',env), patch('urllib.request.OpenerDirector.open',return_value=io.BytesIO(json.dumps(data).encode())):
            with self.assertRaises(RuntimeError): CompatibleAPI().complete([])
    def test_api_does_not_forward_credentials_on_redirect(self):
        env={'AGENT_API_BASE':'https://example.invalid/v1','AGENT_API_KEY':'dummy-test-value','AGENT_MODEL':'fixture'}
        with patch.dict('os.environ',env): client=CompatibleAPI()
        # Offline inspection only; no connection or real credential is used.
        opener=getattr(client,'opener',urllib.request.build_opener())
        handler=next(h for h in opener.handlers if isinstance(h,urllib.request.HTTPRedirectHandler))
        request=urllib.request.Request('https://example.invalid/v1/chat/completions',headers={'Authorization':'Bearer dummy-test-value'})
        try: redirected=handler.redirect_request(request,None,302,'Found',{},'https://other.invalid')
        except urllib.error.HTTPError as exc:
            exc.close(); return
        self.assertIsNone(redirected,'Authenticated API requests must reject redirects')
    def test_cross_entropy_gradient_matches_finite_difference(self):
        z=[.4,-.2,.9]; y=1; eps=1e-6; p=softmax(z)
        for i in range(3):
            plus=z[:]; minus=z[:]; plus[i]+=eps; minus[i]-=eps
            numeric=(-math.log(softmax(plus)[y])+math.log(softmax(minus)[y]))/(2*eps)
            self.assertAlmostEqual(numeric,p[i]-(i==y),places=7)
    def test_dpo_gradient_matches_finite_difference(self):
        theta=.7; beta=.5; eps=1e-6
        loss=lambda t: math.log1p(math.exp(-beta*t))
        numeric=(loss(theta+eps)-loss(theta-eps))/(2*eps)
        self.assertAlmostEqual(numeric,-beta/(1+math.exp(beta*theta)),places=7)
    def test_approved_amount_is_not_silently_expanded(self):
        executor=self.executor()
        self.store.db.execute("UPDATE orders SET paid=9000 WHERE id='O-102'"); self.store.db.commit()
        result=executor.call('request_refund',{'order_id':'O-102'})
        self.assertEqual(result['amount_cents'],8000)
    def test_reused_call_identity_replays_without_second_write(self):
        action=call('same','request_refund')
        model=Script([reply([action]),reply([action]),{'role':'assistant','content':'done'}])
        result=run(model,self.executor(),'refund')
        self.assertEqual(len(result['verified_state']['refunds']),1)
        self.assertEqual(sum(e['usage']['total_tokens'] for e in result['events'] if e['event']=='model_response'),21)
    def test_supported_api_tool_response_is_preserved(self):
        env={'AGENT_API_BASE':'https://example.invalid/v1','AGENT_API_KEY':'dummy-test-value','AGENT_MODEL':'fixture'}
        message=reply([call('one')])
        data={'choices':[{'finish_reason':'tool_calls','message':message}],'usage':{'total_tokens':7}}
        with patch.dict('os.environ',env), patch('urllib.request.OpenerDirector.open',return_value=io.BytesIO(json.dumps(data).encode())):
            result,usage=CompatibleAPI().complete([])
        self.assertEqual(result,message);self.assertEqual(usage['total_tokens'],7)
if __name__=='__main__': unittest.main()
