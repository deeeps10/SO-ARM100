# Units: mm throughout.

from build123d import *
import math

_plane = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane) as sk_main:
    with BuildLine():
        Line((0.0, 259.0), (196.0, 259.0))
        Line((196.0, 259.0), (196.0, 0.0))
        Line((196.0, 0.0), (0.0, 0.0))
        Line((0.0, 0.0), (0.0, 259.0))
    _inc_edges = list(BuildSketch._get_context().pending_edges)

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire = Wire.combine(_inc_edges)[0]
_wire = _wire.moved(_plane.location)
_mkf = BRepBuilderAPI_MakeFace(_plane.wrapped, _wire.wrapped, True)
_face = Face(_mkf.Face())

with BuildPart() as part:
    _solid = Solid.extrude(_face, Vector(0.0, 0.0, -50.0))
    add(_solid)

# -- Arc profile add-extrude from Z=100 to Z=50 --
_plane_arc = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane_arc) as sk_arc:
    with BuildLine():
        Line((196.0, 185.0), (216.0, 185.0))
        RadiusArc((216.0, 185.0), (216.0, 74.0), 55.5)
        Line((216.0, 74.0), (196.0, 74.0))
        Line((196.0, 74.0), (196.0, 185.0))
    _inc_edges_arc = list(BuildSketch._get_context().pending_edges)
_wire_arc = Wire.combine(_inc_edges_arc)[0]
_wire_arc = _wire_arc.moved(_plane_arc.location)
_mkf_arc = BRepBuilderAPI_MakeFace(_plane_arc.wrapped, _wire_arc.wrapped, True)
_face_arc = Face(_mkf_arc.Face())
_arc_solid = Solid.extrude(_face_arc, Vector(0.0, 0.0, -50.0))
_result = part.part.fuse(_arc_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Cut profile from Z=100 down to Z=0 (50mm) --
_plane_cut = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane_cut) as sk_cut:
    with BuildLine():
        Line((50.0, 201.5), (57.5, 209.0))
        Line((57.5, 209.0), (164.0, 209.0))
        Line((164.0, 209.0), (164.0, 146.0))
        Line((164.0, 146.0), (146.0, 146.0))
        Line((146.0, 146.0), (146.0, 113.0))
        Line((146.0, 113.0), (164.0, 113.0))
        Line((164.0, 113.0), (164.0, 50.0))
        Line((164.0, 50.0), (57.5, 50.0))
        Line((57.5, 50.0), (50.0, 57.5))
        Line((50.0, 57.5), (50.0, 201.5))
    _inc_edges_cut = list(BuildSketch._get_context().pending_edges)
