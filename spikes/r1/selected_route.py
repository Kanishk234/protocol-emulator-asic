"""Read-only decoding of selected R1 PIPs from actual frame words."""
import collections


def selected_predecessors(spec, words, text):
    if spec['ArchSpecs']['FrameBitsPerRow']!=32 or spec['ArchSpecs']['MaxFramesPerCol']!=20 or len(words)!=962:
        raise ValueError('Require frozen R1 frame geometry')
    graph=collections.defaultdict(list)
    for line in text.splitlines():
        if not line or line.startswith('#'):continue
        tile,source,other,dest,delay,key=line.split(',')
        bits=spec['TileSpecs'][tile].get(key) if tile==other else {}
        if bits is None:raise ValueError('PIP has no encoding')
        x,y=map(int,tile[1:].split('Y'))
        if all(str((words[1+(x*20+bit//32)*6+1+(4-y)]>>(bit%32))&1)==value for bit,value in bits.items()):
            graph[(other,dest)].append((tile,source))
    return graph


def trace_route(graph,target,limit=64):
    path=[target];seen={target}
    while graph.get(path[-1]):
        preds=graph[path[-1]]
        if len(preds)!=1:raise ValueError('Ambiguous selected route')
        node=preds[0]
        if node in seen or len(path)>=limit:raise ValueError('Cyclic or unbounded routing trace')
        seen.add(node);path.append(node)
    return path
