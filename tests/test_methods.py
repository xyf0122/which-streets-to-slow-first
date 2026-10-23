"""Checks for units, eligibility, exact ties, interval bounds and query interpretation."""
import collections,itertools,json,math,sys,unittest
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from io_utils import read_csv,quantile,median
import robustness as a,query,static

class Methods(unittest.TestCase):
    def test_empirical_quantile(self):
        self.assertEqual(quantile(range(1,21)),17)
        self.assertEqual(median([1,2,3,4]),2.5)
        self.assertEqual(quantile([-2,-2,0,0,1]),1)

    def test_kentucky_reference_and_eligibility(self):
        ws=read_csv(ROOT/'data/kentucky/windows.csv.gz')
        refs={r['reference_id']:r for r in read_csv(ROOT/'data/kentucky/references.csv.gz')}
        cfg=json.loads((ROOT/'config.json').read_text())['kentucky']
        self.assertEqual({r['radar_id'] for r in ws},set(cfg['primary_radars']+cfg['illustrative_radars']))
        for r in ws:
            ref=refs[r['reference_id']]
            ref_ok=float(ref['span_seconds'])>=120*int(r['duration_minutes']) and int(ref['passages'])>=60
            eligible=r['full_window']=='True' and ref_ok and int(r['passages'])>=30
            self.assertEqual(r['status']=='eligible',eligible)
            if eligible:
                deviation=float(r['window_p85_passage_medians_kmh'])-float(r['reference_p85_passage_medians_kmh'])
                self.assertEqual(float(r['signed_deviation_kmh']),deviation)
                self.assertEqual(float(r['absolute_deviation_kmh']),abs(deviation))
                self.assertEqual(float(r['fraction_window_passages_shared']),1)

    def test_austin_strict_threshold_and_floor(self):
        entries=[a.Entry('a',1,F(10),F(2)),a.Entry('b',2,F(9),F(1)),a.Entry('c',3,F(5),F(0))]
        self.assertEqual(a.bounds(entries[2],F(5)),(F(5),F(10)))
        self.assertEqual(a.one_entry(entries,1,entries[0])['status'],'strict_infimum')
        self.assertEqual(a.order(entries,{'a':F(9),'b':F(9),'c':F(5)})[0].key,'a')

    def test_austin_loss_by_corner_enumeration(self):
        entries=[a.Entry('a',1,F(10),F(2)),a.Entry('b',2,F(9),F(1)),a.Entry('c',3,F(8),F(0))]
        for k in [1,2]:
            initial={r.key for r in a.order(entries)[:k]}
            for radius in [F(0),F(1,2),F(2)]:
                losses=[]
                for corner in itertools.product(*(a.bounds(e,radius) for e in entries)):
                    scores={e.key:s for e,s in zip(entries,corner)}
                    optimal=a.order(entries,scores)[:k]
                    losses.append(sum(scores[e.key] for e in optimal)-sum(scores[c] for c in initial))
                self.assertEqual(a.regret(entries,k,radius)['loss'],max(losses))

    def test_saved_portland_predictions(self):
        models=json.loads((ROOT/'data/portland/model.json').read_text())
        diagnostic={(r['scenario'],r['candidate_id']):r for r in read_csv(ROOT/'data/portland/uncertainty.csv.gz')}
        for r in read_csv(ROOT/'data/portland/features.csv.gz'):
            m=models[r['scenario']]
            predicted=m['intercept']+sum(beta*(float(r[name])-mean)/sd for name,beta,mean,sd in zip(m['feature_order'],m['coefficients'],m['means'],m['sd']))
            self.assertAlmostEqual(predicted,float(diagnostic[r['scenario'],r['candidate_id']]['f_i']),places=11)

    def test_query_atom_sources_and_exact_ties(self):
        model=json.loads((ROOT/'data/portland/model.json').read_text())['primary']
        laws=collections.defaultdict(list)
        for r in read_csv(ROOT/'data/portland/query_atoms.csv.gz'):
            source=next(x for x in model['residual_sets'][r['residual_set_id']] if x['candidate_id']==r['calibration_candidate_id'])
            self.assertEqual(float(r['residual']),source['residual'])
            self.assertEqual(float(r['weight']),source['weight'])
            self.assertEqual(float(r['hypothetical_Y']),float(r['f_i'])+source['residual'])
            self.assertEqual(float(r['hypothetical_S']),max(0,float(r['hypothetical_Y'])-20))
            laws[r['candidate_id']].append(float(r['weight']))
        self.assertEqual(len(laws),138)
        for weights in laws.values():self.assertAlmostEqual(math.fsum(weights),1,places=12)
        tied=query.order({'a':2,'b':2},'s')
        self.assertEqual(tied,sorted(tied,key=lambda c:query.sha(('s|'+c).encode())))
        self.assertEqual(query.order({'a':1,'b':1+1e-14},'s')[0],'b')

    def test_query_zero_and_positive_value(self):
        for atom_value,expected in [(20,4),(8,0)]:
            laws={'a':[{'atom_id':'a0','S':0.,'weight':.5},{'atom_id':'a1','S':float(atom_value),'weight':.5}],
                  'b':[{'atom_id':'b','S':12.,'weight':1.}]}
            rows,_,_=query.one_query(laws,1,'s')
            self.assertEqual(next(r['Delta_raw'] for r in rows if r['candidate_id']=='a'),expected)

    def test_query_equal_utility_can_change_membership(self):
        first,second=query.order({'a':1,'b':1},'s')
        laws={first:[{'atom_id':'x0','S':0.,'weight':.5},{'atom_id':'x1','S':1.,'weight':.5}],
              second:[{'atom_id':'y','S':1.,'weight':1.}]}
        rows,_,_=query.one_query(laws,1,'s')
        r=next(x for x in rows if x['candidate_id']==first)
        self.assertEqual(r['Delta_raw'],0)
        self.assertEqual(r['probability_selection_change'],.5)

if __name__=='__main__':unittest.main()
