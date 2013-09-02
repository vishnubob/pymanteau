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
            self.context.canvas.add(op(*coords, layer="LINES", **args))

class CornerShape(DrawShape):
    PositiveFullStart = (
        ("line", (("-tab_width / 2.0", "tab_height / 2.0"), ("tab_width / 2.0", "tab_height / 2.0"))),
        ("line", (("tab_width / 2.0", "tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
    )

    PositiveFullEnd = (
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("-tab_width / 2.0", "tab_height / 2.0"))),
        ("line", (("-tab_width / 2.0", "tab_height / 2.0"), ("tab_width / 2.0", "tab_height / 2.0"))),
    )

    PositivePartialStart = (
        ("line", (("-tab_width / 2.0 + tab_height", "-tab_height / 2.0"), ("-tab_width / 2.0 + tab_height", "tab_height / 2.0"))),
        ("line", (("-tab_width / 2.0 + tab_height", "tab_height / 2.0"), ("tab_width / 2.0", "tab_height / 2.0"))),
        ("line", (("tab_width / 2.0", "tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
    )

    PositivePartialEnd = (
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("-tab_width / 2.0", "tab_height / 2.0"))),
        ("line", (("-tab_width / 2.0", "tab_height / 2.0"), ("tab_width / 2.0 - tab_height", "tab_height / 2.0"))),
        ("line", (("tab_width / 2.0 - tab_height", "tab_height / 2.0"), ("tab_width / 2.0 - tab_height", "-tab_height / 2.0"))),
    )

    NegativeFullStart = (
        ("line", (("-tab_width / 2.0 + tab_height", "-tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
    )

    NegativeFullEnd = (
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0 - tab_height", "-tab_height / 2.0"))),
    )

    NegativePartialStart = (
        ("line", (("-tab_width / 2.0 + tab_height", "-tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
    )

    NegativePartialEnd = (
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0 - tab_height", "-tab_height / 2.0"))),
    )

    CornerMap = {
        "positive_full_start": PositiveFullStart,
        "positive_full_end": PositiveFullEnd,
        "positive_partial_start": PositivePartialStart,
        "positive_partial_end": PositivePartialEnd,
        "negative_full_start": NegativeFullStart,
        "negative_full_end": NegativeFullEnd,
        "negative_partial_start": NegativePartialStart,
        "negative_partial_end": NegativePartialEnd,
    }

    def draw(self, **args):
        positive_flag = self.config.get("strip_positive", True)
        full_flag = self.config.get("corner_full", True)
        start_flag = self.config.get("corner_start", True)
        key1 = ["negative", "positive"][positive_flag]
        key2 = ["partial", "full"][full_flag]
        key3 = ["end", "start"][start_flag]
        key = str.join('_', [key1, key2, key3])
        self.Operations = self.CornerMap[key]
        super(CornerShape, self).draw(color=5, **args)

class PositiveTabShape(DrawShape):
    Operations = (
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("-tab_width / 2.0", "tab_height / 2.0"))),
        ("line", (("-tab_width / 2.0", "tab_height / 2.0"), ("tab_width / 2.0", "tab_height / 2.0"))),
        ("line", (("tab_width / 2.0", "tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
    )

class NegativeTabShape(DrawShape):
    Operations = (
        ("line", (("-tab_width / 2.0", "-tab_height / 2.0"), ("tab_width / 2.0", "-tab_height / 2.0"))),
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
        steps = range(ttc)
        translate = "tab_width * (step - %f) + (tab_width / 2.0)" % (len(steps) / 2.0)
        self.context.push_translation((translate, 0))
        shape_map = [NegativeTabShape(self.context), PositiveTabShape(self.context)]
        offset = int(self.config["strip_positive"])
        for step in steps:
            if step == steps[0]:
                self.context.push_config(step=step, corner_start=True)
                shape = CornerShape(self.context)
            elif step == steps[-1]:
                self.context.push_config(step=step, corner_start=False)
                shape = CornerShape(self.context)
            else:
                self.context.push_config(step=step)
                shape = shape_map[(step + offset) % 2]
            shape.draw(**args)
            self.context.pop_config()
        self.context.pop_transformation()
        self.context.pop_config()

class BoxFace(QuadShape):
    Positive = True
    Full = True

    def draw(self, **args):
        #super(BoxFace, self).draw(color=4, **args)
        ts = TabStrip(self.context)
        # top
        self.context.push_config(strip_tab_count=4, strip_width=self.config["face_width"], strip_positive=self.Positive, corner_full=self.Full, tab_height=2)
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

class BoxFace2(BoxFace):
    Positive = False
    Full = True

class BoxFace3(BoxFace):
    Positive = True
    Full = False

class BoxFace4(BoxFace):
    Positive = False
    Full = False

class BoxFactory(object):
    Defaults = {
        "face_width": 40,
        "face_height": 40,
    }

    def __init__(self, fn="box.dxf"):
        context = Context(fn)
        context.push_translation((25, 25))
        context.push_config(**self.Defaults)
        bf = BoxFace(context)
        bf.draw()
        context.pop_transformation()
        #
        context.push_translation((25, 25 + 42))
        bf = BoxFace2(context)
        bf.draw()
        context.pop_transformation()
        #
        context.push_translation((25 + 42, 25))
        bf = BoxFace3(context)
        bf.draw()
        context.pop_transformation()
        #
        context.push_translation((25 + 42, 25 + 42))
        bf = BoxFace4(context)
        bf.draw()
        context.pop_transformation()
        #
        context.save()
        
bf = BoxFactory()
os.system("inkscape -z box.dxf -e box.png")
