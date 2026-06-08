# Units: mm throughout.

from build123d import *
import math

# -- Edge selection helpers --
def get_edge_by_endpoints(solid, p1, p2, tol=0.05):
    for e in solid.edges():
        verts = e.vertices()
        if len(verts) != 2:
            continue
        pts = [(v.X, v.Y, v.Z) for v in verts]
        if (all(abs(pts[0][i]-p1[i])<tol for i in range(3)) and
            all(abs(pts[1][i]-p2[i])<tol for i in range(3))) or \
           (all(abs(pts[0][i]-p2[i])<tol for i in range(3)) and
            all(abs(pts[1][i]-p1[i])<tol for i in range(3))):
            return e
    return None

def get_vertical_edge(solid, x, y, z0, z1, tol=0.01):
    for e in solid.edges():
        verts = e.vertices()
        if len(verts) != 2:
            continue
        xs = [v.X for v in verts]
        ys = [v.Y for v in verts]
        zs = sorted([v.Z for v in verts])
        if (abs(xs[0]-x)<tol and abs(xs[1]-x)<tol and
            abs(ys[0]-y)<tol and abs(ys[1]-y)<tol and
            abs(zs[0]-z0)<tol and abs(zs[1]-z1)<tol):
            return e
    return None

# All dimensions below are raw numbers.

