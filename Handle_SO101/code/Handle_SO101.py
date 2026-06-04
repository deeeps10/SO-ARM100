# Units: mm throughout.

from build123d import *
from build123d.topology import Compound
import math
try:
    from ocp_vscode import show
    _has_ocp = True
except ImportError:
    _has_ocp = False

# ---- Boolean operation helpers ----
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse as BFuse, BRepAlgoAPI_Cut as BCut

def fuse_solids(solid1, solid2):
    """Fuse two solids with fuzzy tolerance. Falls back to Compound if they do not intersect."""
    # v16.99: guard against None inputs (first feature skipped/failed → part.part is None)
    if solid1 is None: return solid2
    if solid2 is None: return solid1
    from OCP.TopAbs import TopAbs_SOLID
    try:
        fuse_op = BFuse(solid1.wrapped, solid2.wrapped)
        fuse_op.SetFuzzyValue(0.01)
        fuse_op.Build()
        result_shape = fuse_op.Shape()
        if not result_shape.IsNull():
            from OCP.TopAbs import TopAbs_COMPOUND
            from OCP.TopExp import TopExp_Explorer
            from OCP.TopoDS import TopoDS
            if result_shape.ShapeType() == TopAbs_SOLID:
                return Solid(result_shape)
            if result_shape.ShapeType() == TopAbs_COMPOUND:
                from OCP.TopAbs import TopAbs_SOLID as _TS
                _exp = TopExp_Explorer(result_shape, _TS)
                _solids = []
                while _exp.More():
                    _solids.append(Solid(TopoDS.Solid_s(_exp.Current())))
                    _exp.Next()
                if len(_solids) == 1:
                    return _solids[0]
                if len(_solids) > 1:
                    return Compound(_solids)
    except:
        pass
    # Non-touching bodies: OCC returns a Compound — accumulate explicitly.
    existing = list(solid1.solids()) if isinstance(solid1, Compound) else [solid1]
    new_s = list(solid2.solids()) if isinstance(solid2, Compound) else [solid2]
    return Compound(existing + new_s)

def cut_solids(shape, tool):
    """Cut tool from shape. When tool extends beyond shape (through-all cuts), BCut returns a
    Compound with the cut body AND the tool remainder. _extract_cut_result discards solids
    outside the original bounding box so stray geometry is not returned."""
    if shape is None: return None
    if tool is None: return shape

    def _extract_cut_result(raw_shape, original_solid):
        from OCP.TopAbs import TopAbs_SOLID
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS
        if raw_shape.IsNull(): return original_solid
        exp = TopExp_Explorer(raw_shape, TopAbs_SOLID)
        solids = []
        while exp.More():
            s = Solid(TopoDS.Solid_s(exp.Current()))
            if not s.wrapped.IsNull() and len(list(s.faces())) > 0:
                solids.append(s)
            exp.Next()
        if not solids: return original_solid
        if len(solids) == 1: return solids[0]
        # Multiple solids: tool extended beyond the shape. Keep only solids inside original bbox.
        try:
            obb = original_solid.bounding_box()
            tol = 0.5
            kept = []
            for s in solids:
                try:
                    sbb = s.bounding_box()
                    if (sbb.min.X >= obb.min.X - tol and sbb.max.X <= obb.max.X + tol and
                        sbb.min.Y >= obb.min.Y - tol and sbb.max.Y <= obb.max.Y + tol and
                        sbb.min.Z >= obb.min.Z - tol and sbb.max.Z <= obb.max.Z + tol):
                        kept.append(s)
                except:
                    kept.append(s)
            if len(kept) == 1: return kept[0]
            if len(kept) > 1: return Compound(kept)
        except:
            pass
        return max(solids, key=lambda s: len(list(s.faces())))

    try:
        if isinstance(shape, Compound):
            result_solids = []
            for solid in shape.solids():
                try:
                    sbb = solid.bounding_box()
                    tbb = tool.bounding_box()
                    overlap = (
                        not (sbb.max.X < tbb.min.X or sbb.min.X > tbb.max.X) and
                        not (sbb.max.Y < tbb.min.Y or sbb.min.Y > tbb.max.Y) and
                        not (sbb.max.Z < tbb.min.Z or sbb.min.Z > tbb.max.Z)
                    )
                    if overlap:
                        cut_op = BCut(solid.wrapped, tool.wrapped)
                        cut_op.SetFuzzyValue(0.01)
                        cut_op.Build()
                        result_solids.append(_extract_cut_result(cut_op.Shape(), solid))
                    else:
                        result_solids.append(solid)
                except:
                    result_solids.append(solid)
            return result_solids[0] if len(result_solids) == 1 else Compound(result_solids)
        else:
            sbb = shape.bounding_box()
            tbb = tool.bounding_box()
            overlap = (
                not (sbb.max.X < tbb.min.X or sbb.min.X > tbb.max.X) and
                not (sbb.max.Y < tbb.min.Y or sbb.min.Y > tbb.max.Y) and
                not (sbb.max.Z < tbb.min.Z or sbb.min.Z > tbb.max.Z)
            )
            if overlap:
                cut_op = BCut(shape.wrapped, tool.wrapped)
                cut_op.SetFuzzyValue(0.01)
                cut_op.Build()
                return _extract_cut_result(cut_op.Shape(), shape)
            return shape
    except:
        return shape

