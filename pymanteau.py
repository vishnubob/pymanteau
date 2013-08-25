from dxfwrite import DXFEngine as dxf
import math

class Transform(object):
    def transform(self, point):
        pass

class Translation(Transform):
    def __init__(self, offset=(0, 0)):
        self.offset = offset

    def transform(self, point):
        return map(sum, zip(self.offset, point))

class Rotation(Transform):
    def __init__(self, degrees=0, radians=None):
        if radians != None:
            self.radians = None
        else:
            self.radians = math.radians(degrees)

    def transform(self, point):
        x = point[0] * math.cos(self.radians) - point[1] * math.sin(self.radians)
        y = point[0] * math.sin(self.radians) + point[1] * math.cos(self.radians)
        return (x, y)

class TransformStack(list):
    def transform(self, point):
        _point = point[:]
        for step in self:
            _point = step.transform(_point)
        return _point
    
class CutMacro(object):
    Defaults = {}

    def __init__(self, canvas, stack=None, layer="LINES", color=0, **kw):
        self.canvas = canvas
        self.layer = layer
        if stack == None:
            stack = TransformStack()
        self.stack = stack
        self.color = color
        self.params = self.Defaults.copy()
        self.params.update(kw)
    
    def transform(self, coords):
        _coords = []
        for point in coords:
            point = [self.params.get(pos, pos) for pos in point]
            point = self.stack.transform(point)
            _coords.append(point)
        return _coords

    def draw(self):
        for (opname, coords) in self.Operations:
            op = getattr(dxf, opname)
            coords = self.transform(coords)
            print coords
            self.canvas.add(op(*coords, layer=self.layer, color=self.color))

class TabMacro(CutMacro):
    Defaults = {
        'width': 10,
        'height': 2,
    }

    Operations = (
        ("line", ((0, 0), (0, "height"))),
        ("line", ((0, "height"), ("width", "height"))),
        ("line", (("width", "height"), ("width", 0))),
    )

class QuadMacro(CutMacro):
    Defaults = {
        'width': 40,
        'height': 40,
    }

    Operations = (
        ("line", ((0, 0), (0, "height"))),
        ("line", ((0, "height"), ("width", "height"))),
        ("line", (("width", "height"), ("width", 0))),
        ("line", (("width", 0), (0, 0))),
    )
    
class BoxFactory(object):
    def __init__(self, fn="box.dxf"):
        drawing = dxf.drawing(fn)
        drawing.add_layer('LINES')
        stack = TransformStack([Translation((10, 10))])
        t = Translation((10, 10))
        stack.append(t)
        quad = QuadMacro(drawing, stack=stack)
        quad.draw()
        tm = TabMacro(drawing, stack=stack)
        tm.draw()
        t = Translation((20, 0))
        stack.append(t)
        tm.draw()
        t = Rotation(90)
        stack.append(t)
        tm.draw()
        drawing.save()
        
bf = BoxFactory()
