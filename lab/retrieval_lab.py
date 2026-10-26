#!/usr/bin/env python3
"""Small lexical BM25 + metadata filtering lab. No embeddings or LLMs."""
import collections
import json
import math
import re

def tokens(text):
    # Teaching corpus uses spaces around meaningful Chinese terms.
    return re.findall(r'[a-z0-9]+|[\u4e00-\u9fff]+',text.lower())

DOCS=[
 {'id':'normal-v1','category':'normal','start':0,'end':20260701,'tenant':'shop-a','text':'普通 商品 退款 退货 期限 7 天 未拆封'},
 {'id':'normal-v2','category':'normal','start':20260701,'end':99999999,'tenant':'shop-a','text':'普通 商品 退款 退货 期限 14 天 未拆封'},
 {'id':'custom-v1','category':'custom','start':0,'end':99999999,'tenant':'shop-a','text':'定制 商品 退款 退货 不支持 无质量问题'},
 {'id':'digital-v1','category':'digital','start':0,'end':99999999,'tenant':'shop-a','text':'数字 商品 退款 下载 后 不支持'},
 {'id':'private-other','category':'normal','start':0,'end':99999999,'tenant':'shop-b','text':'普通 商品 退款 退货 期限 30 天 私有 政策'},
 {'id':'shipping','category':'shipping','start':0,'end':99999999,'tenant':'shop-a','text':'物流 商品 发货 时间 3 天'}
]
QUERIES=[
 {'text':'普通 商品 退款','category':'normal','date':20260601,'tenant':'shop-a','gold':'normal-v1'},
 {'text':'普通 商品 退款','category':'normal','date':20260801,'tenant':'shop-a','gold':'normal-v2'},
 {'text':'定制 商品 退款','category':'custom','date':20260801,'tenant':'shop-a','gold':'custom-v1'},
 {'text':'数字 商品 下载 退款','category':'digital','date':20260801,'tenant':'shop-a','gold':'digital-v1'}
]

def rank(query,filter_metadata=False,k1=1.5,b=.75):
    corpus=[tokens(d['text']) for d in DOCS];n=len(corpus)
    average=sum(map(len,corpus))/n
    df=collections.Counter(t for doc in corpus for t in set(doc))
    scores=[]
    for d,ts in zip(DOCS,corpus):
        if filter_metadata and not(d['tenant']==query['tenant'] and d['category']==query['category'] and d['start']<=query['date']<d['end']):
            continue
        tf=collections.Counter(ts);score=0.
        for t in tokens(query['text']):
            if not tf[t]: continue
            idf=math.log(1+(n-df[t]+.5)/(df[t]+.5))
            score+=idf*tf[t]*(k1+1)/(tf[t]+k1*(1-b+b*len(ts)/average))
        scores.append({'id':d['id'],'score':round(score,6)})
    return sorted(scores,key=lambda x:(-x['score'],x['id']))

def evaluate(filtered):
    result=[]
    for q in QUERIES:
        found=rank(q,filtered);ids=[d['id'] for d in found]
        rr=1/(ids.index(q['gold'])+1) if q['gold'] in ids else 0
        result.append({'query':q,'ranking':found,'recall_at_1':int(bool(ids) and ids[0]==q['gold']),'reciprocal_rank':rr})
    return {'metadata_filter':filtered,'recall_at_1':sum(x['recall_at_1'] for x in result)/len(result),
            'mrr':sum(x['reciprocal_rank'] for x in result)/len(result),'queries':result}
if __name__=='__main__':
    print(json.dumps({'warning':'Tiny synthetic corpus; no semantic retrieval or generalization claim.',
                      'raw':evaluate(False),'filtered':evaluate(True)},ensure_ascii=False,indent=2))