# All dimensions below are raw numbers.

# 'Sketch17': 6 segments → Line/RadiusArc profile
_inclined_plane_5 = Plane(
    origin=Vector(0.0, 0.0, 4.6648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch17_5:
    with BuildLine():
        Line((-1937.1933, 639.2202), (-1937.1933, 757.8439))
        Line((-1937.1933, 757.8439), (-1899.1933, 744.172))
        Line((-1899.1933, 744.172), (-1842.1598, 744.172))
        Line((-1842.1598, 744.172), (-1840.7806, 651.5157))
        Line((-1840.7806, 651.5157), (-1899.3517, 651.5157))
        Line((-1899.3517, 651.5157), (-1937.1933, 639.2202))
    _inc_edges_sk_Sketch17_5 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch17_5 = Wire.combine(_inc_edges_sk_Sketch17_5)[0]
_wire_sk_Sketch17_5 = _wire_sk_Sketch17_5.moved(_inclined_plane_5.location)
_mkf_sk_Sketch17_5 = BRepBuilderAPI_MakeFace(_inclined_plane_5.wrapped, _wire_sk_Sketch17_5.wrapped, True)
_face_sk_Sketch17_5 = Face(_mkf_sk_Sketch17_5.Face())

# 'Sketch18': 4 segments → Line/RadiusArc profile
_inclined_plane_6 = Plane(
    origin=Vector(0.0, 757.8439, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_6) as sk_Sketch18_6:
    with BuildLine():
        Line((1937.1933, -175.8474), (1937.1933, -225.7252))
        Line((1937.1933, -225.7252), (1892.2832, -225.7252))
        Line((1892.2832, -225.7252), (1899.3517, -217.8748))
        Line((1899.3517, -217.8748), (1937.1933, -175.8474))
    _inc_edges_sk_Sketch18_6 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch18_6 = Wire.combine(_inc_edges_sk_Sketch18_6)[0]
_wire_sk_Sketch18_6 = _wire_sk_Sketch18_6.moved(_inclined_plane_6.location)
_mkf_sk_Sketch18_6 = BRepBuilderAPI_MakeFace(_inclined_plane_6.wrapped, _wire_sk_Sketch18_6.wrapped, True)
_face_sk_Sketch18_6 = Face(_mkf_sk_Sketch18_6.Face())

# 'Sketch14': circle on inclined plane
_inclined_plane_7 = Plane(
    origin=Vector(247.8924, 0.0015, 762.9207),
    x_dir=Vector(0.951055, 0.0, -0.309022),
    z_dir=Vector(0.309022, 2e-06, 0.951055),
)
with BuildSketch(_inclined_plane_7) as sk_Sketch14_7:
    with Locations((1757.7565, 697.9938)):
        Circle(radius=19.8437)

# 'Sketch16': circle on inclined plane
_inclined_plane_8 = Plane(
    origin=Vector(247.8924, 0.0015, 762.9207),
    x_dir=Vector(0.951055, 0.0, -0.309022),
    z_dir=Vector(0.309022, 2e-06, 0.951055),
)
with BuildSketch(_inclined_plane_8) as sk_Sketch16_8:
    with Locations((1757.7926, 697.8418)):
        Circle(radius=11.0001)

# 'Sketch2': 21 segments → Line/RadiusArc profile
_inclined_plane_1 = Plane(
    origin=Vector(0.0, 697.8439, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch2:
    with BuildLine():
        RadiusArc((-1890.6963, -284.9606), (-1886.8015, -260.3336), -58.9484)
        RadiusArc((-1886.8015, -260.3336), (-1889.6068, -238.0268), -129.2376)
        Line((-1889.6068, -238.0268), (-1895.2502, -212.3425))
        RadiusArc((-1895.2502, -212.3425), (-1899.6933, -165.4934), 244.8885)
        Line((-1899.6933, -165.4934), (-1899.6933, -5.705))
        Line((-1899.6933, -5.705), (-2149.6933, -4.6648))
        RadiusArc((-2149.6933, -4.6648), (-2343.7364, -304.152), 1529.4202)
        RadiusArc((-2343.7364, -304.152), (-2487.375, -713.3146), -671.7533)
        RadiusArc((-2487.375, -713.3146), (-2368.4669, -830.8228), -980.6429)
        RadiusArc((-2368.4669, -830.8228), (-2311.4565, -868.2256), -369.6802)
        RadiusArc((-2311.4565, -868.2256), (-2254.3243, -885.6553), -157.4952)
        RadiusArc((-2254.3243, -885.6553), (-2219.5753, -881.621), -90.824)
        RadiusArc((-2219.5753, -881.621), (-2172.8307, -848.5625), -101.4503)
        RadiusArc((-2172.8307, -848.5625), (-2100.0507, -680.1218), -406.369)
        RadiusArc((-2100.0507, -680.1218), (-2061.7863, -526.865), -9890.173)
        RadiusArc((-2061.7863, -526.865), (-2036.6479, -439.8532), 1271.5675)
        RadiusArc((-2036.6479, -439.8532), (-1990.3105, -343.175), 328.9503)
        RadiusArc((-1990.3105, -343.175), (-1967.8313, -319.1711), 138.2313)
        RadiusArc((-1967.8313, -319.1711), (-1899.6674, -299.1212), 86.3011)
        Line((-1899.6674, -299.1212), (-1890.6963, -299.1212))
        Line((-1890.6963, -299.1212), (-1890.6963, -284.9606))
    _inc_edges_sk_Sketch2 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch2 = Wire.combine(_inc_edges_sk_Sketch2)[0]
_wire_sk_Sketch2 = _wire_sk_Sketch2.moved(_inclined_plane_1.location)
_mkf_sk_Sketch2 = BRepBuilderAPI_MakeFace(_inclined_plane_1.wrapped, _wire_sk_Sketch2.wrapped, True)
_face_sk_Sketch2 = Face(_mkf_sk_Sketch2.Face())

# Path wire for Sweep2
with BuildLine() as _bl_Sweep2:
    ThreePointArc((2487.375, 572.8439, 713.3146), (2430.4296, 572.8439, 774.6072), (2368.4669, 572.8439, 830.8228))
    ThreePointArc((2368.4669, 572.8439, 830.8228), (2340.8259, 572.8439, 850.8414), (2311.4565, 572.8439, 868.2256))
    ThreePointArc((2311.4565, 572.8439, 868.2256), (2283.7243, 572.8439, 879.6737), (2254.3243, 572.8439, 885.6553))
    ThreePointArc((2254.3243, 572.8439, 885.6553), (2236.7538, 572.8439, 885.327), (2219.5753, 572.8439, 881.621))
    ThreePointArc((2219.5753, 572.8439, 881.621), (2193.8226, 572.8439, 868.4577), (2172.8307, 572.8439, 848.5625))
    ThreePointArc((2172.8307, 572.8439, 848.5625), (2126.8091, 572.8439, 768.5038), (2100.0507, 572.8439, 680.1218))
    ThreePointArc((2100.0507, 572.8439, 680.1218), (2080.6125, 572.8439, 603.5698), (2061.7863, 572.8439, 526.865))
    ThreePointArc((2061.7863, 572.8439, 526.865), (2049.9921, 572.8439, 483.1352), (2036.6479, 572.8439, 439.8532))
    ThreePointArc((2036.6479, 572.8439, 439.8532), (2017.4443, 572.8439, 389.6136), (1990.3105, 572.8439, 343.175))
    ThreePointArc((1990.3105, 572.8439, 343.175), (1979.7873, 572.8439, 330.5022), (1967.8313, 572.8439, 319.1711))
    ThreePointArc((1967.8313, 572.8439, 319.1711), (1935.9084, 572.8439, 301.8059), (1899.6674, 572.8439, 299.1212))
    Line((1899.6674, 572.8439, 299.1212), (1872.711, 572.8439, 299.1212))
path_Sweep2 = _bl_Sweep2.wires()[0]

# Profile plane from sketch (origin at sketch_origin)
_plane_Sweep2 = Plane(origin=Vector(2487.375, 572.8439, 713.3146), x_dir=Vector(-0.76097693, 0.0, -0.64877894), z_dir=Vector(-0.64877894, 0.0, 0.76097693))

# 'Sketch7': 2 segments -> sweep profile
with BuildSketch(_plane_Sweep2) as sk_Sketch7_1:
    with BuildLine():
        # Arc split: sweep=218.29deg >= 150 — emitted as two half-arcs
        RadiusArc((60.4107, 0.0), (-26.0242, 2.4608), -53.0584)
        RadiusArc((-26.0242, 2.4608), (-0.0, -80.0), -53.0584)
        # Spline from EllipticalArc3D, 57 adaptive samples
        Spline((-0.0, -80.0), (0.028, -77.7579), (0.1034, -75.5178), (0.226, -73.2813), (0.3958, -71.0503), (0.6126, -68.8264), (0.8762, -66.6114), (1.1865, -64.4071), (1.5433, -62.215), (1.9461, -60.0371), (2.3948, -57.8749), (2.8889, -55.7302), (3.4282, -53.6045), (4.012, -51.4997), (4.6401, -49.4174), (5.3119, -47.359), (6.0269, -45.3264), (6.7845, -43.321), (7.5842, -41.3445), (8.4252, -39.3983), (9.307, -37.484), (10.2289, -35.6032), (11.1901, -33.7571), (12.1899, -31.9474), (13.2275, -30.1754), (14.3022, -28.4425), (15.4129, -26.7501), (16.559, -25.0994), (17.7395, -23.4918), (18.9534, -21.9286), (20.1999, -20.4109), (21.4779, -18.9399), (22.7865, -17.5168), (24.1246, -16.1427), (25.4911, -14.8187), (26.8851, -13.5458), (28.3055, -12.325), (29.751, -11.1572), (31.2206, -10.0434), (32.7132, -8.9845), (34.2275, -7.9812), (35.7624, -7.0344), (37.3167, -6.1448), (38.8892, -5.313), (40.4786, -4.5398), (42.0837, -3.8257), (43.7033, -3.1713), (45.336, -2.5772), (46.9807, -2.0437), (48.6359, -1.5713), (50.3005, -1.1603), (51.9731, -0.8112), (53.6525, -0.5241), (55.3372, -0.2992), (57.026, -0.1369), (58.7176, -0.0371), (60.4107, 0.0))
    make_face()
# Path wire for Sweep3
with BuildLine() as _bl_Sweep3:
    ThreePointArc((2149.6933, 572.8439, 4.6648), (2237.9501, 572.8439, 160.0872), (2343.7364, 572.8439, 304.152))
    ThreePointArc((2343.7364, 572.8439, 304.152), (2449.4798, 572.8439, 496.824), (2487.375, 572.8439, 713.3146))
path_Sweep3 = _bl_Sweep3.wires()[0]

# Profile plane from sketch (origin at sketch_origin)
_plane_Sweep3 = Plane(origin=Vector(2487.375, 572.8439, 713.3146), x_dir=Vector(-0.99995986, 0.0, 0.00896), z_dir=Vector(0.00896, 0.0, 0.99995986))

# 'Sketch10': 5 segments -> sweep profile
with BuildSketch(_plane_Sweep3) as sk_Sketch10_2:
    with BuildLine():
        Line((45.6181, 0.0), (39.9621, 36.0924))
        Line((39.9621, 36.0924), (-0.0, 0.0))
        Line((-0.0, 0.0), (-43.8588, -47.4598))
        Line((-43.8588, -47.4598), (-0.0, -80.0))
        # Spline from EllipticalArc3D, 57 adaptive samples
        Spline((-0.0, -80.0), (0.0211, -77.7579), (0.078, -75.5178), (0.1706, -73.2813), (0.2988, -71.0503), (0.4625, -68.8264), (0.6616, -66.6114), (0.896, -64.4071), (1.1654, -62.215), (1.4696, -60.0371), (1.8084, -57.8749), (2.1815, -55.7302), (2.5887, -53.6045), (3.0296, -51.4997), (3.5039, -49.4174), (4.0112, -47.359), (4.5511, -45.3264), (5.1232, -43.321), (5.727, -41.3445), (6.3621, -39.3983), (7.028, -37.484), (7.7242, -35.6032), (8.45, -33.7571), (9.205, -31.9474), (9.9885, -30.1754), (10.8, -28.4425), (11.6388, -26.7501), (12.5042, -25.0994), (13.3957, -23.4918), (14.3123, -21.9286), (15.2536, -20.4109), (16.2187, -18.9399), (17.2068, -17.5168), (18.2172, -16.1427), (19.2492, -14.8187), (20.3018, -13.5458), (21.3744, -12.325), (22.466, -11.1572), (23.5757, -10.0434), (24.7028, -8.9845), (25.8463, -7.9812), (27.0054, -7.0344), (28.1791, -6.1448), (29.3665, -5.313), (30.5667, -4.5398), (31.7788, -3.8257), (33.0018, -3.1713), (34.2347, -2.5772), (35.4766, -2.0437), (36.7266, -1.5713), (37.9836, -1.1603), (39.2466, -0.8112), (40.5147, -0.5241), (41.7869, -0.2992), (43.0622, -0.1369), (44.3396, -0.0371), (45.6181, 0.0))
    make_face()
# 'Sketch12': 5 segments → Line/RadiusArc profile
_inclined_plane_4 = Plane(
    origin=Vector(1899.6933, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch12_4:
    with BuildLine():
        Line((-466.5666, -27.2001), (-629.609, -137.3511))
        Line((-629.609, -137.3511), (-652.8439, 4.6648))
        RadiusArc((-652.8439, 4.6648), (-572.8439, 84.6648), -80.0)
        Line((-572.8439, 84.6648), (-459.8619, 98.5841))
        Line((-459.8619, 98.5841), (-466.5666, -27.2001))
    _inc_edges_sk_Sketch12_4 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch12_4 = Wire.combine(_inc_edges_sk_Sketch12_4)[0]
_wire_sk_Sketch12_4 = _wire_sk_Sketch12_4.moved(_inclined_plane_4.location)
_mkf_sk_Sketch12_4 = BRepBuilderAPI_MakeFace(_inclined_plane_4.wrapped, _wire_sk_Sketch12_4.wrapped, True)
_face_sk_Sketch12_4 = Face(_mkf_sk_Sketch12_4.Face())

# -- Isolation buffer: body_Extrude1 (kind=body) --
with BuildPart() as body_Extrude1:
    # -- Extrude1 --
    _face = _face_sk_Sketch2
    _vec = Vector(-0.0, -1.0, -0.0) * 125.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid)
    # Fusion depth expression: 125.000000 mm
    
    # -- Sweep2 --
    try:
        from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeFace
        from OCP.ShapeFix import ShapeFix_Solid
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_SHELL, TopAbs_WIRE, TopAbs_EDGE
        from OCP.TopoDS import TopoDS
        from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
        from OCP.BRepAdaptor import BRepAdaptor_Curve
        from OCP.gp import gp_Pln, gp_Ax3, gp_Dir, gp_Pnt
        import numpy as _np
        _profile_face = sk_Sketch7_1.sketch.faces()[0]
        _occ_wire = None
        _wire_exp = TopExp_Explorer(_profile_face.wrapped, TopAbs_WIRE)
        if _wire_exp.More():
            _occ_wire = TopoDS.Wire_s(_wire_exp.Current())
        _path_wire = path_Sweep2
        def _make_pipe_solid(_wire, reverse=False):
            _w = _wire.Reversed() if reverse else _wire
            _pipe = BRepOffsetAPI_MakePipeShell(_path_wire.wrapped)
            _pipe.Add(_w)
            _pipe.Build()
            if not _pipe.IsDone(): return None
            if _pipe.MakeSolid(): return Solid(_pipe.Shape())
            return None
        def _fit_plane_cap(wire):
            _pts = []
            _ee = TopExp_Explorer(wire, TopAbs_EDGE)
            while _ee.More():
                _c = BRepAdaptor_Curve(TopoDS.Edge_s(_ee.Current()))
                _t = (_c.FirstParameter() + _c.LastParameter()) / 2.0
                _p = _c.Value(_t)
                _pts.append([_p.X(), _p.Y(), _p.Z()])
                _ee.Next()
            if len(_pts) < 3: return None
            _pts = _np.array(_pts)
            _cen = _pts.mean(axis=0)
            _, _, _vh = _np.linalg.svd(_pts - _cen)
            _n = _vh[-1]; _n /= _np.linalg.norm(_n)
            _x = _pts[0] - _cen; _x -= _np.dot(_x, _n) * _n
            if _np.linalg.norm(_x) < 1e-6: _x = _pts[1] - _cen; _x -= _np.dot(_x, _n) * _n
            _x /= _np.linalg.norm(_x)
            _ax = gp_Ax3(gp_Pnt(*_cen.tolist()), gp_Dir(*_n.tolist()), gp_Dir(*_x.tolist()))
            _mf = BRepBuilderAPI_MakeFace(gp_Pln(_ax), wire)
            return _mf.Face() if _mf.IsDone() else None
        # Attempt A: wire as-is
        _solid = _make_pipe_solid(_occ_wire) if _occ_wire else None
        if _solid is None and _occ_wire:
            # Attempt B: reversed wire
            _solid = _make_pipe_solid(_occ_wire, reverse=True)
        if _solid is None:
            # Attempt C: Solid.sweep() + cap free boundary wires
            _sweep_shell = Solid.sweep(sk_Sketch7_1.sketch.faces()[0], path_Sweep2)
            _sa = ShapeAnalysis_FreeBounds(_sweep_shell.wrapped)
            _cw_exp = TopExp_Explorer(_sa.GetClosedWires(), TopAbs_WIRE)
            _caps = []
            while _cw_exp.More():
                _w = TopoDS.Wire_s(_cw_exp.Current())
                _mf = BRepBuilderAPI_MakeFace(_w, True)
                if _mf.IsDone(): _caps.append(_mf.Face())
                else:
                    _fc = _fit_plane_cap(_w)
                    if _fc is not None: _caps.append(_fc)
                _cw_exp.Next()
            _sew = BRepBuilderAPI_Sewing(0.1)
            _sew.Add(_sweep_shell.wrapped)
            for _fc in _caps: _sew.Add(_fc)
            _sew.Perform()
            _mk = BRepBuilderAPI_MakeSolid()
            _exp = TopExp_Explorer(_sew.SewedShape(), TopAbs_SHELL)
            while _exp.More(): _mk.Add(TopoDS.Shell_s(_exp.Current())); _exp.Next()
            _mk.Build()
            if _mk.IsDone():
                _fix = ShapeFix_Solid(_mk.Solid())
                _fix.Perform()
                _solid = Solid(_fix.Shape())
            else:
                _solid = _sweep_shell
                print('WARNING: Sweep2 sweep — all solid attempts failed, result is Shell')
        add(_solid, mode=Mode.SUBTRACT)
    except Exception as _sweep_err:
        print('WARNING: Sweep2 sweep failed:', _sweep_err)
    
    # -- Sweep3 --
    try:
        from OCP.BRepOffsetAPI import BRepOffsetAPI_MakePipeShell
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeFace
        from OCP.ShapeFix import ShapeFix_Solid
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_SHELL, TopAbs_WIRE, TopAbs_EDGE
        from OCP.TopoDS import TopoDS
        from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
        from OCP.BRepAdaptor import BRepAdaptor_Curve
        from OCP.gp import gp_Pln, gp_Ax3, gp_Dir, gp_Pnt
        import numpy as _np
        _profile_face = sk_Sketch10_2.sketch.faces()[0]
        _occ_wire = None
        _wire_exp = TopExp_Explorer(_profile_face.wrapped, TopAbs_WIRE)
        if _wire_exp.More():
            _occ_wire = TopoDS.Wire_s(_wire_exp.Current())
        _path_wire = path_Sweep3
        def _make_pipe_solid(_wire, reverse=False):
            _w = _wire.Reversed() if reverse else _wire
            _pipe = BRepOffsetAPI_MakePipeShell(_path_wire.wrapped)
            _pipe.Add(_w)
            _pipe.Build()
            if not _pipe.IsDone(): return None
            if _pipe.MakeSolid(): return Solid(_pipe.Shape())
            return None
        def _fit_plane_cap(wire):
            _pts = []
            _ee = TopExp_Explorer(wire, TopAbs_EDGE)
            while _ee.More():
                _c = BRepAdaptor_Curve(TopoDS.Edge_s(_ee.Current()))
                _t = (_c.FirstParameter() + _c.LastParameter()) / 2.0
                _p = _c.Value(_t)
                _pts.append([_p.X(), _p.Y(), _p.Z()])
                _ee.Next()
            if len(_pts) < 3: return None
            _pts = _np.array(_pts)
            _cen = _pts.mean(axis=0)
            _, _, _vh = _np.linalg.svd(_pts - _cen)
            _n = _vh[-1]; _n /= _np.linalg.norm(_n)
            _x = _pts[0] - _cen; _x -= _np.dot(_x, _n) * _n
            if _np.linalg.norm(_x) < 1e-6: _x = _pts[1] - _cen; _x -= _np.dot(_x, _n) * _n
            _x /= _np.linalg.norm(_x)
            _ax = gp_Ax3(gp_Pnt(*_cen.tolist()), gp_Dir(*_n.tolist()), gp_Dir(*_x.tolist()))
            _mf = BRepBuilderAPI_MakeFace(gp_Pln(_ax), wire)
            return _mf.Face() if _mf.IsDone() else None
        # Attempt A: wire as-is
        _solid = _make_pipe_solid(_occ_wire) if _occ_wire else None
        if _solid is None and _occ_wire:
            # Attempt B: reversed wire
            _solid = _make_pipe_solid(_occ_wire, reverse=True)
        if _solid is None:
            # Attempt C: Solid.sweep() + cap free boundary wires
            _sweep_shell = Solid.sweep(sk_Sketch10_2.sketch.faces()[0], path_Sweep3)
            _sa = ShapeAnalysis_FreeBounds(_sweep_shell.wrapped)
            _cw_exp = TopExp_Explorer(_sa.GetClosedWires(), TopAbs_WIRE)
            _caps = []
            while _cw_exp.More():
                _w = TopoDS.Wire_s(_cw_exp.Current())
                _mf = BRepBuilderAPI_MakeFace(_w, True)
                if _mf.IsDone(): _caps.append(_mf.Face())
                else:
                    _fc = _fit_plane_cap(_w)
                    if _fc is not None: _caps.append(_fc)
                _cw_exp.Next()
            _sew = BRepBuilderAPI_Sewing(0.1)
            _sew.Add(_sweep_shell.wrapped)
            for _fc in _caps: _sew.Add(_fc)
            _sew.Perform()
            _mk = BRepBuilderAPI_MakeSolid()
            _exp = TopExp_Explorer(_sew.SewedShape(), TopAbs_SHELL)
            while _exp.More(): _mk.Add(TopoDS.Shell_s(_exp.Current())); _exp.Next()
            _mk.Build()
            if _mk.IsDone():
                _fix = ShapeFix_Solid(_mk.Solid())
                _fix.Perform()
                _solid = Solid(_fix.Shape())
            else:
                _solid = _sweep_shell
                print('WARNING: Sweep3 sweep — all solid attempts failed, result is Shell')
        add(_solid, mode=Mode.SUBTRACT)
    except Exception as _sweep_err:
        print('WARNING: Sweep3 sweep failed:', _sweep_err)
    
    # -- Extrude2 --
    _face = _face_sk_Sketch12_4
    _vec = Vector(-1.0, 0.0, 0.0) * -350.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -350.000000 mm
    

# -- Build --
with BuildPart() as part:
    # -- Add Extrude1 (separate body) --
    add(body_Extrude1.part)
    
    # -- Mirror1 (bodies: Body2) --
    _mirror_plane_Plane6_1498 = Plane(
        origin=Vector(2186.7298, 697.8439, 445.8564),
        x_dir=Vector(1.0, 0.0, 0.0),
        z_dir=Vector(-0.0, 1.0, 0.0),
    )
    _mirrored_Body2 = mirror(body_Extrude1.part, about=_mirror_plane_Plane6_1498, mode=Mode.PRIVATE)
    add(_mirrored_Body2)
    
    # -- Extrude5 --
    _face = _face_sk_Sketch17_5
    _vec = Vector(0.0, 0.0, -1.0) * -221.0604
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -221.060408652 mm
    
    # -- Extrude6 --
    _face = _face_sk_Sketch18_6
    _vec = Vector(-0.0, 1.0, 0.0) * -118.6236
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -118.62361908 mm
    
    # -- Extrude3 --
    extrude(sk_Sketch14_7.sketch, amount=900.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: 900.000000 mm
    
    # -- Extrude4 --
    extrude(sk_Sketch16_8.sketch, amount=-430.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -430.000000 mm
    

# -- Export --
export_step(part.part, 'Handle_SO101.step')
export_stl(part.part,  'Handle_SO101.stl')
if _has_ocp: show(part)
