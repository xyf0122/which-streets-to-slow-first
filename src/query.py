"""Finite-support value of revealing one modeled future outcome."""
import hashlib, json, math

def sha(b):return hashlib.sha256(b).hexdigest()


def severity_variance(f,residuals,reference):
    """Use Var(a+E)=Var(E) in the linear regime; no tolerance-based tie binning."""
    values=[max(0.0,f+r['residual']-reference) for r in residuals]
    mean=math.fsum(r['weight']*v for r,v in zip(residuals,values))
    direct=math.fsum(r['weight']*(v-mean)**2 for r,v in zip(residuals,values))
    if all(f+r['residual']>=reference for r in residuals):
        center=math.fsum(r['weight']*r['residual'] for r in residuals)
        canonical=math.fsum(r['weight']*(r['residual']-center)**2 for r in residuals)
        return canonical,direct,'translation_invariant_residual_variance'
    return direct,direct,'weighted_clipped_severity_variance'


def order(scores,seed):
    if any(not math.isfinite(x) for x in scores.values()):raise ValueError('nonfinite selection score')
    return sorted(scores,key=lambda cid:(-scores[cid],sha((seed+'|'+cid).encode()),cid))


def one_query(laws,K,seed,tolerance=1e-10):
    if not isinstance(K,int) or K<1 or K>=len(laws):raise ValueError('require 1 <= K < candidate count')
    means={cid:math.fsum(a['weight']*a['S'] for a in atoms) for cid,atoms in laws.items()}
    for atoms in laws.values():
        if not math.isclose(math.fsum(a['weight'] for a in atoms),1,abs_tol=1e-12,rel_tol=0):raise ValueError('weights do not sum to one')
        if any(a['weight']<=0 or a['S']<0 or not math.isfinite(a['S']) for a in atoms):raise ValueError('invalid atom')
    ranking=order(means,seed);initial=ranking[:K];initial_set=set(initial);V0=math.fsum(means[c] for c in initial);total=math.fsum(means.values());rows=[];posterior=[];max_error=0.0
    for q in sorted(laws):
        others=[c for c in ranking if c!=q];B=math.fsum(means[c] for c in others[:K]);threshold=means[others[K-1]];values=[];probs=[];exchanges=[];selected_probs=[];explicit=[]
        for a in laws[q]:
            revealed=a['S'];scores={**means,q:revealed};selected=order(scores,seed)[:K];selected_set=set(selected)
            actual=math.fsum(scores[c] for c in selected);closed=B+max(0.0,revealed-threshold);error=abs(actual-closed);max_error=max(error,max_error)
            if error>tolerance:raise ArithmeticError('closed form differs from explicit reranking')
            removed=sorted(initial_set-selected_set);added=sorted(selected_set-initial_set)
            if len(removed)!=len(added) or len(removed)>1:raise ArithmeticError('more than one slot exchanged')
            values.append(a['weight']*closed);explicit.append(a['weight']*actual);probs.append(a['weight']*bool(removed));exchanges.append(a['weight']*len(removed));selected_probs.append(a['weight']*(q in selected_set))
            posterior.append({'K':K,'queried_candidate_id':q,'atom_id':a['atom_id'],'atom_weight':a['weight'],'revealed_model_severity':revealed,'selection_rule':'same_top_K_exact_score_then_saved_candidate_tie_hash','selected_ids_json':json.dumps(selected,separators=(',',':')),'selected_scores_json':json.dumps([scores[c] for c in selected],separators=(',',':')),'removed_ids_json':json.dumps(removed,separators=(',',':')),'added_ids_json':json.dumps(added,separators=(',',':')),'exchanged_slots':len(removed),'queried_selected':q in selected_set,'V_after_closed':closed,'V_after_explicit':actual,'closed_explicit_difference':closed-actual})
        V=math.fsum(values);delta=V-V0
        if delta < -tolerance:raise ArithmeticError('substantive negative ideal-information value')
        lo=min(a['S'] for a in laws[q]);hi=max(a['S'] for a in laws[q]);inside=q in initial_set
        zero='outside_all_atoms_at_or_below_threshold' if not inside and hi<=threshold else 'inside_all_atoms_at_or_above_replacement_threshold' if inside and lo>=threshold else ''
        rows.append({'K':K,'candidate_id':q,'m_i':means[q],'severity_variance':math.fsum(a['weight']*(a['S']-means[q])**2 for a in laws[q]),'expected_severity_rank':ranking.index(q)+1,'baseline_selected':inside,'B_q':B,'c_q':threshold,'m_minus_threshold':means[q]-threshold,'min_atom_severity':lo,'max_atom_severity':hi,'support_straddles_threshold':lo<threshold<hi,'structural_zero_case':zero,'V0':V0,'T_model':total,'V_query':V,'V_query_explicit':math.fsum(explicit),'Delta_raw':delta,'within_zero_arithmetic_tolerance':abs(delta)<=tolerance,'negative_within_arithmetic_tolerance':delta<0 and delta>=-tolerance,'probability_selection_change':math.fsum(probs),'expected_exchanged_slots':math.fsum(exchanges),'probability_queried_selected':math.fsum(selected_probs)})
    return rows,posterior,{'K':K,'M':0,'V0':V0,'T_model':total,'model_capture_fraction':V0/total if total>0 else None,'selected_ids_json':json.dumps(initial,separators=(',',':')),'selection_boundary_m':means[initial[-1]],'first_outside_m':means[ranking[K]],'max_closed_explicit_absolute_error':max_error}


