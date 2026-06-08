# Units: mm throughout.

from build123d import *
import math


_plane = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane) as sk_Lego:
    with BuildLine():
        Line((0.0, 0.0), (195.0, 0.0))
        Line((195.0, 0.0), (195.0, 73.7143))
        Line((195.0, 73.7143), (215.0, 73.7143))
        RadiusArc((215.0, 73.7143), (215.0, 184.2857), -55.2857)
        Line((215.0, 184.2857), (195.0, 184.2857))
        Line((195.0, 184.2857), (195.0, 258.0))
        Line((195.0, 258.0), (0.0, 258.0))
        Line((0.0, 258.0), (0.0, 0.0))
    _inc_edges = list(BuildSketch._get_context().pending_edges)

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire = Wire.combine(_inc_edges)[0]
_wire = _wire.moved(_plane.location)
_mkf = BRepBuilderAPI_MakeFace(_plane.wrapped, _wire.wrapped, True)
_face = Face(_mkf.Face())

_plane_cut = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane_cut) as sk_cut:
    with BuildLine():
        Line((163.0, 208.0), (163.0, 145.5))
        Line((163.0, 145.5), (145.0, 145.5))
        Line((145.0, 145.5), (145.0, 112.5))
        Line((145.0, 112.5), (163.0, 112.5))
        Line((163.0, 112.5), (163.0, 50.0))
        Line((163.0, 50.0), (50.0, 50.0))
        Line((50.0, 50.0), (50.0, 208.0))
        Line((50.0, 208.0), (163.0, 208.0))
    _inc_edges_cut = list(BuildSketch._get_context().pending_edges)
_wire_cut = Wire.combine(_inc_edges_cut)[0]
_wire_cut = _wire_cut.moved(_plane_cut.location)
_mkf_cut = BRepBuilderAPI_MakeFace(_plane_cut.wrapped, _wire_cut.wrapped, True)
_face_cut = Face(_mkf_cut.Face())