# 'Sketch4': 11 segments → Line/RadiusArc profile
_inclined_plane_1 = Plane(
    origin=Vector(0.0, 0.0, 50.0002),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch4:
    with BuildLine():
        Line((418.0, 99.1428), (438.0, 99.1428))
        RadiusArc((438.0, 99.1428), (511.2275, 160.588), -74.3572)
        RadiusArc((511.2275, 160.588), (475.1786, 237.8952), -74.357)
        RadiusArc((475.1786, 237.8952), (450.912, 246.7275), -74.356)
        Line((450.912, 246.7275), (438.0, 247.8571))
        Line((438.0, 247.8571), (418.0, 247.8571))
        Line((418.0, 247.8571), (418.0, 347.0))
        Line((418.0, 347.0), (0.0, 347.0))
        Line((0.0, 347.0), (0.0, 0.0))
        Line((0.0, 0.0), (418.0, 0.0))
        Line((418.0, 0.0), (418.0, 99.1428))
    _inc_edges_sk_Sketch4 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch4 = Wire.combine(_inc_edges_sk_Sketch4)[0]
_wire_sk_Sketch4 = _wire_sk_Sketch4.moved(_inclined_plane_1.location)
_mkf_sk_Sketch4 = BRepBuilderAPI_MakeFace(_inclined_plane_1.wrapped, _wire_sk_Sketch4.wrapped, True)
_face_sk_Sketch4 = Face(_mkf_sk_Sketch4.Face())

# 'Sketch5': 12 segments → Line/RadiusArc profile
_inclined_plane_2 = Plane(
    origin=Vector(0.0, 0.0, 50.0002),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_2) as sk_Sketch5_2:
    with BuildLine():
        Line((50.0, 50.0), (50.0, 81.0))
        Line((50.0, 81.0), (31.0, 81.0))
        Line((31.0, 81.0), (31.0, 266.0))
        Line((31.0, 266.0), (50.0, 266.0))
        Line((50.0, 266.0), (50.0, 297.0))
        Line((50.0, 297.0), (368.0, 297.0))
        Line((368.0, 297.0), (368.0, 243.5))
        Line((368.0, 243.5), (380.0, 243.5))
        Line((380.0, 243.5), (380.0, 103.5))
        Line((380.0, 103.5), (368.0, 103.5))
        Line((368.0, 103.5), (368.0, 50.0))
        Line((368.0, 50.0), (50.0, 50.0))
    _inc_edges_sk_Sketch5_2 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch5_2 = Wire.combine(_inc_edges_sk_Sketch5_2)[0]
_wire_sk_Sketch5_2 = _wire_sk_Sketch5_2.moved(_inclined_plane_2.location)
_mkf_sk_Sketch5_2 = BRepBuilderAPI_MakeFace(_inclined_plane_2.wrapped, _wire_sk_Sketch5_2.wrapped, True)
_face_sk_Sketch5_2 = Face(_mkf_sk_Sketch5_2.Face())

# 'Sketch7': 8 segments → Line/RadiusArc profile
_inclined_plane_3 = Plane(
    origin=Vector(0.0, 0.0, -1.9997),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_3) as sk_Sketch7_3:
    with BuildLine():
        RadiusArc((-404.36, 184.9229), (-433.1617, 200.2123), -33.6585)
        RadiusArc((-433.1617, 200.2123), (-473.4162, 195.0917), -80.3875)
        RadiusArc((-473.4162, 195.0917), (-482.9908, 185.909), -25.0882)
        RadiusArc((-482.9908, 185.909), (-481.6641, 158.9599), -26.4664)
        RadiusArc((-481.6641, 158.9599), (-463.1911, 148.0116), -30.9025)
        RadiusArc((-463.1911, 148.0116), (-426.4482, 147.6609), -108.4613)
        RadiusArc((-426.4482, 147.6609), (-405.8394, 159.1669), -31.9659)
        RadiusArc((-405.8394, 159.1669), (-404.36, 184.9229), -27.5107)
    _inc_edges_sk_Sketch7_3 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch7_3 = Wire.combine(_inc_edges_sk_Sketch7_3)[0]
_wire_sk_Sketch7_3 = _wire_sk_Sketch7_3.moved(_inclined_plane_3.location)
_mkf_sk_Sketch7_3 = BRepBuilderAPI_MakeFace(_inclined_plane_3.wrapped, _wire_sk_Sketch7_3.wrapped, True)
_face_sk_Sketch7_3 = Face(_mkf_sk_Sketch7_3.Face())

# 'Sketch8': 8 segments → Line/RadiusArc profile
_inclined_plane_4 = Plane(
    origin=Vector(0.0, 0.0, 8.8964),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch8_4:
    with BuildLine():
        RadiusArc((-405.8394, 159.1669), (-404.36, 184.9229), -27.5107)
        RadiusArc((-404.36, 184.9229), (-433.1617, 200.2123), -33.6585)
        RadiusArc((-433.1617, 200.2123), (-473.4162, 195.0917), -80.3875)
        RadiusArc((-473.4162, 195.0917), (-482.9908, 185.909), -25.0882)
        RadiusArc((-482.9908, 185.909), (-481.6641, 158.9599), -26.4664)
        RadiusArc((-481.6641, 158.9599), (-463.1911, 148.0116), -30.9025)
        RadiusArc((-463.1911, 148.0116), (-426.4482, 147.6609), -108.4613)
        RadiusArc((-426.4482, 147.6609), (-405.8394, 159.1669), -31.9659)
    _inc_edges_sk_Sketch8_4 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch8_4 = Wire.combine(_inc_edges_sk_Sketch8_4)[0]
_wire_sk_Sketch8_4 = _wire_sk_Sketch8_4.moved(_inclined_plane_4.location)
_mkf_sk_Sketch8_4 = BRepBuilderAPI_MakeFace(_inclined_plane_4.wrapped, _wire_sk_Sketch8_4.wrapped, True)
_face_sk_Sketch8_4 = Face(_mkf_sk_Sketch8_4.Face())

# 'Sketch10': 16 segments → Line/RadiusArc profile
_inclined_plane_5 = Plane(
    origin=Vector(0.0, 0.0, 0.0003),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch10_5:
    with BuildLine():
        RadiusArc((-450.3581, 186.0769), (-463.4343, 183.854), -42.7749)
        RadiusArc((-463.4343, 183.854), (-468.4335, 180.9616), -15.3185)
        RadiusArc((-468.4335, 180.9616), (-471.5236, 175.2575), -10.37)
        RadiusArc((-471.5236, 175.2575), (-471.0226, 169.7819), -9.7194)
        RadiusArc((-471.0226, 169.7819), (-466.1425, 164.4226), -11.6539)
        RadiusArc((-466.1425, 164.4226), (-452.6004, 160.9487), -30.3552)
        RadiusArc((-452.6004, 160.9487), (-443.968, 160.6231), -142.4426)
        RadiusArc((-443.968, 160.6231), (-430.2512, 161.6884), -81.1349)
        RadiusArc((-430.2512, 161.6884), (-420.3563, 165.5365), -23.2761)
        RadiusArc((-420.3563, 165.5365), (-416.7447, 170.3868), -9.8626)
        RadiusArc((-416.7447, 170.3868), (-416.6806, 176.0873), -10.2483)
        RadiusArc((-416.6806, 176.0873), (-418.3206, 180.0209), -8.3815)
        RadiusArc((-418.3206, 180.0209), (-421.2209, 182.3025), -10.5279)
        RadiusArc((-421.2209, 182.3025), (-428.0734, 184.9319), -25.0566)
        RadiusArc((-428.0734, 184.9319), (-434.9268, 185.9498), -48.1909)
        RadiusArc((-434.9268, 185.9498), (-450.3581, 186.0769), -120.1169)
    _inc_edges_sk_Sketch10_5 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch10_5 = Wire.combine(_inc_edges_sk_Sketch10_5)[0]
_wire_sk_Sketch10_5 = _wire_sk_Sketch10_5.moved(_inclined_plane_5.location)
_mkf_sk_Sketch10_5 = BRepBuilderAPI_MakeFace(_inclined_plane_5.wrapped, _wire_sk_Sketch10_5.wrapped, True)
_face_sk_Sketch10_5 = Face(_mkf_sk_Sketch10_5.Face())

# -- Build --
with BuildPart() as part:
    # -- Extrude1 --
    _face = _face_sk_Sketch4
    _vec = Vector(0.0, 0.0, 1.0) * -50.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid)

    # -- Extrude2 --
    _face = _face_sk_Sketch5_2
    _vec = Vector(0.0, 0.0, 1.0) * -175.0
    _solid = Solid.extrude(_face, _vec)
    _result = part.part.cut(_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

    # -- Extrude3 --
    _face = _face_sk_Sketch7_3
    _vec = Vector(0.0, 0.0, -1.0) * -10.8962
    _solid = Solid.extrude(_face, _vec)
    _result = part.part.cut(_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

    # -- Extrude4 --
    with BuildPart() as extrude4_part:
        add(_face_sk_Sketch8_4)
        extrude(amount=-24.8807, taper=math.radians(-42))
    _solid = extrude4_part.part
    _result = part.part.cut(_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

    # -- Cut: Sketch8 profile, 24.8807074mm depth, 42 degree taper --
    with BuildPart() as _sk8_cut_bp:
        add(_face_sk_Sketch8_4)
        extrude(amount=24.8807074, taper=42)
    _result = part.part.cut(_sk8_cut_bp.part)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

    # -- Extrude5 --
    _face = _face_sk_Sketch10_5
    _vec = Vector(0.0, 0.0, -1.0) * -33.7769
    _solid = Solid.extrude(_face, _vec)
    _result = part.part.fuse(_solid)
    part.part = _result[0] if isinstance(_result, ShapeList) else _result

    # -- Chamfer1: two-length chamfer, 12mm along Z, 10.804mm horizontal --
    try:
        chamfer([part.edges()[3], part.edges()[6], part.edges()[9], part.edges()[30], part.edges()[31], part.edges()[32], part.edges()[33], part.edges()[34], part.edges()[35], part.edges()[36], part.edges()[37]], length=10.804, length2=12.000)
    except Exception as _ce:
        print('WARNING: Chamfer1 failed:', _ce)

    # -- Chamfer2: two-length chamfer, 12mm along Z, 10.804mm horizontal --
    try:
        chamfer([part.edges()[46], part.edges()[47], part.edges()[48], part.edges()[49], part.edges()[50], part.edges()[51], part.edges()[52], part.edges()[53], part.edges()[54], part.edges()[55], part.edges()[56], part.edges()[57]], length=10.804, length2=12.000)
    except Exception as _ce:
        print('WARNING: Chamfer2 failed:', _ce)

    # -- Chamfer3: two edges near (50,297) corner at Z=0.0002 (mirrors to Z=100.0002) --
    try:
        _e1 = get_edge_by_endpoints(part.part, (50.0, 276.804, 0.0002), (50.0, 297.0, 0.0002))
        _e2 = get_edge_by_endpoints(part.part, (50.0, 297.0, 0.0002), (378.804, 297.0, 0.0002))
        _chamfer3_edges = [e for e in [_e1, _e2] if e is not None]
        if _chamfer3_edges:
            chamfer(_chamfer3_edges, length=10.804, length2=12.000)
        else:
            print('WARNING: Chamfer3 edges not found')
    except Exception as _ce:
        print('WARNING: Chamfer3 failed:', _ce)

# -- Mirror along XY plane at Z=50.0002 --
_mirror_plane = Plane(origin=(0.0, 0.0, 50.0002), z_dir=(0.0, 0.0, 1.0))
_mirrored = part.part.mirror(_mirror_plane)
_final = Compound(children=[part.part, _mirrored])

# -- Export --
export_step(_final, "/Users/softage/Documents/stls/5may/Gauge_0.step")
export_stl(_final, "/Users/softage/Documents/stls/5may/Gauge_0.stl")
