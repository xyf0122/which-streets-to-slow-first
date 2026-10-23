"""Exact finite-frame score-box analysis. Standard library; no empirical error model."""
from dataclasses import dataclass
from fractions import Fraction as F

@dataclass(frozen=True)
class Entry:
    key: str
    rank: int
    total: F
    speed: F


def q(x):
    """Lossless text: terminating decimals when possible, otherwise a/b."""
    x = F(x)
    d = x.denominator
    a = b = 0
    while d % 2 == 0:
        a += 1; d //= 2
    while d % 5 == 0:
        b += 1; d //= 5
    if d != 1:
        return str(x)
    n = max(a, b)
    if not n:
        return str(x.numerator)
    num = x.numerator * 10**n // x.denominator
    sign = '-' if num < 0 else ''
    s = str(abs(num)).zfill(n+1)
    return sign + (s[:-n] + '.' + s[-n:]).rstrip('0').rstrip('.')


def ahead(score, rank, other_score, other_rank):
    return score > other_score or (score == other_score and rank < other_rank)


def order(entries, scores=None):
    return sorted(entries, key=lambda e: (-(scores[e.key] if scores is not None else e.total), e.rank))


def bounds(e, r):
    if r < 0:
        raise ValueError('negative radius')
    return e.total - min(r, e.speed), e.total + r


def membership(entries, k, r):
    box = {e.key: bounds(e,r) for e in entries}
    out = {}
    for e in entries:
        lo, hi = box[e.key]
        worst = 1 + sum(ahead(box[j.key][1],j.rank,lo,e.rank) for j in entries if j.key != e.key)
        best = 1 + sum(ahead(box[j.key][0],j.rank,hi,e.rank) for j in entries if j.key != e.key)
        cls = 'guaranteed_included' if worst <= k else ('guaranteed_excluded' if best > k else 'decision_sensitive')
        out[e.key] = dict(lower=lo,upper=hi,best_rank=best,worst_rank=worst,classification=cls)
    return out


def one_entry(entries, k, e):
    ranked = order(entries)
    inside = e in ranked[:k]
    rival = ranked[k] if inside else ranked[k-1]
    gap = e.total-rival.total if inside else rival.total-e.total
    equality_flips = e.rank > rival.rank if inside else e.rank < rival.rank
    feasible = not inside or gap < e.speed or (gap == e.speed and equality_flips)
    status = ('attained' if equality_flips else 'strict_infimum') if feasible else 'unattainable_speed_floor'
    magnitude = gap if feasible else None
    # One rational witness beyond a strict threshold; not an extra scenario radius.
    witness = None
    if feasible:
        eps = F(0) if equality_flips else (min(F(1,1000),(e.speed-gap)/2) if inside else F(1,1000))
        witness = (-1 if inside else 1)*(gap+eps)
    return dict(nominal_included=inside,competitor_id=rival.key,competitor_total=rival.total,
                algebraic_gap=gap,threshold_magnitude=magnitude,status=status,
                equality_flips=equality_flips,threshold_delta=(-gap if inside else gap),
                witness_delta=witness)


def crossing(gap, speed):
    """Unique nonnegative solution r+min(r,speed)=gap."""
    assert gap >= 0 and speed >= 0
    return gap/2 if gap <= 2*speed else gap-speed


def critical(entries,k,e):
    """One transition per candidate: loss of guarantee or first possibility."""
    ranked=order(entries)
    inside=e in ranked[:k]
    if inside:
        rival=order([j for j in entries if j.key != e.key])[k-1]
        c=crossing(e.total-rival.total,e.speed)
        at=e.rank > rival.rank # failure of guarantee at equality
        return dict(kind='loses_guaranteed_inclusion',radius=c,transition_at_equality=at,
                    boundary_ids=[rival.key],nominal_included=True)
    opponents=[j for j in entries if ahead(j.total,j.rank,e.total,e.rank)]
    # Each initially-ahead opponent stops preceding e at this pairwise crossing.
    events=sorted([(crossing(j.total-e.total,j.speed), e.rank < j.rank, j.key) for j in opponents],
                  key=lambda x:(x[0],not x[1],x[2]))
    need=len(opponents)-k+1
    c=events[need-1][0]
    losses_at=sum(t<c or (t==c and at) for t,at,_ in events)
    return dict(kind='becomes_possibly_included',radius=c,transition_at_equality=losses_at>=need,
                boundary_ids=sorted(j for t,at,j in events if t==c),nominal_included=False)


def class_from_critical(c,r,side='at'):
    changed=r>c['radius'] or (r==c['radius'] and (side=='right' or (side=='at' and c['transition_at_equality'])))
    if c['nominal_included']:
        return 'decision_sensitive' if changed else 'guaranteed_included'
    return 'decision_sensitive' if changed else 'guaranteed_excluded'


def regret(entries,k,r):
    nominal=order(entries)[:k]
    A={e.key for e in nominal}
    box={e.key:bounds(e,r) for e in entries}
    insiders=sorted(nominal,key=lambda e:(box[e.key][0],-e.rank))
    outsiders=sorted([e for e in entries if e.key not in A],key=lambda e:(-box[e.key][1],e.rank))
    curve=[F(0)]
    for a,b in zip(insiders,outsiders):
        curve.append(curve[-1]+box[b.key][1]-box[a.key][0])
    R=max(curve)
    # This single corner simultaneously maximizes loss and the number of selected outsiders.
    scores={e.key:box[e.key][0 if e.key in A else 1] for e in entries}
    alt=order(entries,scores)[:k]
    B={e.key for e in alt}
    realized=sum(scores[x] for x in B)-sum(scores[x] for x in A)
    assert realized == R
    return dict(loss=R,curve=curve,scores=scores,nominal=A,alternative=B,
                alternative_order=[e.key for e in alt],max_exchanges=len(B-A),
                maximizing_t=[t for t,v in enumerate(curve) if v==R])
