#!/usr/bin/env python3
"""Paired cluster bootstrap illustration. Does not fix sampling bias."""
import collections
import json
import random

def quantile(sorted_values,p):
    if not sorted_values: raise ValueError('empty distribution')
    position=(len(sorted_values)-1)*p
    low=int(position);high=min(low+1,len(sorted_values)-1);fraction=position-low
    return sorted_values[low]*(1-fraction)+sorted_values[high]*fraction

def cluster_bootstrap(rows,repeats=2000,seed=7):
    if not rows or repeats<1: raise ValueError('nonempty rows and positive repeats required')
    groups=collections.defaultdict(list)
    for row in rows:
        if row['a'] not in (0,1) or row['b'] not in (0,1): raise ValueError('binary outcomes required')
        groups[row['group']].append(row['b']-row['a'])
    keys=list(groups);rng=random.Random(seed);estimates=[]
    for _ in range(repeats):
        selected=[rng.choice(keys) for _ in keys]
        values=[v for key in selected for v in groups[key]]
        estimates.append(sum(values)/len(values))
    estimates.sort()
    return {'difference':sum(r['b']-r['a'] for r in rows)/len(rows),
            'percentile_interval':[quantile(estimates,.025),quantile(estimates,.975)],
            'groups':len(groups),'rows':len(rows),'repeats':repeats,'seed':seed}

if __name__=='__main__':
    # Eight independent-style clusters in the illustration, with four correlated tasks each.
    patterns=[(0,1),(0,1),(0,1),(1,1),(1,1),(1,0),(0,0),(1,1)]
    rows=[{'group':f'user-{i}','a':a,'b':b} for i,(a,b) in enumerate(patterns) for _ in range(4)]
    clustered=cluster_bootstrap(rows)
    wrong_independence=cluster_bootstrap([{**r,'group':str(i)} for i,r in enumerate(rows)])
    print(json.dumps({'warning':'Synthetic illustration; eight clusters are a small sample, and bootstrap does not establish representativeness.',
                      'clustered':clustered,'incorrect_row_independence_assumption':wrong_independence},indent=2))
