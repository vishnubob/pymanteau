from dxfwrite import DXFEngine as dxf


class CutMacro(object):
    DEFAULTS = {}

    def __init__(self, canvas, layer="LINES", offset=(0,0), rotation=0, color=0, **kw):
        self.canvas = canvas
        self.layer = layer
        self.offset = offset
        self.rotation = rotation
        self.color = color
        params = self.Defaults.copy()
        params.update(kw)
        self.__dict__.update(params)
    
    def draw(self):
        pass

class ScrewReceiverMacro(CutMacro):
    def draw(self):
        drawing = dxf.drawing('test.dxf')
        drawing.add_layer('LINES')
        drawing.add(dxf.line((0, 0), (1, 0), color=7, layer='LINES'))
        drawing.save()

class TabMacro(CutMacro):
    DEFAULT = {
        'width': 10,
        'height': 2,
    }

    def draw(self):
        drawing.add(dxf.line((0, 0), (1, 0), color=7, layer='LINES'))

class BoxFactory(object):
    def __init__(self, fn="box.dxf"):
        drawing = dxf.drawing(fn)
        drawing.add_layer('LINES')
        drawing.add(dxf.line((0, 0), (1, 0), color=7, layer='LINES'))
        drawing.save()
        
bf = BoxFactory()