_wire_cut = Wire.combine(_inc_edges_cut)[0]
_wire_cut = _wire_cut.moved(_plane_cut.location)
_mkf_cut = BRepBuilderAPI_MakeFace(_plane_cut.wrapped, _wire_cut.wrapped, True)
_face_cut = Face(_mkf_cut.Face())
_cut_solid = Solid.extrude(_face_cut, Vector(0.0, 0.0, -50.0))
_result = part.part.cut(_cut_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Chamfer: inner cut loop straight edges at Z=100 --
def _find_edge(solid, p1, p2, tol=0.05):
    for e in solid.edges():
        verts = e.vertices()
        if len(verts) != 2: continue
        pts = [(v.X, v.Y, v.Z) for v in verts]
        if (all(abs(pts[0][i]-p1[i])<tol for i in range(3)) and all(abs(pts[1][i]-p2[i])<tol for i in range(3))) or \
           (all(abs(pts[0][i]-p2[i])<tol for i in range(3)) and all(abs(pts[1][i]-p1[i])<tol for i in range(3))):
            return e
    return None

_chamfer_coords = [
    ((50.0,57.5,100.0),   (50.0,201.5,100.0)),
    ((164.0,50.0,100.0),  (57.5,50.0,100.0)),
    ((164.0,113.0,100.0), (164.0,50.0,100.0)),
    ((146.0,113.0,100.0), (164.0,113.0,100.0)),
    ((146.0,146.0,100.0), (146.0,113.0,100.0)),
    ((164.0,146.0,100.0), (146.0,146.0,100.0)),
    ((164.0,209.0,100.0), (164.0,146.0,100.0)),
    ((57.5,209.0,100.0),  (164.0,209.0,100.0)),
]
with BuildPart() as _ch_bp:
    add(part.part)
    _ch_edges = [_find_edge(_ch_bp.part, p1, p2) for p1, p2 in _chamfer_coords]
    _ch_edges = [e for e in _ch_edges if e is not None]
    try:
        chamfer(_ch_edges, length=6.00000381, length2=6.66367531)
    except Exception as _ce:
        print('WARNING: Chamfer failed:', _ce)
part.part = _ch_bp.part

# -- Chamfer2: outermost edges at Z=100 --
_outer_chamfer_coords = [
    ((0.0,259.0,100.0),   (196.0,259.0,100.0)),
    ((0.0,0.0,100.0),     (0.0,259.0,100.0)),
    ((196.0,0.0,100.0),   (0.0,0.0,100.0)),
    ((196.0,259.0,100.0), (196.0,185.0,100.0)),
    ((196.0,74.0,100.0),  (196.0,0.0,100.0)),
    ((196.0,185.0,100.0), (216.0,185.0,100.0)),
    ((216.0,74.0,100.0),  (196.0,74.0,100.0)),
    ((216.0,185.0,100.0), (216.0,74.0,100.0)),
]
with BuildPart() as _ch2_bp:
    add(part.part)
    _ch2_edges = [_find_edge(_ch2_bp.part, p1, p2) for p1, p2 in _outer_chamfer_coords]
    _ch2_edges = [e for e in _ch2_edges if e is not None]
    try:
        chamfer(_ch2_edges, length=5.40242553, length2=6.00000381)
    except Exception as _ce:
        print('WARNING: Chamfer2 failed:', _ce)
part.part = _ch2_bp.part

# -- Two rectangle add-extrudes from Z=100 to Z=50 --
_rect_pairs = [
    [(176.1812,124.4291),(161.4964,124.4291),(161.4964,112.9966),(176.1812,112.9966)],
    [(176.7726,135.8616),(162.7776,135.8616),(162.7776,145.5201),(176.7726,145.5201)],
]
_rp = Plane(origin=Vector(0.0,0.0,100.0),x_dir=Vector(1.0,0.0,0.0),z_dir=Vector(0.0,0.0,1.0))
for _rpts in _rect_pairs:
    with BuildSketch(_rp) as _sk_r:
        with BuildLine():
            for _ri in range(len(_rpts)):
                Line(_rpts[_ri], _rpts[(_ri+1) % len(_rpts)])
        _inc_r = list(BuildSketch._get_context().pending_edges)
    _wr = Wire.combine(_inc_r)[0]
    _wr = _wr.moved(_rp.location)
    _fr = Face(BRepBuilderAPI_MakeFace(_rp.wrapped, _wr.wrapped, True).Face())
    _rs = Solid.extrude(_fr, Vector(0.0, 0.0, -50.0))
    _result = part.part.fuse(_rs)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Four 15mm diameter circle cuts along Z --
for _cx, _cy in [(50.0,209.0),(50.0,50.0),(164.0,113.0),(164.0,146.0)]:
    _c_plane = Plane(origin=Vector(_cx, _cy, 100.0))
    _c_edge = Edge.make_circle(7.5, _c_plane)
    _c_wire = Wire([_c_edge])
    _c_face = Face(BRepBuilderAPI_MakeFace(_c_wire.wrapped).Face())
    _c_solid = Solid.extrude(_c_face, Vector(0.0, 0.0, -50.0))
    _result = part.part.cut(_c_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Two triangle cuts extending to X=65 --
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCP.gp import gp_Pnt

def _make_tri_solid(pts_3d, plane, extrude_vec):
    _p = BRepBuilderAPI_MakePolygon()
    for _pt in pts_3d:
        _p.Add(gp_Pnt(_pt[0],_pt[1],_pt[2]))
    _p.Close()
    _w = Wire(_p.Wire())
    _f = Face(BRepBuilderAPI_MakeFace(plane.wrapped,_w.wrapped,True).Face())
    return Solid.extrude(_f, extrude_vec)

# Triangle 1: in Y=50 plane, extrude +Y 15mm (to Y=65)
_t1_plane = Plane(origin=Vector(0.0,50.0,0.0),x_dir=Vector(1.0,0.0,0.0),z_dir=Vector(0.0,1.0,0.0))
_ts1 = _make_tri_solid([(50.0,50.0,100.0),(44.0,50.0,100.0),(50.0,50.0,93.3363)], _t1_plane, Vector(0.0,15.0,0.0))
_result = part.part.cut(_ts1)
part.part = _result[0] if isinstance(_result,ShapeList) else _result

# Triangle 2: in X=50 plane, extrude +X 15mm (to X=65)
_t2_plane = Plane(origin=Vector(50.0,0.0,0.0),x_dir=Vector(0.0,1.0,0.0),z_dir=Vector(1.0,0.0,0.0))
_ts2 = _make_tri_solid([(50.0,44.0,100.0),(50.0,50.0,100.0),(50.0,50.0,93.3363)], _t2_plane, Vector(15.0,0.0,0.0))
_result = part.part.cut(_ts2)
part.part = _result[0] if isinstance(_result,ShapeList) else _result

# Triangle 3: in X=50 plane (Y=209-215), extrude +X 15mm (to X=65)
_t3_plane = Plane(origin=Vector(50.0,0.0,0.0),x_dir=Vector(0.0,1.0,0.0),z_dir=Vector(1.0,0.0,0.0))
_ts3 = _make_tri_solid([(50.0,209.0,100.0),(50.0,215.0,100.0),(50.0,209.0,93.3363)], _t3_plane, Vector(15.0,0.0,0.0))
_result = part.part.cut(_ts3)
part.part = _result[0] if isinstance(_result,ShapeList) else _result

# -- Triangle cut from Y=50 to Y=209 --
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCP.gp import gp_Pnt
_tri_pts = [(50.0,50.0,100.0),(44.0,50.0,100.0),(50.0,50.0,93.3363)]
_poly = BRepBuilderAPI_MakePolygon()
for _pt in _tri_pts:
    _poly.Add(gp_Pnt(_pt[0],_pt[1],_pt[2]))
_poly.Close()
_tri_wire = Wire(_poly.Wire())
_tri_plane = Plane(origin=Vector(0.0,50.0,0.0),x_dir=Vector(1.0,0.0,0.0),z_dir=Vector(0.0,1.0,0.0))
_tri_face = Face(BRepBuilderAPI_MakeFace(_tri_plane.wrapped,_tri_wire.wrapped,True).Face())
_tri_solid = Solid.extrude(_tri_face, Vector(0.0,159.0,0.0))
_result = part.part.cut(_tri_solid)
part.part = _result[0] if isinstance(_result,ShapeList) else _result

# -- Closed polygon cut from Z=95.1061 to Z=100 --
_oval_pts = [
    (200.8839,143.3712,95.1061),(202.7815,144.2663,95.1061),(206.4883,145.4522,95.1061),
    (218.5092,146.5769,95.1061),(225.6384,146.2485,95.1061),(230.9776,145.4292,95.1061),
    (234.6381,144.3626,95.1061),(237.3721,143.1271,95.1061),(240.5831,140.8231,95.1061),
    (242.161,139.1457,95.1061),(243.3693,137.3807,95.1061),(244.3259,135.3613,95.1061),
    (244.9619,133.131,95.1061),(245.2821,129.74,95.1061),(245.2246,128.9219,95.1061),
    (245.0938,127.061,95.1061),(244.5576,124.6349,95.1061),(244.101,123.4777,95.1061),
    (243.7289,122.5345,95.1061),(243.399,121.9804,95.1061),(242.5401,120.5375,95.1061),
    (241.4992,119.2922,95.1061),(241.2171,118.9546,95.1061),(239.1967,117.2131,95.1061),
    (238.4258,116.7396,95.1061),(236.9507,115.8335,95.1061),(234.5783,114.7634,95.1061),
    (233.5991,114.4714,95.1061),(230.9945,113.6947,95.1061),(225.8951,112.9491,95.1061),
    (225.1199,112.8358,95.1061),(218.98,112.6026,95.1061),(213.8531,112.766,95.1061),
    (208.0562,113.4706,95.1061),(204.0514,114.5116,95.1061),(200.2923,116.1966,95.1061),
    (198.6173,117.2811,95.1061),(198.1472,117.5854,95.1061),(196.4274,119.1116,95.1061),
    (195.1547,120.6594,95.1061),(194.2548,122.1842,95.1061),(193.4001,124.3753,95.1061),
    (192.9112,126.6345,95.1061),(192.718,129.4796,95.1061),(192.8923,132.205,95.1061),
    (193.4203,134.6832,95.1061),(194.225,136.7643,95.1061),(195.3145,138.6292,95.1061),
    (196.6762,140.2657,95.1061),(198.3861,141.7823,95.1061),
]
_oval_poly = BRepBuilderAPI_MakePolygon()
for _pt in _oval_pts:
    _oval_poly.Add(gp_Pnt(_pt[0],_pt[1],_pt[2]))
_oval_poly.Close()
_oval_wire = Wire(_oval_poly.Wire())
_oval_plane = Plane(origin=Vector(0.0,0.0,95.1061),x_dir=Vector(1.0,0.0,0.0),z_dir=Vector(0.0,0.0,1.0))
_oval_face = Face(BRepBuilderAPI_MakeFace(_oval_plane.wrapped,_oval_wire.wrapped,True).Face())
_oval_solid = Solid.extrude(_oval_face, Vector(0.0,0.0,4.8939))

with BuildPart() as _oval_taper_bp:
    add(_oval_face)
    extrude(amount=-9.1061, taper=42)
_oval_taper_solid = _oval_taper_bp.part

# -- Inner oval profile cut from Z=100 to Z=86 (14mm) --
_inner_oval_pts = [
    (232.8379,123.9509,100.0),(231.4597,123.2352,100.0),(229.4503,122.571,100.0),
    (224.3515,121.7785,100.0),(218.98,121.5769,100.0),(216.2778,121.6288,100.0),
    (210.407,122.2427,100.0),(207.2789,123.0484,100.0),(205.1278,124.0409,100.0),
    (204.2227,124.6478,100.0),(203.4216,125.339,100.0),(202.7872,126.0805,100.0),
    (202.3096,126.8516,100.0),(201.9654,127.6793,100.0),(201.7646,128.5164,100.0),
    (201.6923,129.5196,100.0),(201.7482,130.3557,100.0),(201.9259,131.2439,100.0),
    (202.241,132.1097,100.0),(202.6741,132.8999,100.0),(203.3295,133.7371,100.0),
    (204.2972,134.6442,100.0),(205.5618,135.4994,100.0),(206.9547,136.1479,100.0),
    (209.0613,136.7736,100.0),(213.3516,137.4081,100.0),(218.4091,137.6026,100.0),
    (222.9854,137.4849,100.0),(228.2883,136.8829,100.0),(231.1464,136.0962,100.0),
    (232.7899,135.3437,100.0),(233.8664,134.6401,100.0),(234.2709,134.2885,100.0),
    (234.9794,133.4986,100.0),(235.5696,132.5724,100.0),(235.9558,131.6743,100.0),
    (236.2023,130.7234,100.0),(236.3077,129.5196,100.0),(236.286,129.0714,100.0),
    (236.1562,128.1505,100.0),(235.8891,127.3012,100.0),(235.5093,126.5458,100.0),
    (234.9272,125.7296,100.0),(234.1197,124.9066,100.0),
]
_inner_poly = BRepBuilderAPI_MakePolygon()
for _pt in _inner_oval_pts:
    _inner_poly.Add(gp_Pnt(_pt[0],_pt[1],_pt[2]))
_inner_poly.Close()
_inner_wire = Wire(_inner_poly.Wire())
_inner_plane = Plane(origin=Vector(0.0,0.0,100.0),x_dir=Vector(1.0,0.0,0.0),z_dir=Vector(0.0,0.0,1.0))
_inner_face = Face(BRepBuilderAPI_MakeFace(_inner_plane.wrapped,_inner_wire.wrapped,True).Face())
_inner_solid = Solid.extrude(_inner_face, Vector(0.0,0.0,-14.0))

# -- Mirror along Z=50 plane --
_mirror_plane = Plane(origin=(0.0, 0.0, 50.0), z_dir=(0.0, 0.0, 1.0))
_mirrored = part.part.mirror(_mirror_plane)
_final = Compound(children=[part.part, _mirrored])

# -- 50-point oval cuts after mirror --
_oval_cut = []
for _s in _final.solids():
    _r = _s.cut(_oval_solid)
    _r = _r[0] if isinstance(_r,ShapeList) else _r
    _r = _r.cut(_oval_taper_solid)
    _r = _r[0] if isinstance(_r,ShapeList) else _r
    _oval_cut.append(_r)
_final = Compound(children=_oval_cut)

# -- 44-point inner oval fuse after mirror --
_fused = []
for _s in _final.solids():
    _r = _s.fuse(_inner_solid)
    _fused.append(_r[0] if isinstance(_r,ShapeList) else _r)
_final = Compound(children=_fused)

# -- Triangle cut through body along Y axis at Y=129.5 (after mirror) --
_tri_y_poly = BRepBuilderAPI_MakePolygon()
for _pt in [(155.2475,129.5,-39.2603),(292.1472,129.5,-39.2603),(288.0097,129.5,108.1871)]:
    _tri_y_poly.Add(gp_Pnt(_pt[0],_pt[1],_pt[2]))
_tri_y_poly.Close()
_tri_y_wire = Wire(_tri_y_poly.Wire())
_tri_y_plane = Plane(origin=Vector(0.0,129.5,0.0),x_dir=Vector(1.0,0.0,0.0),z_dir=Vector(0.0,1.0,0.0))
_tri_y_face = Face(BRepBuilderAPI_MakeFace(_tri_y_plane.wrapped,_tri_y_wire.wrapped,True).Face())
_tri_y_pos = Solid.extrude(_tri_y_face, Vector(0.0,200.0,0.0))
_tri_y_neg = Solid.extrude(_tri_y_face, Vector(0.0,-200.0,0.0))
_cut = []
for _s in _final.solids():
    _r = _s.cut(_tri_y_pos)
    _r = _r[0] if isinstance(_r,ShapeList) else _r
    _r = _r.cut(_tri_y_neg)
    _r = _r[0] if isinstance(_r,ShapeList) else _r
    _cut.append(_r)
_final = Compound(children=_cut)

export_step(_final, "/Users/softage/Documents/stls/5may/Lego_Size_Test_02_zero.step")
export_stl(_final, "/Users/softage/Documents/stls/5may/Lego_Size_Test_02_zero.stl")