def compare_policies(rows,candidates,K,seed):
    byid={r['candidate_id']:r for r in rows};C={r['candidate_id']:r for r in candidates};N=len(rows);V0=rows[0]['V0'];total=rows[0]['T_model'];random=math.fsum(r['V_query'] for r in rows)/N
    choice={
        'decision_targeted':order({r['candidate_id']:r['Delta_raw'] for r in rows},seed)[0],
        'uncertainty_only':order({c:r['severity_variance'] for c,r in C.items()},seed)[0],
        'oldest_evidence':order({c:r['A'] for c,r in C.items()},seed)[0]}
    outputs=[]
    for policy in ['no_query','decision_targeted','uniform_random','uncertainty_only','oldest_evidence']:
        q=choice.get(policy,'');row=byid[q] if q else None
        V=V0 if policy=='no_query' else random if policy=='uniform_random' else row['V_query']
        p=0.0 if policy=='no_query' else math.fsum(r['probability_selection_change'] for r in rows)/N if policy=='uniform_random' else row['probability_selection_change']
        ex=0.0 if policy=='no_query' else math.fsum(r['expected_exchanged_slots'] for r in rows)/N if policy=='uniform_random' else row['expected_exchanged_slots']
        outputs.append({'K':K,'query_policy':policy,'M':0 if policy=='no_query' else 1,'chosen_candidate_id':q,'candidate_universe_size':N,'query_choice_support_size':0 if policy=='no_query' else N if policy=='uniform_random' else 1,'V0':V0,'T_model':total,'expected_captured_value':V,'gain_over_no_query_raw':V-V0,'gain_over_uniform_random_raw':V-random,'model_capture_fraction':V/total if total>0 else None,'gain_over_no_query_model_pp':100*(V-V0)/total if total>0 else None,'gain_over_random_model_pp':100*(V-random)/total if total>0 else None,'probability_selection_change':p,'expected_exchanged_slots':ex,'posterior_rule':'same_top_K_exact_score_then_hash','chosen_query_expected_severity_rank':row['expected_severity_rank'] if row else None,'chosen_query_A':C[q]['A'] if row else None,'chosen_query_variance':C[q]['severity_variance'] if row else None})
    return outputs


def compute(candidates,laws,cfg):
    queries=[];post=[];base=[];policies=[];C={r['candidate_id']:r for r in candidates}
    for K in cfg['K_all']:
        qr,pr,br=one_query(laws,K,cfg['tie_seed'],cfg['numerical_tolerances']['closed_form_abs'])
        for r in qr:
            c=C[r['candidate_id']]
            r.update(A=c['A'],residual_set_id=c.get('residual_set_id','synthetic'),severity_variance_direct=r['severity_variance'],severity_variance=c['severity_variance'],variance_arithmetic=c.get('variance_arithmetic','weighted_severity_variance'))
        queries+=qr;post+=pr;base.append(br);policies+=compare_policies(qr,candidates,K,cfg['tie_seed'])
    return {'query_values':queries,'posterior_decisions':post,'no_query_baseline':base,'policy_comparison':policies}

