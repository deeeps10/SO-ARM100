from build123d import *
try:
    from ocp_vscode import show, set_port
    set_port(3939)
    _has_ocp = True
except Exception:
    _has_ocp = False

# Rectangle on plane Y=928.9194, corners filleted at R=70mm
# Plane normal points -Y so extrusion goes toward Y=888.91937256
_plane = Plane(
    origin=Vector(1892.9779, 928.9194, 65.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)

# Extrude toward Y=888.91937256 (distance=40.00002744mm along -Y normal)
with BuildPart() as part:
    with BuildSketch(_plane):
        with BuildLine():
            FilletPolyline(
                (0, 0), (510, 0), (510, 420), (0, 420),
                radius=70,
                close=True,
            )
        make_face()
    extrude(amount=40.00002744)

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCP.gp import gp_Pnt

# Plane shared by all 4 profiles (all points at Y=928.9194)
_cut_plane = Plane(
    origin=Vector(1892.9779, 928.9194, 65.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 1.0, 0.0),
)

_profiles = {
    'a': [
        (1962.9779, 928.9194, 171.4291),(1945.116, 928.9194, 153.1892),(1942.361, 928.9194, 149.8378),
        (1940.2267, 928.9194, 146.0606),(1938.7778, 928.9194, 141.9712),(1938.0576, 928.9194, 137.693),
        (1938.0879, 928.9194, 133.3546),(1938.8678, 928.9194, 129.0868),(1940.3737, 928.9194, 125.0181),
        (1942.5604, 928.9194, 121.271),(1945.3619, 928.9194, 117.9584),(1948.6942, 928.9194, 115.18),
        (1952.4564, 928.9194, 113.0195),(1956.5355, 928.9194, 111.542),(1960.8086, 928.9194, 110.7919),
        (1965.1471, 928.9194, 110.7919),(1969.4202, 928.9194, 111.542),(1973.4993, 928.9194, 113.0195),
        (1977.2617, 928.9194, 115.18),(1980.5937, 928.9194, 117.9584),(1983.3952, 928.9194, 121.271),
        (1985.582, 928.9194, 125.0181),(1987.0879, 928.9194, 129.0868),(1987.8677, 928.9194, 133.3546),
        (1987.8981, 928.9194, 137.693),(1987.1779, 928.9194, 141.9712),(1985.7289, 928.9194, 146.0606),
        (1983.5947, 928.9194, 149.8378),(1980.8397, 928.9194, 153.1892),
    ],
    'b': [
        (2332.9779, 928.9194, 171.4291),(2315.116, 928.9194, 153.1892),(2312.361, 928.9194, 149.8378),
        (2310.2267, 928.9194, 146.0606),(2308.7778, 928.9194, 141.9712),(2308.0576, 928.9194, 137.693),
        (2308.0879, 928.9194, 133.3546),(2308.8678, 928.9194, 129.0868),(2310.3737, 928.9194, 125.0181),
        (2312.5604, 928.9194, 121.271),(2315.3619, 928.9194, 117.9584),(2318.694, 928.9194, 115.18),
        (2322.4564, 928.9194, 113.0195),(2326.5355, 928.9194, 111.542),(2330.8086, 928.9194, 110.7919),
        (2335.1471, 928.9194, 110.7919),(2339.4202, 928.9194, 111.542),(2343.4993, 928.9194, 113.0195),
        (2347.2617, 928.9194, 115.18),(2350.5937, 928.9194, 117.9584),(2353.3952, 928.9194, 121.271),
        (2355.582, 928.9194, 125.0181),(2357.0879, 928.9194, 129.0868),(2357.8677, 928.9194, 133.3546),
        (2357.8981, 928.9194, 137.693),(2357.1779, 928.9194, 141.9712),(2355.7289, 928.9194, 146.0606),
        (2353.5947, 928.9194, 149.8378),(2350.8397, 928.9194, 153.1892),
    ],
    'c': [
        (1962.9779, 928.9194, 451.4291),(1945.116, 928.9194, 433.1892),(1942.361, 928.9194, 429.8378),
        (1940.2267, 928.9194, 426.0606),(1938.7778, 928.9194, 421.9712),(1938.0576, 928.9194, 417.6929),
        (1938.0879, 928.9194, 413.3546),(1938.8678, 928.9194, 409.0868),(1940.3737, 928.9194, 405.0181),
        (1942.5604, 928.9194, 401.271),(1945.3619, 928.9194, 397.9584),(1948.6942, 928.9194, 395.18),
        (1952.4564, 928.9194, 393.0195),(1956.5355, 928.9194, 391.542),(1960.8086, 928.9194, 390.7919),
        (1965.1471, 928.9194, 390.7919),(1969.4202, 928.9194, 391.542),(1973.4993, 928.9194, 393.0195),
        (1977.2617, 928.9194, 395.18),(1980.5937, 928.9194, 397.9584),(1983.3952, 928.9194, 401.271),
        (1985.582, 928.9194, 405.0181),(1987.0879, 928.9194, 409.0868),(1987.8677, 928.9194, 413.3546),
        (1987.8981, 928.9194, 417.6929),(1987.1779, 928.9194, 421.9712),(1985.7289, 928.9194, 426.0606),
        (1983.5947, 928.9194, 429.8378),(1980.8397, 928.9194, 433.1892),
    ],
    'd': [
        (2332.9779, 928.9194, 451.4291),(2315.116, 928.9194, 433.1892),(2312.361, 928.9194, 429.8378),
        (2310.2267, 928.9194, 426.0606),(2308.7778, 928.9194, 421.9712),(2308.0576, 928.9194, 417.6929),
        (2308.0879, 928.9194, 413.3546),(2308.8678, 928.9194, 409.0868),(2310.3737, 928.9194, 405.0181),
        (2312.5604, 928.9194, 401.271),(2315.3619, 928.9194, 397.9584),(2318.694, 928.9194, 395.18),
        (2322.4564, 928.9194, 393.0195),(2326.5355, 928.9194, 391.542),(2330.8086, 928.9194, 390.7919),
        (2335.1471, 928.9194, 390.7919),(2339.4202, 928.9194, 391.542),(2343.4993, 928.9194, 393.0195),
        (2347.2617, 928.9194, 395.18),(2350.5937, 928.9194, 397.9584),(2353.3952, 928.9194, 401.271),
        (2355.582, 928.9194, 405.0181),(2357.0879, 928.9194, 409.0868),(2357.8677, 928.9194, 413.3546),
        (2357.8981, 928.9194, 417.6929),(2357.1779, 928.9194, 421.9712),(2355.7289, 928.9194, 426.0606),
        (2353.5947, 928.9194, 429.8378),(2350.8397, 928.9194, 433.1892),
    ],
}

for _name, _pts in _profiles.items():
    _poly = BRepBuilderAPI_MakePolygon()
    for _pt in _pts:
        _poly.Add(gp_Pnt(*_pt))
    _poly.Close()
    _wire = Wire(_poly.Wire())
    _face = Face(BRepBuilderAPI_MakeFace(_cut_plane.wrapped, _wire.wrapped, True).Face())
    # Cut through body in -Y direction (body thickness = 40mm, use 50mm to ensure full cut)
    _cut_solid = Solid.extrude(_face, Vector(0.0, -50.0, 0.0))
    _result = part.part.cut(_cut_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Rectangle extrude: Y=888.9194 down to Y=875.5153656 (13.4040344mm) --
_rect_plane = Plane(
    origin=Vector(2068.4778, 888.9194, 196.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
# Local 2D: x→world X, y→world Z
# width=159.0001, height=157.9999
_rect_wire_plane = Plane(
    origin=Vector(2068.4778, 888.9194, 196.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
_rpoly = BRepBuilderAPI_MakePolygon()
for _rp in [(2068.4778, 888.9194, 196.6977),(2227.4779, 888.9194, 196.6977),
            (2227.4779, 888.9194, 354.6976),(2068.4778, 888.9194, 354.6976)]:
    _rpoly.Add(gp_Pnt(*_rp))
_rpoly.Close()
_rect_wire2 = Wire(_rpoly.Wire())
_rect_face2 = Face(BRepBuilderAPI_MakeFace(_rect_plane.wrapped, _rect_wire2.wrapped, True).Face())
_rect_solid2 = Solid.extrude(_rect_face2, Vector(0.0, -13.4040344, 0.0))
_result = part.part.fuse(_rect_solid2)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Tapered extrude from edges 377,380,382,383 (Y=875.5154) to Y=863.51539612 at 44deg --
_taper_plane = Plane(
    origin=Vector(2068.4778, 875.5154, 196.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
_tpoly = BRepBuilderAPI_MakePolygon()
for _tp in [(2068.4778, 875.5154, 196.6977), (2227.4779, 875.5154, 196.6977),
            (2227.4779, 875.5154, 354.6976), (2068.4778, 875.5154, 354.6976)]:
    _tpoly.Add(gp_Pnt(*_tp))
_tpoly.Close()
_taper_wire = Wire(_tpoly.Wire())
_taper_face = Face(BRepBuilderAPI_MakeFace(_taper_plane.wrapped, _taper_wire.wrapped, True).Face())
# Distance: 875.5154 - 863.51539612 = 12.00000388mm in -Y
_taper_solid = Solid.extrude_taper(_taper_face, Vector(0.0, -12.00000388, 0.0), taper=-44)
_result = part.part.fuse(_taper_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Extrude rectangle from edges 391,390,388,385 (Y=863.5154) to Y=852.91938782 --
_rect3_plane = Plane(
    origin=Vector(2056.8895, 863.5154, 185.1094),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
_r3poly = BRepBuilderAPI_MakePolygon()
for _r3p in [(2056.8895, 863.5154, 185.1094), (2239.0662, 863.5154, 185.1094),
             (2239.0662, 863.5154, 366.2859), (2056.8895, 863.5154, 366.2859)]:
    _r3poly.Add(gp_Pnt(*_r3p))
_r3poly.Close()
_rect3_wire = Wire(_r3poly.Wire())
_rect3_face = Face(BRepBuilderAPI_MakeFace(_rect3_plane.wrapped, _rect3_wire.wrapped, True).Face())
_rect3_solid = Solid.extrude(_rect3_face, Vector(0.0, -10.59601218, 0.0))
_result = part.part.fuse(_rect3_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

export_step(part.part, "/Users/softage/Desktop/Print_Leader_SO_ARM100_08k_UP_Prusa - WaveShare_Mounting_Plate_01d-2.step")
export_stl(part.part, "/Users/softage/Desktop/Print_Leader_SO_ARM100_08k_UP_Prusa - WaveShare_Mounting_Plate_01d-2.stl")

if _has_ocp:
    show(part)
