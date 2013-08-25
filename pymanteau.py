import os
import math
from dxfwrite import DXFEngine as dxf

class Transform(object):
    def transform(self, point, config):
        pass

    def convert(self, point, config):
        return tuple([eval(str(pos), config) for pos in point])

class Translation(Transform):
    def __init__(self, offset=(0, 0)):
        self.offset = offset

    def transform(self, point, config):
        return map(sum, zip(self.convert(self.offset, config), self.convert(point, config)))

class Rotation(Transform):
    def __init__(self, degrees=0, radians=None):
        if radians != None:
            self.radians = None
        else:
            self.radians = math.radians(degrees)

    def transform(self, point, config):
        point = self.convert(point, config)
        x = point[0] * math.cos(self.radians) - point[1] * math.sin(self.radians)
        y = point[0] * math.sin(self.radians) + point[1] * math.cos(self.radians)
        return (x, y)

class TransformStack(list):
    def transform(self, point, config):
        _point = point[:]
        for step in self:
            _point = step.transform(_point, config)
        return _point
    
class DrawMacro(object):
    Defaults = {}

    def __init__(self, stack=None, config={}):
        if stack == None:
            stack = TransformStack()
        self.stack = stack
        self.config = self.Defaults.copy()
        self.config.update(config)
    
    def transform(self, coords):
        _coords = []
        for point in coords:
            point = self.stack.transform(point, self.config)
            _coords.append(point)
        return _coords

    def draw(self, canvas, **args):
        for (opname, coords) in self.Operations:
            op = getattr(dxf, opname)
            coords = self.transform(coords)
            print coords
            canvas.add(op(*coords, **args))

class TabMacro(DrawMacro):
    Defaults = {
        'tab_width': 10,
        'tab_height': 2,
    }

    Operations = (
        ("line", ((0, 0), (0, "tab_height"))),
        ("line", ((0, "tab_height"), ("tab_width", "tab_height"))),
        ("line", (("tab_width", "tab_height"), ("tab_width", 0))),
    )

class QuadMacro(DrawMacro):
    Defaults = {
        'face_width': 40,
        'face_height': 40,
    }

    Operations = (
        ("line", ((0, 0), (0, "face_height"))),
        ("line", ((0, "face_height"), ("face_width", "face_height"))),
        ("line", (("face_width", "face_height"), ("face_width", 0))),
        ("line", (("face_width", 0), (0, 0))),
    )

class BoxFace(QuadMacro):
    def draw(self, canvas, **args):
        # transform us to our center
        super(BoxFace, self).draw(canvas, **args)
        width = self.config["face_width"]
        height = self.config["face_width"]
        half_width = width / 2.0
        half_height = height / 2.0
        self.stack.append(Translation((half_width, half_height)))
        # bottom
        self.stack.append(Translation(("-tab_width / 2.0", "-face_height / 2.0")))
        tm = TabMacro(self.stack, self.config)
        tm.draw(canvas, **args)
        # top
        self.stack[0] = Rotation(180)
        self.stack[-1] = Translation(("tab_width / 2.0", "face_height / 2.0"))
        tm.draw(canvas, **args)
        # left
        self.stack[0] = Rotation(90)
        self.stack[-1] = Translation(("face_width / 2.0", "-tab_width / 2.0"))
        tm.draw(canvas, **args)
        # right
        self.stack[0] = Rotation(270)
        self.stack[-1] = Translation(("-face_width / 2.0", "tab_width / 2.0"))
        tm.draw(canvas, **args)
    
class BoxFactory(object):
    def __init__(self, fn="box.dxf"):
        drawing = dxf.drawing(fn)
        drawing.add_layer('LINES')
        r = Rotation(0)
        t = Translation((10, 10))
        stack = TransformStack([r, t])
        quad = BoxFace(stack)
        quad.draw(drawing, layer="LINES")
        drawing.save()
        
bf = BoxFactory()
os.system("inkscape -z box.dxf -e box.png")