with BuildPart() as part:
    _vec = Vector(0.0, 0.0, 1.0) * -50.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid)

    # -- Cut profile along Z --
    _cut_vec = Vector(0.0, 0.0, 1.0) * -50.0
    _cut_solid = Solid.extrude(_face_cut, _cut_vec)
    _result = part.part.cut(_cut_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

    # -- Chamfer: two-length 6.00000381mm / 6.66367531mm on edges 16,15,22,18,17,19,20,21 --
    try:
        chamfer([part.edges()[16], part.edges()[15], part.edges()[22], part.edges()[18], part.edges()[17], part.edges()[19], part.edges()[20], part.edges()[21]], length=6.00000381, length2=6.66367531)
    except Exception as _ce:
        print('WARNING: Chamfer failed:', _ce)

    # -- Chamfer2: two-length 6.00000381mm / 6.66367531mm on edges 8,10,12,14,15,13,11,9 --
    try:
        chamfer([part.edges()[8], part.edges()[10], part.edges()[12], part.edges()[14], part.edges()[15], part.edges()[13], part.edges()[11], part.edges()[9]], length=5.40242553 , length2=6.00000381)
    except Exception as _ce:
        print('WARNING: Chamfer2 failed:', _ce)


# -- Four rectangular profile cuts extruded from Z=100 down to Z=80 --
_rect_profiles = [
    [(39.9924, 216.3689), (46.8096, 216.3689), (46.8096, 211.1663), (39.9924, 211.1663)],
    [(170.6733, 138.0396), (162.9568, 138.0396), (162.9568, 143.2364), (170.6733, 143.2364)],
    [(165.4765, 114.1025), (173.508, 114.1025), (173.508, 120.0868), (165.4765, 120.0868)],
    [(46.4225, 41.9676), (41.3349, 41.9676), (41.3349, 47.7651), (46.4225, 47.7651)],
]
_rect_plane = Plane(origin=Vector(0.0, 0.0, 100.0), x_dir=Vector(1.0, 0.0, 0.0), z_dir=Vector(0.0, 0.0, 1.0))
for _rpts in _rect_profiles:
    with BuildSketch(_rect_plane) as _sk_rect:
        with BuildLine():
            for _ri in range(len(_rpts)):
                Line(_rpts[_ri], _rpts[(_ri+1) % len(_rpts)])
        _inc_edges_rect = list(BuildSketch._get_context().pending_edges)
    _wire_rect = Wire.combine(_inc_edges_rect)[0]
    _wire_rect = _wire_rect.moved(_rect_plane.location)
    _mkf_rect = BRepBuilderAPI_MakeFace(_rect_plane.wrapped, _wire_rect.wrapped, True)
    _face_rect = Face(_mkf_rect.Face())
    _rect_solid = Solid.extrude(_face_rect, Vector(0.0, 0.0, -20.0))
    _result = part.part.fuse(_rect_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Four 15mm diameter circle cuts along Z --
_circle_centers = [
    (163.0, 112.5),
    (163.0, 145.5),
    (50.0, 208.0),
    (50.0, 50.0),
]
for _cx, _cy in _circle_centers:
    _c_plane = Plane(origin=Vector(_cx, _cy, 100.0))
    _c_edge = Edge.make_circle(7.5, _c_plane)
    _c_wire = Wire([_c_edge])
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace as _MF
    _c_face = Face(_MF(_c_wire.wrapped).Face())
    _c_solid = Solid.extrude(_c_face, Vector(0.0, 0.0, -50.0))
    _result = part.part.cut(_c_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Sketch for notch profile at Z=80.5535 --
_plane_notch = Plane(
    origin=Vector(0.0, 0.0, 80.5535),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane_notch) as sk_notch:
    with BuildLine():
        Line((243.0, 122.9505), (234.6667, 128.3091))
        Line((234.6667, 128.3091), (234.6667, 118.0527))
        Line((234.6667, 118.0527), (193.0, 118.0527))
        Line((193.0, 118.0527), (193.0, 109.0783))
        Line((193.0, 109.0783), (243.0, 109.0783))
        Line((243.0, 109.0783), (243.0, 122.9505))
    _inc_edges_notch = list(BuildSketch._get_context().pending_edges)
_wire_notch = Wire.combine(_inc_edges_notch)[0]
_wire_notch = _wire_notch.moved(_plane_notch.location)
_mkf_notch = BRepBuilderAPI_MakeFace(_plane_notch.wrapped, _wire_notch.wrapped, True)
_face_notch = Face(_mkf_notch.Face())

# -- Cut 1: profile extruded upward to Z=100 (19.4465mm) --
_cut1_solid = Solid.extrude(_face_notch, Vector(0.0, 0.0, 19.4465))
_result = part.part.cut(_cut1_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Cut 2: same profile extruded downward to Z=76 (4.5535mm) with 42 degree taper --
with BuildPart() as _notch_taper_bp:
    add(_face_notch)
    extrude(amount=-4.5535, taper=42)
_result = part.part.cut(_notch_taper_bp.part)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Sketch for second notch profile at Z=80.5535 --
_plane_notch2 = Plane(
    origin=Vector(0.0, 0.0, 80.5535),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_plane_notch2) as sk_notch2:
    with BuildLine():
        Line((215.4359, 157.1552), (207.1026, 157.1552))
        Line((207.1026, 157.1552), (207.1026, 139.8475))
        Line((207.1026, 139.8475), (215.4359, 139.8475))
        Line((215.4359, 139.8475), (215.4359, 157.1552))
    _inc_edges_notch2 = list(BuildSketch._get_context().pending_edges)
_wire_notch2 = Wire.combine(_inc_edges_notch2)[0]
_wire_notch2 = _wire_notch2.moved(_plane_notch2.location)
_mkf_notch2 = BRepBuilderAPI_MakeFace(_plane_notch2.wrapped, _wire_notch2.wrapped, True)
_face_notch2 = Face(_mkf_notch2.Face())

# -- Cut 3: second profile extruded upward to Z=100 (19.4465mm) --
_cut3_solid = Solid.extrude(_face_notch2, Vector(0.0, 0.0, 19.4465))
_result = part.part.cut(_cut3_solid)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Cut 4: second profile extruded downward to Z=76 (4.5535mm) with 42 degree taper --
with BuildPart() as _notch2_taper_bp:
    add(_face_notch2)
    extrude(amount=-4.5535, taper=42)
_result = part.part.cut(_notch2_taper_bp.part)
part.part = _result[0] if isinstance(_result, ShapeList) else _result

# -- Mirror along XY plane at Z=50 --
_mirror_plane = Plane(origin=(0.0, 0.0, 50.0), z_dir=(0.0, 0.0, 1.0))
_mirrored = part.part.mirror(_mirror_plane)
_final = Compound(children=[part.part, _mirrored])

# -- Rectangle add-extrude from Z=0 to Z=24.5mm --
_plane_rect2 = Plane(origin=Vector(0.0, 0.0, 0.0), x_dir=Vector(1.0, 0.0, 0.0), z_dir=Vector(0.0, 0.0, 1.0))
with BuildSketch(_plane_rect2) as _sk_rect2:
    with BuildLine():
        Line((191.5177, 101.5021), (227.393, 101.5021))
        Line((227.393, 101.5021), (227.393, 164.3646))
        Line((227.393, 164.3646), (191.5177, 164.3646))
        Line((191.5177, 164.3646), (191.5177, 101.5021))
    _inc_edges_rect2 = list(BuildSketch._get_context().pending_edges)
_wire_rect2 = Wire.combine(_inc_edges_rect2)[0]
_wire_rect2 = _wire_rect2.moved(_plane_rect2.location)
_mkf_rect2 = BRepBuilderAPI_MakeFace(_plane_rect2.wrapped, _wire_rect2.wrapped, True)
_face_rect2 = Face(_mkf_rect2.Face())
_rect2_solid = Solid.extrude(_face_rect2, Vector(0.0, 0.0, 24.5))
_fused_solids = []
for _s in _final.solids():
    _r = _s.fuse(_rect2_solid)
    _r = _r[0] if isinstance(_r, ShapeList) else _r
    _fused_solids.append(_r)
_final = Compound(children=_fused_solids)

# -- Triangle cut through body along Y axis --
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCP.gp import gp_Pnt
_tri_pts = [(291.501, 129.0, 113.1752), (297.7419, 129.0, -14.8483), (174.3929, 129.0, -16.8865)]
_poly = BRepBuilderAPI_MakePolygon()
for _pt in _tri_pts:
    _poly.Add(gp_Pnt(_pt[0], _pt[1], _pt[2]))
_poly.Close()
_tri_wire = Wire(_poly.Wire())
_tri_plane = Plane(origin=Vector(0.0, 129.0, 0.0), x_dir=Vector(1.0, 0.0, 0.0), z_dir=Vector(0.0, 1.0, 0.0))
_mkf_tri = BRepBuilderAPI_MakeFace(_tri_plane.wrapped, _tri_wire.wrapped, True)
_tri_face = Face(_mkf_tri.Face())
_tri_cut_pos = Solid.extrude(_tri_face, Vector(0.0, 200.0, 0.0))
_tri_cut_neg = Solid.extrude(_tri_face, Vector(0.0, -200.0, 0.0))
_cut_solids = []
for _s in _final.solids():
    _r = _s.cut(_tri_cut_pos)
    _r = _r[0] if isinstance(_r, ShapeList) else _r
    _r = _r.cut(_tri_cut_neg)
    _r = _r[0] if isinstance(_r, ShapeList) else _r
    _cut_solids.append(_r)
_final = Compound(children=_cut_solids)

export_step(_final, "/Users/softage/Documents/stls/5may/Lego.step")
export_stl(_final, "/Users/softage/Documents/stls/5may/Lego.stl")
