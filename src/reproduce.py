"""Reproduce the reported comparisons from fixed analytical inputs."""
import argparse, collections, itertools, json, math, sys
from fractions import Fraction as F
from pathlib import Path
sys.dont_write_bytecode = True
from io_utils import read_csv, write_csv, write_json
import kentucky, query, robustness as austin, static

ROOT = Path(__file__).resolve().parents[1]


def kentucky_results(out, cfg):
    windows = read_csv(ROOT / 'data/kentucky/windows.csv.gz')
    for row in windows:
        for key in ['duration_minutes', 'passages', 'reference_passages']:
            row[key] = int(row[key])
        row['full_window'] = row['full_window'] == 'True'
        if row['status'] == 'eligible':
            for key in ['signed_deviation_kmh', 'absolute_deviation_kmh']:
                row[key] = float(row[key])
    summaries, durations = kentucky.summarize(windows, cfg['kentucky'])
    write_csv(out / 'kentucky/deployment_duration.csv', summaries)
    write_csv(out / 'kentucky/durations.csv', durations)


def austin_results(out, cfg):
    source = read_csv(ROOT / 'data/austin/candidates.csv.gz')
    entries = [austin.Entry(r['candidate_id'], int(r['published_rank']),
                           F(r['total_score']), F(r['measured_speed_score'])) for r in source]
    assert len(entries) == len({e.key for e in entries}) == 703
    summaries, tipping, members, paths = [], [], [], []
    for k in cfg['capacities']:
        nominal = austin.order(entries)[:k]
        initial = {e.key for e in nominal}
        critical = {e.key: austin.critical(entries, k, e) for e in entries}
        for e in entries:
            tipping.append(dict(K=k, candidate_id=e.key, **austin.one_entry(entries, k, e)))
        events = sorted({F(0)} | {c['radius'] for c in critical.values()})
        for index, radius in enumerate(events):
            for side in ['at', 'right']:
                counts = collections.Counter(austin.class_from_critical(c, radius, side)
                                             for c in critical.values())
                paths.append(dict(K=k, radius=radius,
                    position='exact_point' if side == 'at' else 'open_interval_after',
                    next_radius=events[index+1] if index+1 < len(events) else '',
                    guaranteed_included=counts['guaranteed_included'],
                    decision_sensitive=counts['decision_sensitive'],
                    guaranteed_excluded=counts['guaranteed_excluded']))
        for value in cfg['austin_radii']:
            radius = F(value)
            membership = austin.membership(entries, k, radius)
            loss = austin.regret(entries, k, radius)
            counts = collections.Counter(m['classification'] for m in membership.values())
            for e in entries:
                members.append(dict(K=k, radius=radius, candidate_id=e.key, **membership[e.key]))
            summaries.append(dict(K=k, radius=radius, nominal_sum=sum(e.total for e in nominal),
                guaranteed_included=counts['guaranteed_included'],
                decision_sensitive=counts['decision_sensitive'],
                guaranteed_excluded=counts['guaranteed_excluded'],
                possibly_included=counts['guaranteed_included']+counts['decision_sensitive'],
                individually_removable_nominal=k-counts['guaranteed_included'],
                possible_outside_entrants=sum(e.key not in initial and membership[e.key]['best_rank']<=k for e in entries),
                max_simultaneous_exchanged_slots=loss['max_exchanges'],
                worst_case_loss_points=loss['loss']))
    for name, data in [('scenarios.csv', summaries), ('tipping_points.csv.gz', tipping),
                       ('membership.csv.gz', members), ('robustness_path.csv.gz', paths)]:
        data = [{k: austin.q(v) if isinstance(v, F) else '' if v is None else v
                 for k, v in row.items()} for row in data]
        write_csv(out / 'austin' / name, data)


def portland_results(out, cfg):
    score_rows = read_csv(ROOT / 'data/portland/scores.csv.gz')
    observations = read_csv(ROOT / 'data/portland/observed_outcomes.csv.gz')
    scores = {(s, m): {r['candidate_id']: float(r['score']) for r in score_rows
                       if r['scenario'] == s and r['method_id'] == m}
              for s in ['primary', 'availability_30d'] for m in cfg['portland_rules']}
    performance, selections, comparisons = [], [], []
    for scenario in cfg['portland_scenarios']:
        input_scenario = 'availability_30d' if scenario == 'availability_30d' else 'primary'
        values = {r['candidate_id']: float(r['S']) for r in observations if r['scenario'] == scenario}
        metrics, selected = {}, {}
        for method in cfg['portland_rules']:
            sm = scores[input_scenario, method]
            for k in cfg['capacities']:
                met, ids = static.performance(values, {c: sm[c] for c in values}, k, cfg['tie_seed'])
                performance.append(dict(scenario=scenario, method_id=method, K=k, status='complete', **met))
                metrics[method, k] = met
                selected[method, k] = set(ids[:met['K_eff']])
                for i, cid in enumerate(ids):
                    selections.append(dict(scenario=scenario, method_id=method, K=k,
                        candidate_id=cid, selected=i<met['K_eff'], review_position=i+1,
                        score=sm[cid], input_scenario=input_scenario))
        for k in cfg['capacities']:
            for a, b in itertools.combinations(cfg['portland_rules'], 2):
                sa, sb = selected[a,k], selected[b,k]
                ra, rb = metrics[a,k], metrics[b,k]
                comparisons.append(dict(scenario=scenario, K=k, method_a=a, method_b=b,
                    capture_gain_b_minus_a_pp=100*(rb['capture']-ra['capture']),
                    captured_sum_gain_b_minus_a=rb['captured_sum']-ra['captured_sum'],
                    regret_change_b_minus_a=rb['regret_per_review']-ra['regret_per_review'],
                    overlap=len(sa&sb), exchanged_slots=len(sa-sb), symmetric_difference=len(sa^sb),
                    identical_selection=sa==sb))
    for name, data in [('performance.csv.gz',performance), ('selections.csv.gz',selections),
                       ('comparisons.csv.gz',comparisons)]:
        write_csv(out / 'portland' / name, data)


def query_results(out, cfg):
    candidates = read_csv(ROOT / 'data/portland/query_candidates.csv.gz')
    for row in candidates:
        for key in ['m_i','severity_variance','severity_variance_direct','A','f_i']:
            row[key] = float(row[key])
    atoms = read_csv(ROOT / 'data/portland/query_atoms.csv.gz')
    laws = collections.defaultdict(list)
    for row in atoms:
        laws[row['candidate_id']].append(dict(atom_id=row['atom_id'],
            S=float(row['hypothetical_S']), weight=float(row['weight'])))
    results = query.compute(candidates, laws, cfg['query'])
    for name, data in results.items():
        write_csv(out / 'query' / (name+'.csv.gz'), data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'output')
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit('Choose a new output directory to preserve existing results.')
    if out == ROOT or out in ROOT.parents or ROOT/'data' == out or ROOT/'data' in out.parents:
        raise SystemExit('Output must be separate from the source data.')
    cfg = json.loads((ROOT/'config.json').read_text())
    for label, function in [('Kentucky',kentucky_results), ('Austin',austin_results),
                            ('Portland observed',portland_results), ('Portland modeled query',query_results)]:
        print(label, flush=True)
        function(out,cfg)
    print('Completed: '+str(out))


if __name__ == '__main__':
    main()
