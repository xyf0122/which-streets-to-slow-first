"""CSV serialization and empirical summary helpers."""
import csv,gzip,io,json,math
from pathlib import Path

def read_csv(path):
 p=Path(path)
 with (gzip.open(p,'rt',newline='',encoding='utf-8-sig') if p.suffix=='.gz' else p.open(newline='',encoding='utf-8-sig')) as f:return list(csv.DictReader(f))


def write_csv(path,rows,fields=None):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);rows=list(rows);fields=fields or list(rows[0])
 s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows);b=s.getvalue().encode()
 p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b)


def write_json(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n')


def quantile(values,p=.85):
 a=sorted(values)
 if not a:raise ValueError('Empty distribution')
 return a[max(0,math.ceil(p*len(a))-1)]


def median(a):
 a=sorted(a);n=len(a)
 if not n:raise ValueError('Empty distribution')
 return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

