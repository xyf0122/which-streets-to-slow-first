"""Whole-location evaluation using fixed scores and observed outcomes."""
import hashlib, math

def sha(b): return hashlib.sha256(b).hexdigest()

def ordered(scores,seed='TRA_METHOD_V01'):
    if any(not math.isfinite(v) or v<0 for v in scores.values()):raise ValueError('invalid score')
    return sorted(scores,key=lambda cid:(-scores[cid],sha((seed+'|'+cid).encode()),cid))


def performance(values,scores,K,seed='TRA_METHOD_V01'):
    if K<0 or not isinstance(K,int):raise ValueError('invalid K')
    if set(values)!=set(scores):raise ValueError('method-specific missing scores')
    if any(not math.isfinite(v) or v<0 for v in values.values()):raise ValueError('invalid severity')
    ids=ordered(scores,seed);keff=min(K,len(ids));selected=ids[:keff]
    total=math.fsum(values.values());captured=math.fsum(values[c] for c in selected);oracle=math.fsum(sorted(values.values(),reverse=True)[:keff]);flags=[]
    if not ids:flags.append('empty_cohort')
    if total==0:flags.append('zero_total_severity')
    if keff==0:flags.append('zero_effective_capacity')
    if K>len(ids):flags.append('capacity_saturated')
    return {'N':len(ids),'K_eff':keff,'captured_sum':captured,'total_sum':total,'capture':captured/total if total else None,'hindsight_sum':oracle,'regret_per_review':(oracle-captured)/keff if keff else None,'flags':'|'.join(flags)},ids

