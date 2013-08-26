import os
import math
from dxfwrite import DXFEngine as dxf

class Context(object):
    def __init__(self, fn):
        self.canvas = dxf.drawing(fn)
        self.canvas.add_layer('LINES')
        self.config = [{}]
        self.transformation_stack = []

    def save(self):
        self.canvas.save()

    # config
    def push_config(self, **config):
        _config = self.config[-1].copy()
        _config.update(config)
        self.config.append(_config)

    def pop_config(self):
        self.config.pop()

    # variable substitution
    def convert(self, point):
        try:
            return tuple([eval(str(pos), globals(), self.config[-1]) for pos in point])
        except:
            raise ValueError, point

    # transformation
    def push_translation(self, point):
        self.transformation_stack.append(("translation", point))

    def push_rotation(self, degrees=0, radians=None):
        if radians != None:
            radians = None
        else:
            radians = math.radians(degrees)
        self.transformation_stack.append(("rotation", radians))

    def push_transformation(self, kind, *args, **kw):
        if kind == "rotation":
            self.push_rotation(*args, **kw)
        elif kind == "translation":
            self.push_translation(*args, **kw)
        else:
            raise ValueError, kind

    def pop_transformation(self, depth=1):
        for x in range(depth):
            self.transformation_stack.pop()

    def _translate(self, point, offset):
        offset = self.convert(offset)
        point = self.convert(point)
        point = tuple(map(sum, zip(offset, point)))
        return point

    def _rotate(self, point, angle):
        point = self.convert(point)
        x = point[0] * math.cos(angle) - point[1] * math.sin(angle)
        y = point[0] * math.sin(angle) + point[1] * math.cos(angle)
        point = (x, y)
        return point
        
    def transform(self, point):
        for (kind, args) in self.transformation_stack[::-1]:
            if kind == "rotation":
                point = self._rotate(point, args)
            elif kind == "translation":
                point = self._translate(point, args)
            else:
                raise ValueError, kind
        return point

class DrawShape(object):
    def __init__(self, context):
        self.context = context

    @property
    def config(self):
        return self.context.config[-1]
    
    def transform(self, coords):
        _coords = []
        for point in coords:
            point = self.context.transform(point)
            _coords.append(point)
        return _coords

    def draw(self, **args):
        color = 4
        for (opname, coords) in self.Operations:
            op = getattr(dxf, opname)
            coords = self.transform(coords)
            print coords
            self.context.canvas.add(op(*coords, layer="LINES", color=1, **args))
            color += 1

class TabShape(DrawShape):
    Operations = (
        ("line", (("-tab_width / 2.0", "tab_height / 2.0"), ("-tab_width / 2.0", "-tab_height / 2.0"))),
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
        ("line", (("tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0", "tab_height / 2.0"))),
    )

class LeftCornerTabShape(TabShape):
    Operations = (
        ("line", (("-tab_width / 2.0 + tab_height", "-tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
        ("line", (("tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0", "tab_height / 2.0"))),
    )

class RightCornerTabShape(TabShape):
    Operations = (
        ("line", (("-tab_width / 2.0", "tab_height / 2.0"), ("-tab_width / 2.0", "-tab_height / 2.0"))),
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0 - tab_height", "-tab_height / 2.0"))),
    )

class QuadShape(DrawShape):
    Operations = (
        ("line", (("-face_width / 2.0", "-face_height / 2.0"), ("-face_width / 2.0", "face_height / 2.0"))),
        ("line", (("-face_width / 2.0", "face_height / 2.0"), ("face_width / 2.0", "face_height / 2.0"))),
        ("line", (("face_width / 2.0", "face_height / 2.0"), ("face_width / 2.0", "-face_height / 2.0"))),
        ("line", (("face_width / 2.0", "-face_height / 2.0"), ("-face_width / 2.0", "-face_height / 2.0"))),
    )

class TabStrip(DrawShape):
    def draw(self, **args):
        tc = self.config["strip_tab_count"]
        ttc = tc + (tc - 1)
        tw = (self.config["strip_width"] / float(ttc))
        self.context.push_config(tab_width=tw, total_tab_count=ttc)
        tc_start = int(not self.config["strip_tab_positive"])
        steps = range(tc_start, ttc, 2)
        self.context.push_translation(("tab_width * (step - (last_step / 2.0))", 0))
        for step in steps:
            self.context.push_config(step=step, last_step=steps[-1])
            if step == steps[0]:
                shape = LeftCornerTabShape(self.context)
                shape.draw(**args)
            elif step == steps[-1]:
                shape = RightCornerTabShape(self.context)
                shape.draw(**args)
            else:
                shape = TabShape(self.context)
                shape.draw(**args)
            self.context.pop_config()
        self.context.pop_transformation()
        self.context.pop_config()

class BoxFace(QuadShape):
    def draw(self, **args):
        super(BoxFace, self).draw(**args)
        ts = TabStrip(self.context)
        # top
        self.context.push_config(strip_tab_count=6, strip_width=self.config["face_width"], strip_tab_positive=True, tab_height=2)
        self.context.push_translation((0, "face_height / 2.0 - tab_height / 2.0"))
        ts.draw()
        self.context.pop_transformation()
        # left
        self.context.push_translation(("-face_width / 2.0 + tab_height / 2.0", 0))
        self.context.push_rotation(90)
        ts.draw()
        self.context.pop_transformation(2)
        # bottom
        self.context.push_translation((0, "-face_width / 2.0 + tab_height / 2.0"))
        self.context.push_rotation(180)
        ts.draw()
        self.context.pop_transformation(2)
        # right
        self.context.push_translation(("(face_width / 2.0 - tab_height / 2.0)", 0))
        self.context.push_rotation(270)
        ts.draw()
        self.context.pop_transformation(2)

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
