#!/usr/bin/env python3
"""Tiny CPU experiments for loss functions. This is NOT LLM fine-tuning."""
import json
import math

def softmax(logits):
    peak=max(logits)
    exp=[math.exp(x-peak) for x in logits]
    return [x/sum(exp) for x in exp]

def ce_training():
    # Features: bias, is_eligible, is_confirmed. Actions: refund, deny, ask.
    data=[([1.,1.,1.],0),([1.,0.,1.],1),([1.,1.,0.],2),([1.,0.,0.],1)]
    weights=[[0.,0.,0.] for _ in range(3)]
    history=[]
    for epoch in range(201):
        loss=0.; grad=[[0.,0.,0.] for _ in range(3)]
        for x,y in data:
            p=softmax([sum(wi*xi for wi,xi in zip(w,x)) for w in weights])
            loss-=math.log(max(p[y],1e-15))/len(data)
            for k in range(3):
                for j in range(3):
                    grad[k][j]+=(p[k]-(k==y))*x[j]/len(data)
        if epoch in (0,20,100,200):
            history.append({"epoch":epoch,"cross_entropy":round(loss,5)})
        if epoch<200:
            for k in range(3):
                for j in range(3): weights[k][j]-=.5*grad[k][j]
    predictions=[]
    for x,y in data:
        p=softmax([sum(wi*xi for wi,xi in zip(w,x)) for w in weights])
        predictions.append({"x":x,"expected":y,"predicted":max(range(3),key=lambda k:p[k]),
                            "probabilities":[round(v,4) for v in p]})
    return {"history":history,"training_points":predictions,
            "limit":"Four hand-written points: no generalization claim."}

def preference_training():
    # Two possible responses. Their log-probability difference is theta.
    # Reference theta=0, so the DPO log-ratio difference is theta.
    theta=0.; beta=.5; hist=[]
    for step in range(101):
        margin=beta*theta
        loss=math.log1p(math.exp(-margin))
        if step in (0,20,100):
            hist.append({"step":step,"theta":round(theta,4),"dpo_loss":round(loss,5),
                         "probability_of_preferred":round(1/(1+math.exp(-theta)),5)})
        if step<100:
            gradient=-beta/(1+math.exp(margin))
            theta-=.2*gradient
    return {"history":hist,"limit":"Toy two-response DPO objective, no transformer, rollout or RL environment."}

if __name__=="__main__":
    print(json.dumps({"cross_entropy":ce_training(),"preference":preference_training()},indent=2))
