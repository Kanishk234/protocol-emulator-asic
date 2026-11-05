import pytest

from c_select_congestion_readback import overloaded_edges, crossing_nets


class Layer:
    def __init__(self, direction='HORIZONTAL'): self.direction=direction
    def getName(self): return 'Metal3'
    def getDirection(self): return self.direction


class Grid:
    def getGridX(self): return [0,7200,14400]
    def getGridY(self): return [0,7200,14400]
    def getCapacity(self, layer, x, y): return 14
    def getUsage(self, layer, x, y): return 15 if (x,y)==(0,0) else 0


def test_horizontal_capacity_and_crossing_nets():
    edges, totals=overloaded_edges(Grid(),[Layer()])
    assert totals['Metal3']['overflow']==1
    assert edges[0]['start_dbu']==[3600,3600]
    assert edges[0]['end_dbu']==[10800,3600]
    segment=((3600,3600,'Metal3'),(18000,3600,'Metal3'))
    routes={'clock':[segment,segment], 'unrelated':[((3600,10800,'Metal3'),(18000,10800,'Metal3'))]}
    crossing_nets(routes,edges)
    assert edges[0]['crossing_route_names']==['clock']


def test_vertical_edge_mapping():
    edges,_=overloaded_edges(Grid(),[Layer('VERTICAL')])
    assert edges[0]['end_dbu']==[3600,10800]
    crossing_nets({'data':[((3600,3600,'Metal3'),(3600,18000,'Metal3'))]},edges)


def test_unmatched_geometry_rejects():
    edges,_=overloaded_edges(Grid(),[Layer()])
    with pytest.raises(ValueError,match='no matching'):
        crossing_nets({},edges)


@pytest.mark.parametrize('value',[-1,float('nan'),float('inf')])
def test_bad_grid_value_rejects(value):
    grid=Grid()
    grid.getCapacity=lambda *args:value
    with pytest.raises(ValueError,match='capacity/usage'):
        overloaded_edges(grid,[Layer()])


def test_boundary_overflow_rejects():
    grid=Grid()
    grid.getUsage=lambda layer,x,y:15 if (x,y)==(2,0) else 0
    with pytest.raises(ValueError,match='outer grid edge'):
        overloaded_edges(grid,[Layer()])
