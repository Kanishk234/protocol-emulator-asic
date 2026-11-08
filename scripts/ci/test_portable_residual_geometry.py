import pytest
from portable_residual_geometry import saved_overflow, find_net


class Layer:
    def __init__(self, name='Metal3', direction='HORIZONTAL'):
        self.name,self.direction=name,direction
    def getName(self):return self.name
    def getDirection(self):return self.direction


class Grid:
    def __init__(self, usage=None, capacity=3):self.usage=usage or {};self.capacity=capacity
    def getGridX(self):return [0,7200,14400]
    def getGridY(self):return [0,7200]
    def getCapacity(self, layer,x,y):return self.capacity
    def getUsage(self, layer,x,y):return self.usage.get((x,y),0)


def test_read_saved_horizontal_overflow_without_capacity_change():
    grid=Grid({(1,0):4});rows=saved_overflow(grid,[Layer()])
    assert rows==[dict(layer='Metal3',x_index=1,y_index=0,lower_gcell_origin_dbu=[7200,0],
                      upper_gcell_origin_dbu=[14400,0],capacity=3,usage=4,overflow=1)]
    assert grid.capacity==3 and grid.usage=={(1,0):4}


def test_vertical_edges_use_y_neighbor_and_terminal_boundary():
    rows=saved_overflow(Grid({(1,0):5}),[Layer('Metal2','VERTICAL')])
    assert rows[0]['upper_gcell_origin_dbu']==[7200,7200]
    assert rows[0]['overflow']==2
    with pytest.raises(ValueError,match='boundary'):
        saved_overflow(Grid({(1,1):5}),[Layer('Metal2','VERTICAL')])


@pytest.mark.parametrize('usage,capacity,direction', [({(2,0):4},3,'HORIZONTAL'),({(0,0):0},-1,'HORIZONTAL'),({(0,0):-1},3,'HORIZONTAL'),({},3,'DIAGONAL')])
def test_invalid_geometry_refuses(usage,capacity,direction):
    with pytest.raises(ValueError):saved_overflow(Grid(usage,capacity),[Layer(direction=direction)])


class Net:
    def __init__(self,name):self.name=name
    def getName(self):return self.name


class Block:
    def __init__(self,nets):self.nets=nets
    def findNet(self,name):return self.nets.get(name)


def test_escaped_unique_net_resolution():
    net=Net(r'word\[51\].dec')
    assert find_net(Block({net.name:net}),'word[51].dec') is net


def test_missing_or_ambiguous_net_refuses():
    with pytest.raises(ValueError):find_net(Block({}),'word[51].dec')
    with pytest.raises(ValueError):find_net(Block({'word[51].dec':Net('first'),r'word\[51\].dec':Net('second')}),'word[51].dec')
