"""Aggregate the fixed observation-window summaries with equal deployment weights."""
from io_utils import median,quantile

def describe(vals,prefix):
 if not vals:return {prefix+k:'' for k in ['median','q25','q75','iqr','min','max']}
 lo,hi=quantile(vals,.25),quantile(vals,.75)
 return {prefix+'median':median(vals),prefix+'q25':lo,prefix+'q75':hi,prefix+'iqr':hi-lo,prefix+'min':min(vals),prefix+'max':max(vals)}


def summarize(windows,s):
 summaries=[]
 for rid in s['primary_radars']+s['illustrative_radars']:
  for dur in s['window_minutes']:
   ws=[w for w in windows if w['radar_id']==rid and w['duration_minutes']==dur];valid=[w for w in ws if w['status']=='eligible'];es=[w['signed_deviation_kmh'] for w in valid]
   summaries.append(dict(radar_id=rid,scope='primary' if rid in s['primary_radars'] else 'illustrative',duration_minutes=dur,intervals=len({w['interval_id'] for w in ws}),full_windows=sum(w['full_window'] for w in ws),trailing_partial_windows=sum(not w['full_window'] for w in ws),eligible_windows=len(valid),low_count_windows=sum(w['status']=='fewer_than_30_passages' for w in ws),reference_ineligible_windows=sum(w['status']=='reference_ineligible' for w in ws),status='estimable' if valid else 'not_estimable',eligible_window_passages=sum(w['passages'] for w in valid),**describe(es,'signed_kmh_'),**describe([abs(e) for e in es],'absolute_kmh_')))
 common=[r for r in s['primary_radars'] if all(any(a['radar_id']==r and a['duration_minutes']==d and a['eligible_windows']>0 for a in summaries) for d in s['window_minutes'])]
 agg=[]
 for dur in s['window_minutes']:
  rows=[a for a in summaries if a['radar_id'] in common and a['duration_minutes']==dur]
  agg.append(dict(duration_minutes=dur,cohort='common_primary_all_four_durations',deployment_count=len(common),deployment_ids=';'.join(common),eligible_windows=sum(a['eligible_windows'] for a in rows),aggregation='equal deployment weights; median of deployment medians',median_deployment_absolute_deviation_kmh=median([a['absolute_kmh_median'] for a in rows]) if rows else '',median_deployment_signed_deviation_kmh=median([a['signed_kmh_median'] for a in rows]) if rows else '',**describe([a['absolute_kmh_median'] for a in rows],'deployment_absolute_median_kmh_')))
 return summaries,agg
