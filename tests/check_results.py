"""Compare every reproduced result with the reported full-precision reference."""
import argparse, csv, gzip, hashlib, json, math, sys
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from io_utils import read_csv

def equal(actual,expected):
    if actual==expected:return True
    try:
        if Fraction(actual)==Fraction(expected):return True
        return math.isclose(float(actual),float(expected),rel_tol=1e-12,abs_tol=1e-10)
    except (ValueError,ZeroDivisionError):return False

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    expected=json.loads(gzip.decompress((ROOT/'tests/reference_results.json.gz').read_bytes()))
    checked=0
    for name,rows in expected.items():
        observed=read_csv(a.out/name)
        assert len(observed)==len(rows),(name,len(observed),len(rows))
        for i,(actual,reference) in enumerate(zip(observed,rows)):
            for key,value in reference.items():
                assert equal(actual[key],value),(name,i,key,actual[key],value)
                checked+=1
        print(name+': '+str(len(rows))+' rows match')
    manifest=json.loads((ROOT/'checksums.json').read_text())
    for name,digest in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    print(str(checked)+' reference cells checked; all distributed file checksums match.')

if __name__=='__main__':main()
