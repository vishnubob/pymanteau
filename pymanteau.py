import os
import math
from dxfwrite import DXFEngine as dxf

class Context(object):
    def __init__(self, fn):
        self.canvas = dxf.drawing(fn)
        self.canvas.add_layer('LINES')
        self.config = [{}]
        self.translation_stack = []
        self.rotation_stack = []

    def save(self):
        self.canvas.save()

    def push_config(self, **config):
        _config = self.config[-1].copy()
        _config.update(config)
        self.config.append(_config)

    def pop_config(self):
        self.config.pop()

    def push_rotation(self, degrees=0, radians=None):
        if radians != None:
            radians = None
        else:
            radians = math.radians(degrees)
        self.rotation_stack.append(radians)

    def pop_rotation(self):
        self.rotation.pop()

    def push_translation(self, point):
        self.translation_stack.append(point)

    def pop_translation(self):
        self.translation_stack.pop()

    def convert(self, point):
        return tuple([eval(str(pos), globals(), self.config[-1]) for pos in point])
        
    def translate(self, point):
        for offset in self.translation_stack:
            offset = self.convert(offset)
            point = self.convert(point)
            point = tuple(map(sum, zip(offset, point)))
        return point

    def rotate(self, point):
        for angle in self.rotation_stack:
            point = self.convert(point)
            x = point[0] * math.cos(angle) - point[1] * math.sin(angle)
            y = point[0] * math.sin(angle) + point[1] * math.cos(angle)
            point = (x, y)
        return point
        
    def transform(self, point):
        return self.translate(self.rotate(point))

class DrawShape(object):
    def __init__(self, context):
        self.context = context

    @property
    def config(self):
        return self.context.config
    
    def transform(self, coords):
        _coords = []
        for point in coords:
            point = self.context.transform(point)
            _coords.append(point)
        return _coords

    def draw(self, **args):
        for (opname, coords) in self.Operations:
            op = getattr(dxf, opname)
            coords = self.transform(coords)
            print coords
            self.context.canvas.add(op(*coords, layer="LINES", **args))

class TabShape(DrawShape):
    Operations = (
        ("line", (("tab_width / 2.0", "-tab_height / 2.0"), ("-tab_width / 2.0", "-tab_height / 2.0"))),
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
        ("line", (("tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0", "tab_height / 2.0"))),
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
    Operations = (
        ("line", (("-face_width / 2.0", "-face_height / 2.0"), ("-face_width / 2.0", "face_height / 2.0"))),
        ("line", (("-face_width / 2.0", "face_height / 2.0"), ("face_width / 2.0", "face_height / 2.0"))),
        ("line", (("face_width / 2.0", "face_height / 2.0"), ("face_width / 2.0", "-face_height / 2.0"))),
        ("line", (("face_width / 2.0", "-face_height / 2.0"), ("-face_width / 2.0", "-face_height / 2.0"))),
    )

class TabStrip(DrawShape):
    def draw(self, canvas, **args):
        tc = self.config["strip_tab_count"]
        ttc = tc + (tc - 1)
        if self.config["strip_vertical"]:
            tw = (self.config["face_height"] / float(ttc))
        else:
            tw = (self.config["face_width"] / float(ttc))
        ts = TabShape(self.context, self.config, tab_width=tw)
        tcs = LeftTabCornerShape(self.context, self.config, tab_width=tw)
        self.context.append(Translation((0, 0)))
        if self.config["strip_positive"]:
            tc_start = 0
        else:
            tc_start = 1
        steps = range(tc_start, ttc, 2)
        for tc in steps:
            print tc, ttc
            if self.config["strip_vertical"]:
                self.context[-1] = Translation((0, "%s * tab_width" % tc))
            else:
                self.context[-1] = Translation(("%s * tab_width" % tc, 0))
            ts.draw(canvas, **args)
            """
            if tc in (steps[0], steps[-1]):
                tcs.draw(canvas, **args)
            else:
                ts.draw(canvas, **args)
            """
        self.context.pop()

class BoxFace(QuadShape):
    def draw(self, **args):
        super(BoxFace, self).draw(**args)
        self.context.push_config(tab_width=5, tab_height=2)
        self.context.push_translation((0, "(face_height / 2.0) - (tab_height / 2.0)"))
        tm = TabShape(self.context)
        tm.draw()

class BoxFactory(object):
    Defaults = {
        "face_width": 40,
        "face_height": 40,
    }

    def __init__(self, fn="box.dxf"):
        context = Context(fn)
        context.push_translation((50, 50))
        context.push_config(**self.Defaults)
        bf = BoxFace(context)
        bf.draw()
        context.save()
        
bf = BoxFactory()
os.system("inkscape -z box.dxf -e box.png")
