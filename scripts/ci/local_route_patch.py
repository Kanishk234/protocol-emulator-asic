"""Bounded grid edits with capacity accounting; not physical signoff."""
from collections import Counter, deque
from heapq import heappop, heappush

PITCH = 7200


def edge(a, b):
    a,b=tuple(a),tuple(b)
    for p in (a,b):
        if (len(p)!=3 or any(type(v) is not int for v in p) or
                p[2] not in (1,2,3,4) or any(v%PITCH!=PITCH//2 for v in p[:2])):
            raise ValueError('Invalid grid point')
    if not ((a[:2]==b[:2] and abs(a[2]-b[2])==1) or
            (a[2]==b[2] and sorted((abs(a[0]-b[0]),abs(a[1]-b[1])))==[0,PITCH])):
        raise ValueError('Expected one atomic grid edge')
    return tuple(sorted((tuple(a), tuple(b))))


def component(edges, start, maximum_layer):
    graph = {}
    for a,b in edges:
        if max(a[2],b[2]) <= maximum_layer:
            graph.setdefault(a,set()).add(b)
            graph.setdefault(b,set()).add(a)
    if start not in graph:
        raise ValueError('Receiver is not covered on its native Metal1 grid point')
    found={start}; todo=deque([start])
    while todo:
        for node in graph[todo.popleft()]-found:
            found.add(node);todo.append(node)
    return found


def path(start, goals, free, occupied, maximum_layer=4, radius=4, banned=()):
    """Shortest bounded preferred-direction path; never use occupied planar capacity."""
    start=tuple(start);goals=set(goals);banned=set(banned)
    goals={p for p in goals if max(abs(p[0]-start[0]),abs(p[1]-start[1]))<=radius*PITCH}
    if not goals:raise ValueError('No local receiver-component attachment')
    valid_xy={p[:2] for e in free for p in e}
    todo=[(0,start)];cost={start:0};previous={};end=None
    while todo:
        value,a=heappop(todo)
        if value!=cost[a]:continue
        if a in goals:end=a;break
        if value>160:continue
        x,y,z=a
        neighbors=[(x,y,k) for k in (z-1,z+1) if 1<=k<=maximum_layer]
        if z>=2:
            axis=0 if z==3 else 1
            for delta in (-PITCH,PITCH):
                p=list(a);p[axis]+=delta;neighbors.append(tuple(p))
        for b in neighbors:
            if b[:2] not in valid_xy:continue
            if max(abs(b[0]-start[0]),abs(b[1]-start[1]))>radius*PITCH:continue
            if b in occupied and b not in goals:continue
            e=edge(a,b)
            if e in banned:continue
            planar=z==b[2]
            if planar and free.get(e,0)<1:continue
            new=value+(10 if planar else 1)
            if new>160:continue
            if new<cost.get(b,10**9):
                cost[b]=new;previous[b]=a;heappush(todo,(new,b))
    if end is None:raise ValueError('No bounded path with spare planar capacity')
    result=[]
    while end!=start:
        a=previous[end];result.append(edge(a,end));end=a
    return list(reversed(result))


def consume(free, edges, change=-1):
    for a,b in edges:
        if a[2]==b[2]:
            e=edge(a,b)
            if e not in free:raise ValueError('Planar edge outside capacity grid')
            free[e]+=change
            if change<0 and free[e]<0:raise ValueError('Plan exceeds available capacity')


def patch(routes, free, detours, attachments):
    """Return only reviewed changed nets plus an explicit added/removed ledger."""
    free=dict(free);changed={};ledger=[]
    for item in detours:
        name=item['net'];old=list(changed.get(name,[edge(a,b) for a,b in routes[name]]))
        e=edge(*item['edge'])
        if old.count(e)!=1:raise ValueError('Detour must replace one actual atomic edge')
        old.remove(e);consume(free,[e],1)
        occupied={p for segment in old for p in segment}
        try:additions=path(e[0],{e[1]},free,occupied,banned=[e])
        except ValueError as exc:raise ValueError('Detour '+name+': '+str(exc)) from exc
        consume(free,additions)
        changed[name]=sorted(old+additions)
        ledger.append(dict(net=name,kind='detour',removed=[e],added=additions))
    for item in attachments:
        name=item['net'];old=changed.get(name,[edge(a,b) for a,b in routes[name]])
        if len(set(old))!=len(old):raise ValueError('Ambiguous repeated source edges')
        goals=component(old,tuple(item['receiver']),item['maximum_layer'])
        try:
            additions=path(tuple(item['diode']),goals,free,{p for s in old for p in s},
                           maximum_layer=item['maximum_layer'])
        except ValueError as exc:raise ValueError('Attachment '+name+': '+str(exc)) from exc
        if any(e in old for e in additions):raise ValueError('Repeated attachment edge')
        consume(free,additions);changed[name]=sorted(old+additions)
        ledger.append(dict(net=name,kind='attachment',removed=[],added=additions))
    if any(value<0 for value in free.values()):raise ValueError('Unresolved global overflow')
    return changed,ledger,free


def audit(before, after, ledger):
    expected={n:Counter(edge(a,b) for a,b in rows) for n,rows in before.items()}
    if set(before)!=set(after):raise ValueError('Route inventory changed')
    for item in ledger:
        if item['net'] not in expected:raise ValueError('Unknown edit ledger net')
        counts=expected[item['net']]
        for e in item['removed']:
            e=edge(*e)
            if counts[e]!=1:raise ValueError('Wrong removed route edge')
            del counts[e]
        for e in item['added']:
            e=edge(*e)
            if counts[e]:raise ValueError('Duplicate planned route edge')
            counts[e]+=1
    for name,rows in after.items():
        if Counter(edge(a,b) for a,b in rows)!=expected[name]:
            raise ValueError('Route differs from explicit edit ledger: '+name)


def pins(text):
    result={};remaining=0;name=None
    for raw in text.splitlines():
        fields=raw.split()
        if not fields:continue
        if not remaining:
            if len(fields)!=2 or fields[0] in result:raise ValueError('Bad pin header')
            name=fields[0];remaining=int(fields[1]);result[name]={}
            if remaining<=0:raise ValueError('Empty pin inventory')
        else:
            if len(fields)!=3 or fields[0] in result[name]:raise ValueError('Bad pin row')
            result[name][fields[0]]=tuple(map(int,fields[1:]));remaining-=1
    if remaining:raise ValueError('Incomplete pin inventory')
    return result
