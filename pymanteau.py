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
    
class DrawShape(object):
    Defaults = {}

    def __init__(self, stack=None, config={}, **args):
        if stack == None:
            stack = TransformStack()
        self.stack = stack
        self.config = self.Defaults.copy()
        self.config.update(config)
        self.config.update(args)
    
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

class TabShape(DrawShape):
    Defaults = {
        'tab_width': 10,
        'tab_height': 2,
    }

    Operations = (
        ("line", ((0, 0), (0, "tab_height"))),
        ("line", ((0, "tab_height"), ("tab_width", "tab_height"))),
        ("line", (("tab_width", "tab_height"), ("tab_width", 0))),
    )

class LeftTabCornerShape(TabShape):
    Operations = (
        ("line", ((0, 0), (0, "tab_height"))),
        ("line", ((0, "tab_height"), ("tab_width - tab_height", "tab_height"))),
    )

class LeftTabCornerShape(TabShape):
    Operations = (
        ("line", ((0, 0), (0, "tab_height"))),
        ("line", ((0, "tab_height"), ("tab_width - tab_height", "tab_height"))),
    )

class QuadShape(DrawShape):
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

class TabStrip(DrawShape):
    Defaults = {
        'strip_tab_count': 4,
        'strip_vertical': True,
        'strip_positive': True,
    }

    def draw(self, canvas, **args):
        tc = self.config["strip_tab_count"]
        ttc = tc + (tc - 1)
        if self.config["strip_vertical"]:
            tw = (self.config["face_height"] / float(ttc))
        else:
            tw = (self.config["face_width"] / float(ttc))
        ts = TabShape(self.stack, self.config, tab_width=tw)
        tcs = LeftTabCornerShape(self.stack, self.config, tab_width=tw)
        self.stack.append(Translation((0, 0)))
        if self.config["strip_positive"]:
            tc_start = 0
        else:
            tc_start = 1
        steps = range(tc_start, ttc, 2)
        for tc in steps:
            print tc, ttc
            if self.config["strip_vertical"]:
                self.stack[-1] = Translation((0, "%s * tab_width" % tc))
            else:
                self.stack[-1] = Translation(("%s * tab_width" % tc, 0))
            ts.draw(canvas, **args)
            """
            if tc in (steps[0], steps[-1]):
                tcs.draw(canvas, **args)
            else:
                ts.draw(canvas, **args)
            """
        self.stack.pop()

class BoxFace(QuadShape):
    def draw(self, canvas, **args):
        # transform us to our center
        super(BoxFace, self).draw(canvas, **args)
        self.stack.append(Translation(("face_width / 2.0", "face_height / 2.0")))
        # bottom
        self.stack.append(Translation(("-tab_width / 2.0", "-face_height / 2.0")))
        tm = TabShape(self.stack, self.config)
        #tm.draw(canvas, **args)
        # left
        self.stack[0] = Rotation(90)
        self.stack[-1] = Translation(("face_width / 2.0", "-tab_width / 2.0"))
        #tm.draw(canvas, **args)
        # right
        self.stack[0] = Rotation(90)
        #self.stack[-1] = Translation(("-face_width / 2.0", "tab_width / 2.0"))
        #tm.draw(canvas, **args)
        self.stack[-1] = Translation(("face_width / 2.0", "-face_height / 2.0"))
        ts = TabStrip(self.stack, self.config)
        ts.draw(canvas, **args)
        # top
        self.stack[0] = Rotation(0)
        #self.stack[-1] = Translation(("tab_width / 2.0", "face_height / 2.0"))
        self.stack[-1] = Translation(("-face_width / 2.0", "-face_height / 2.0"))
        #ts = TabStrip(self.stack, self.config, strip_vertical=False)
        #ts.draw(canvas, **args)
        #tm.draw(canvas, **args)

    
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
