# # Units: mm throughout.

# from build123d import *
# from build123d import WorkplaneList  # not in __all__, needed for hole placement
# from build123d.topology import Compound
# import math
# try:
#     from ocp_vscode import show
#     _has_ocp = True
# except ImportError:
#     _has_ocp = False

import os

from build123d import *
from build123d.topology import Compound
try:
    import trimesh
except ImportError:
    trimesh = None
try:
    from ocp_vscode import show
    _has_ocp = True
except ImportError:
    _has_ocp = False

script_dir = os.path.dirname(os.path.abspath(__file__))
REFERENCE_STL = os.path.join(os.path.expanduser("~"), "Downloads", "Base_SO101.stl")
GENERATED_STL  = os.path.join(script_dir, "Base_SO1010128_generated.stl")
GENERATED_STEP = os.path.join(script_dir, "Base_SO1010128_generated.step")
# Reference STL was exported in units 10× smaller (e.g. cm) so its volume is
# 10³ = 1000× smaller than the generated file which is in mm.
REFERENCE_SCALE = 1000

# ---- Boolean operation helpers ----
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse as BFuse, BRepAlgoAPI_Cut as BCut, BRepAlgoAPI_Common as BCommon

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

def intersect_solids(solid1, solid2):
    """Intersect two solids (keep only overlapping volume). Used to clip a
    mirrored cut tool to its companion body so the subtract stays bounded.
    Returns solid1 unchanged if either input is None or BCommon fails."""
    if solid1 is None or solid2 is None:
        return solid1
    try:
        common_op = BCommon(solid1.wrapped, solid2.wrapped)
        common_op.SetFuzzyValue(0.01)
        common_op.Build()
        result = common_op.Shape()
        if result is None or result.IsNull():
            return solid1
        from OCP.TopAbs import TopAbs_SOLID
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopoDS import TopoDS
        exp = TopExp_Explorer(result, TopAbs_SOLID)
        solids = []
        while exp.More():
            solids.append(Solid(TopoDS.Solid_s(exp.Current())))
            exp.Next()
        if len(solids) == 1:
            return solids[0]
        if len(solids) > 1:
            return Compound(solids)
        return solid1
    except Exception:
        return solid1

# All dimensions below are raw numbers.

# 'Sketch3': 9 segments → Line/RadiusArc profile
_inclined_plane_1 = Plane(
    origin=Vector(0.0, 720.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch3:
    with BuildLine():
        RadiusArc((53.0497, -290.0), (95.2264, -253.2385), -116.25)
        Line((95.2264, -253.2385), (123.5, -212.8596))
        Line((123.5, -212.8596), (173.5, -141.4522))
        Line((173.5, -141.4522), (173.5, 130.0))
        RadiusArc((173.5, 130.0), (143.5, 160.0), -30.0)
        Line((143.5, 160.0), (0.0, 160.0))
        Line((0.0, 160.0), (0.0, -305.4112))
        Line((0.0, -305.4112), (23.0, -305.4112))
        Line((23.0, -305.4112), (53.0497, -290.0))
    _inc_edges_sk_Sketch3 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch3 = Wire.combine(_inc_edges_sk_Sketch3)[0]
_wire_sk_Sketch3 = _wire_sk_Sketch3.moved(_inclined_plane_1.location)
_mkf_sk_Sketch3 = BRepBuilderAPI_MakeFace(_inclined_plane_1.wrapped, _wire_sk_Sketch3.wrapped, True)
_face_sk_Sketch3 = Face(_mkf_sk_Sketch3.Face())

# 'Sketch4': 8 segments → Line/RadiusArc profile
_inclined_plane_2 = Plane(
    origin=Vector(0.0, 0.0, -160.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_2) as sk_Sketch4_2:
    with BuildLine():
        Line((-123.5, 720.0), (-96.8212, 720.0))
        Line((-96.8212, 720.0), (-96.8212, 763.353))
        Line((-96.8212, 763.353), (-263.5635, 763.353))
        Line((-263.5635, 763.353), (-263.5635, 645.9608))
        Line((-263.5635, 645.9608), (-173.5, 645.9608))
        Line((-173.5, 645.9608), (-173.5, 687.0821))
        RadiusArc((-173.5, 687.0821), (-161.3978, 711.1584), 29.9999)
        RadiusArc((-161.3978, 711.1584), (-123.5, 720.0), 73.2759)
    _inc_edges_sk_Sketch4_2 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch4_2 = Wire.combine(_inc_edges_sk_Sketch4_2)[0]
_wire_sk_Sketch4_2 = _wire_sk_Sketch4_2.moved(_inclined_plane_2.location)
_mkf_sk_Sketch4_2 = BRepBuilderAPI_MakeFace(_inclined_plane_2.wrapped, _wire_sk_Sketch4_2.wrapped, True)
_face_sk_Sketch4_2 = Face(_mkf_sk_Sketch4_2.Face())

# 'Sketch5': 7 segments → Line/RadiusArc profile
_inclined_plane_3 = Plane(
    origin=Vector(0.0, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_3) as sk_Sketch5_3:
    with BuildLine():
        Line((-655.6629, -160.0), (-695.0, -160.0))
        RadiusArc((-695.0, -160.0), (-720.0, -135.0), 25.0)
        Line((-720.0, -135.0), (-720.0, -64.8593))
        Line((-720.0, -64.8593), (-818.387, -64.8593))
        Line((-818.387, -64.8593), (-818.387, -219.7413))
        Line((-818.387, -219.7413), (-655.6629, -219.7413))
        Line((-655.6629, -219.7413), (-655.6629, -160.0))
    _inc_edges_sk_Sketch5_3 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch5_3 = Wire.combine(_inc_edges_sk_Sketch5_3)[0]
_wire_sk_Sketch5_3 = _wire_sk_Sketch5_3.moved(_inclined_plane_3.location)
_mkf_sk_Sketch5_3 = BRepBuilderAPI_MakeFace(_inclined_plane_3.wrapped, _wire_sk_Sketch5_3.wrapped, True)
_face_sk_Sketch5_3 = Face(_mkf_sk_Sketch5_3.Face())

# 'Sketch6': 10 segments → Line/RadiusArc profile
_inclined_plane_4 = Plane(
    origin=Vector(0.0, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch6_4:
    with BuildLine():
        Line((-586.4615, -159.9177), (-586.4615, -183.1774))
        Line((-586.4615, -183.1774), (-352.0, -183.1774))
        Line((-352.0, -183.1774), (-352.0, 305.4112))
        Line((-352.0, 305.4112), (-573.0, 305.4112))
        Line((-573.0, 305.4112), (-641.0, 305.4112))
        Line((-641.0, 305.4112), (-620.0, 284.4112))
        Line((-620.0, 284.4112), (-620.0, 100.0))
        Line((-620.0, 100.0), (-573.0, 100.0))
        Line((-573.0, 100.0), (-573.0, -159.9177))
        Line((-573.0, -159.9177), (-586.4615, -159.9177))
    _inc_edges_sk_Sketch6_4 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch6_4 = Wire.combine(_inc_edges_sk_Sketch6_4)[0]
_wire_sk_Sketch6_4 = _wire_sk_Sketch6_4.moved(_inclined_plane_4.location)
_mkf_sk_Sketch6_4 = BRepBuilderAPI_MakeFace(_inclined_plane_4.wrapped, _wire_sk_Sketch6_4.wrapped, True)
_face_sk_Sketch6_4 = Face(_mkf_sk_Sketch6_4.Face())

# 'Sketch7': 4 segments → Line/RadiusArc profile
_inclined_plane_5 = Plane(
    origin=Vector(0.0, 631.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch7_5:
    with BuildLine():
        Line((-0.0, -398.7349), (-0.0, -100.0))
        Line((-0.0, -100.0), (-70.0, -100.0))
        Line((-70.0, -100.0), (-70.0, -398.7349))
        Line((-70.0, -398.7349), (-0.0, -398.7349))
    _inc_edges_sk_Sketch7_5 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch7_5 = Wire.combine(_inc_edges_sk_Sketch7_5)[0]
_wire_sk_Sketch7_5 = _wire_sk_Sketch7_5.moved(_inclined_plane_5.location)
_mkf_sk_Sketch7_5 = BRepBuilderAPI_MakeFace(_inclined_plane_5.wrapped, _wire_sk_Sketch7_5.wrapped, True)
_face_sk_Sketch7_5 = Face(_mkf_sk_Sketch7_5.Face())

# 'Sketch8': 5 segments → Line/RadiusArc profile
_inclined_plane_6 = Plane(
    origin=Vector(0.0, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_6) as sk_Sketch8_6:
    with BuildLine():
        Line((-573.0, -135.0), (-560.9081, -135.0))
        Line((-560.9081, -135.0), (-560.9081, -160.0))
        Line((-560.9081, -160.0), (-588.0, -160.0))
        RadiusArc((-588.0, -160.0), (-573.0, -145.0), -15.0)
        Line((-573.0, -145.0), (-573.0, -135.0))
    _inc_edges_sk_Sketch8_6 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch8_6 = Wire.combine(_inc_edges_sk_Sketch8_6)[0]
_wire_sk_Sketch8_6 = _wire_sk_Sketch8_6.moved(_inclined_plane_6.location)
_mkf_sk_Sketch8_6 = BRepBuilderAPI_MakeFace(_inclined_plane_6.wrapped, _wire_sk_Sketch8_6.wrapped, True)
_face_sk_Sketch8_6 = Face(_mkf_sk_Sketch8_6.Face())

# 'Sketch9': 6 segments → Line/RadiusArc profile
_inclined_plane_7 = Plane(
    origin=Vector(0.0, 560.9081, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_7) as sk_Sketch9_7:
    with BuildLine():
        Line((146.1141, 135.0), (146.1141, 159.8859))
        Line((146.1141, 159.8859), (146.1141, 195.7432))
        Line((146.1141, 195.7432), (79.2799, 195.7432))
        Line((79.2799, 195.7432), (79.2799, 135.0))
        Line((79.2799, 135.0), (123.5, 135.0))
        Line((123.5, 135.0), (146.1141, 135.0))
    _inc_edges_sk_Sketch9_7 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch9_7 = Wire.combine(_inc_edges_sk_Sketch9_7)[0]
_wire_sk_Sketch9_7 = _wire_sk_Sketch9_7.moved(_inclined_plane_7.location)
_mkf_sk_Sketch9_7 = BRepBuilderAPI_MakeFace(_inclined_plane_7.wrapped, _wire_sk_Sketch9_7.wrapped, True)
_face_sk_Sketch9_7 = Face(_mkf_sk_Sketch9_7.Face())

# 'Sketch13': 3 segments → Line/RadiusArc profile
_inclined_plane_8 = Plane(
    origin=Vector(0.0, 327.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_8) as sk_Sketch13_8:
    with BuildLine():
        RadiusArc((146.1141, 159.8641), (123.5, 135.0), -25.2424)
        Line((123.5, 135.0), (146.1141, 135.0))
        Line((146.1141, 135.0), (146.1141, 159.8641))
    _inc_edges_sk_Sketch13_8 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch13_8 = Wire.combine(_inc_edges_sk_Sketch13_8)[0]
_wire_sk_Sketch13_8 = _wire_sk_Sketch13_8.moved(_inclined_plane_8.location)
_mkf_sk_Sketch13_8 = BRepBuilderAPI_MakeFace(_inclined_plane_8.wrapped, _wire_sk_Sketch13_8.wrapped, True)
_face_sk_Sketch13_8 = Face(_mkf_sk_Sketch13_8.Face())

# 'Sketch14': 7 segments → Line/RadiusArc profile
_inclined_plane_9 = Plane(
    origin=Vector(0.0, 370.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_9) as sk_Sketch14_9:
    with BuildLine():
        RadiusArc((223.5, 135.0), (198.5, 160.0), -25.0)
        Line((198.5, 160.0), (146.1141, 159.8641))
        Line((146.1141, 159.8641), (146.1141, -180.5633))
        Line((146.1141, -180.5633), (173.5, -141.4522))
        Line((173.5, -141.4522), (213.5, -84.3263))
        Line((213.5, -84.3263), (223.5, -70.0448))
        Line((223.5, -70.0448), (223.5, 135.0))
    _inc_edges_sk_Sketch14_9 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch14_9 = Wire.combine(_inc_edges_sk_Sketch14_9)[0]
_wire_sk_Sketch14_9 = _wire_sk_Sketch14_9.moved(_inclined_plane_9.location)
_mkf_sk_Sketch14_9 = BRepBuilderAPI_MakeFace(_inclined_plane_9.wrapped, _wire_sk_Sketch14_9.wrapped, True)
_face_sk_Sketch14_9 = Face(_mkf_sk_Sketch14_9.Face())

# Path wire for Sweep1
with BuildLine() as _bl_Sweep1:
    Line((146.1141, 380.0, -150.0), (198.0962, 380.0, -150.0))
    ThreePointArc((198.0962, 380.0, -150.0), (208.9632, 380.0, -145.7503), (213.5, 380.0, -135.0))
    Line((213.5, 380.0, -135.0), (213.5, 380.0, 120.4451))
path_Sweep1 = _bl_Sweep1.wires()[0]

# Profile plane from sketch (origin at sketch_origin)
_plane_Sweep1 = Plane(origin=Vector(146.1141, 0.0, -0.0), x_dir=Vector(0.0, -1.0, 0.0), z_dir=Vector(-1.0, 0.0, 0.0))

# 'Sketch15': 3 segments -> sweep profile
with BuildSketch(_plane_Sweep1) as sk_Sketch15_9:
    with BuildLine():
        Line((-370.0, -150.0), (-380.0, -150.0))
        RadiusArc((-380.0, -150.0), (-370.0, -160.0), -10.0)
        Line((-370.0, -160.0), (-370.0, -150.0))
    make_face()
# 'Sketch17': 6 segments → Line/RadiusArc profile
_inclined_plane_11 = Plane(
    origin=Vector(0.0, 370.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_11) as sk_Sketch17_11:
    with BuildLine():
        Line((173.5, 130.0), (173.5, -141.4522))
        Line((173.5, -141.4522), (213.5, -84.3263))
        Line((213.5, -84.3263), (213.5, 135.0))
        RadiusArc((213.5, 135.0), (198.0962, 150.0), -15.0053)
        Line((198.0962, 150.0), (165.8607, 150.0))
        RadiusArc((165.8607, 150.0), (173.5, 130.0), 30.0)
    _inc_edges_sk_Sketch17_11 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch17_11 = Wire.combine(_inc_edges_sk_Sketch17_11)[0]
_wire_sk_Sketch17_11 = _wire_sk_Sketch17_11.moved(_inclined_plane_11.location)
_mkf_sk_Sketch17_11 = BRepBuilderAPI_MakeFace(_inclined_plane_11.wrapped, _wire_sk_Sketch17_11.wrapped, True)
_face_sk_Sketch17_11 = Face(_mkf_sk_Sketch17_11.Face())

# 'Sketch18': 3 segments → Line/RadiusArc profile
_inclined_plane_12 = Plane(
    origin=Vector(0.0, 720.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_12) as sk_Sketch18_12:
    with BuildLine():
        Line((236.0488, -52.1233), (236.0488, -141.4522))
        Line((236.0488, -141.4522), (173.5, -141.4522))
        Line((173.5, -141.4522), (236.0488, -52.1233))
    _inc_edges_sk_Sketch18_12 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch18_12 = Wire.combine(_inc_edges_sk_Sketch18_12)[0]
_wire_sk_Sketch18_12 = _wire_sk_Sketch18_12.moved(_inclined_plane_12.location)
_mkf_sk_Sketch18_12 = BRepBuilderAPI_MakeFace(_inclined_plane_12.wrapped, _wire_sk_Sketch18_12.wrapped, True)
_face_sk_Sketch18_12 = Face(_mkf_sk_Sketch18_12.Face())

# 'Sketch19': 8 segments → Line/RadiusArc profile
_inclined_plane_13 = Plane(
    origin=Vector(0.0, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_13) as sk_Sketch19_13:
    with BuildLine():
        Line((-302.0, 100.0), (-352.0, 100.0))
        Line((-352.0, 100.0), (-352.0, -135.0))
        RadiusArc((-352.0, -135.0), (-327.0, -160.0), -25.0)
        Line((-327.0, -160.0), (-306.8015, -159.9804))
        RadiusArc((-306.8015, -159.9804), (-282.0, -135.0), -24.9602)
        Line((-282.0, -135.0), (-282.0, 84.7094))
        Line((-282.0, 84.7094), (-282.0, 100.0))
        Line((-282.0, 100.0), (-302.0, 100.0))
    _inc_edges_sk_Sketch19_13 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch19_13 = Wire.combine(_inc_edges_sk_Sketch19_13)[0]
_wire_sk_Sketch19_13 = _wire_sk_Sketch19_13.moved(_inclined_plane_13.location)
_mkf_sk_Sketch19_13 = BRepBuilderAPI_MakeFace(_inclined_plane_13.wrapped, _wire_sk_Sketch19_13.wrapped, True)
_face_sk_Sketch19_13 = Face(_mkf_sk_Sketch19_13.Face())

# 'Sketch20': 7 segments → Line/RadiusArc profile
_inclined_plane_14 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_14) as sk_Sketch20_14:
    with BuildLine():
        Line((-146.1141, -180.5633), (-92.0, -257.8463))
        Line((-92.0, -257.8463), (-92.0, -202.5973))
        Line((-92.0, -202.5973), (-95.0, -84.7094))
        Line((-95.0, -84.7094), (-95.0, 135.0))
        RadiusArc((-95.0, 135.0), (-120.0, 160.0), -25.0)
        Line((-120.0, 160.0), (-146.1141, 160.0))
        Line((-146.1141, 160.0), (-146.1141, -180.5633))
    _inc_edges_sk_Sketch20_14 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch20_14 = Wire.combine(_inc_edges_sk_Sketch20_14)[0]
_wire_sk_Sketch20_14 = _wire_sk_Sketch20_14.moved(_inclined_plane_14.location)
_mkf_sk_Sketch20_14 = BRepBuilderAPI_MakeFace(_inclined_plane_14.wrapped, _wire_sk_Sketch20_14.wrapped, True)
_face_sk_Sketch20_14 = Face(_mkf_sk_Sketch20_14.Face())

# 'Sketch21': 4 segments → Line/RadiusArc profile
_inclined_plane_15 = Plane(
    origin=Vector(0.0, 370.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_15) as sk_Sketch21_15:
    with BuildLine():
        Line((-123.5, 135.0), (-146.1141, 135.0))
        Line((-146.1141, 135.0), (-146.1141, -180.5633))
        Line((-146.1141, -180.5633), (-123.5, -212.8596))
        Line((-123.5, -212.8596), (-123.5, 135.0))
    _inc_edges_sk_Sketch21_15 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch21_15 = Wire.combine(_inc_edges_sk_Sketch21_15)[0]
_wire_sk_Sketch21_15 = _wire_sk_Sketch21_15.moved(_inclined_plane_15.location)
_mkf_sk_Sketch21_15 = BRepBuilderAPI_MakeFace(_inclined_plane_15.wrapped, _wire_sk_Sketch21_15.wrapped, True)
_face_sk_Sketch21_15 = Face(_mkf_sk_Sketch21_15.Face())

# 'Sketch22': 6 segments → Line/RadiusArc profile
_inclined_plane_16 = Plane(
    origin=Vector(0.0, 302.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_16) as sk_Sketch22_16:
    with BuildLine():
        Line((123.5, -100.0), (0.0, -100.0))
        Line((0.0, -100.0), (0.0, -150.0))
        Line((0.0, -150.0), (92.0, -150.0))
        Line((92.0, -150.0), (92.0, -236.9249))
        Line((92.0, -236.9249), (123.5, -191.9383))
        Line((123.5, -191.9383), (123.5, -100.0))
    _inc_edges_sk_Sketch22_16 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch22_16 = Wire.combine(_inc_edges_sk_Sketch22_16)[0]
_wire_sk_Sketch22_16 = _wire_sk_Sketch22_16.moved(_inclined_plane_16.location)
_mkf_sk_Sketch22_16 = BRepBuilderAPI_MakeFace(_inclined_plane_16.wrapped, _wire_sk_Sketch22_16.wrapped, True)
_face_sk_Sketch22_16 = Face(_mkf_sk_Sketch22_16.Face())

# 'Sketch24': 3 segments → Line/RadiusArc profile
_inclined_plane_17 = Plane(
    origin=Vector(0.0, 620.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_17) as sk_Sketch24_17:
    with BuildLine():
        Line((-123.5, -200.8596), (-128.442, -205.8017))
        Line((-128.442, -205.8017), (-123.5, -212.8596))
        Line((-123.5, -212.8596), (-123.5, -200.8596))
    _inc_edges_sk_Sketch24_17 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch24_17 = Wire.combine(_inc_edges_sk_Sketch24_17)[0]
_wire_sk_Sketch24_17 = _wire_sk_Sketch24_17.moved(_inclined_plane_17.location)
_mkf_sk_Sketch24_17 = BRepBuilderAPI_MakeFace(_inclined_plane_17.wrapped, _wire_sk_Sketch24_17.wrapped, True)
_face_sk_Sketch24_17 = Face(_mkf_sk_Sketch24_17.Face())

# 'Sketch23': 10 segments → Line/RadiusArc profile
_inclined_plane_18 = Plane(
    origin=Vector(0.0, 302.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_18) as sk_Sketch23_18:
    with BuildLine():
        Line((123.5, -200.8596), (123.5, -191.9383))
        Line((123.5, -191.9383), (123.5, -100.0))
        Line((123.5, -100.0), (0.0, -100.0))
        Line((0.0, -100.0), (0.0, -150.0))
        Line((0.0, -150.0), (92.0, -150.0))
        Line((92.0, -150.0), (91.1412, -236.9219))
        Line((91.1412, -236.9219), (90.8943, -261.9135))
        Line((90.8943, -261.9135), (125.971, -249.5753))
        Line((125.971, -249.5753), (128.442, -205.8017))
        Line((128.442, -205.8017), (123.5, -200.8596))
    _inc_edges_sk_Sketch23_18 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch23_18 = Wire.combine(_inc_edges_sk_Sketch23_18)[0]
_wire_sk_Sketch23_18 = _wire_sk_Sketch23_18.moved(_inclined_plane_18.location)
_mkf_sk_Sketch23_18 = BRepBuilderAPI_MakeFace(_inclined_plane_18.wrapped, _wire_sk_Sketch23_18.wrapped, True)
_face_sk_Sketch23_18 = Face(_mkf_sk_Sketch23_18.Face())

# 'Sketch25': 4 segments → Line/RadiusArc profile
_inclined_plane_19 = Plane(
    origin=Vector(210.2176, 256.6282, 147.196),
    x_dir=Vector(0.573576, 0.0, -0.819152),
    z_dir=Vector(0.579228, 0.707107, 0.40558),
)
with BuildSketch(_inclined_plane_19) as sk_Sketch25_19:
    with BuildLine():
        Line((-86.3898, 64.1654), (-189.013, 64.1654))
        Line((-189.013, 64.1654), (-200.9352, 47.1948))
        Line((-200.9352, 47.1948), (-94.9115, 47.1948))
        Line((-94.9115, 47.1948), (-86.3898, 64.1654))
    _inc_edges_sk_Sketch25_19 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch25_19 = Wire.combine(_inc_edges_sk_Sketch25_19)[0]
_wire_sk_Sketch25_19 = _wire_sk_Sketch25_19.moved(_inclined_plane_19.location)
_mkf_sk_Sketch25_19 = BRepBuilderAPI_MakeFace(_inclined_plane_19.wrapped, _wire_sk_Sketch25_19.wrapped, True)
_face_sk_Sketch25_19 = Face(_mkf_sk_Sketch25_19.Face())

# 'Sketch26': 5 segments → Line/RadiusArc profile
_inclined_plane_20 = Plane(
    origin=Vector(0.0, 314.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_20) as sk_Sketch26_20:
    with BuildLine():
        Line((-123.5, -200.8596), (-123.5, -200.3094))
        Line((-123.5, -200.3094), (-123.5, -191.9383))
        Line((-123.5, -191.9383), (-133.3298, -198.8212))
        Line((-133.3298, -198.8212), (-128.442, -205.8017))
        Line((-128.442, -205.8017), (-123.5, -200.8596))
    _inc_edges_sk_Sketch26_20 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch26_20 = Wire.combine(_inc_edges_sk_Sketch26_20)[0]
_wire_sk_Sketch26_20 = _wire_sk_Sketch26_20.moved(_inclined_plane_20.location)
_mkf_sk_Sketch26_20 = BRepBuilderAPI_MakeFace(_inclined_plane_20.wrapped, _wire_sk_Sketch26_20.wrapped, True)
_face_sk_Sketch26_20 = Face(_mkf_sk_Sketch26_20.Face())

# 'Sketch27': 5 segments → Line/RadiusArc profile
_inclined_plane_21 = Plane(
    origin=Vector(188.8362, 0.0, 24.8331),
    x_dir=Vector(0.130384, 0.0, -0.991464),
    z_dir=Vector(0.991464, -0.0, 0.130384),
)
with BuildSketch(_inclined_plane_21) as sk_Sketch27_21:
    with BuildLine():
        Line((-162.1945, 380.0), (-117.6232, 380.0))
        Line((-117.6232, 380.0), (-117.6232, 596.0))
        Line((-117.6232, 596.0), (-145.5195, 596.0))
        Line((-145.5195, 596.0), (-162.1945, 581.0))
        Line((-162.1945, 581.0), (-162.1945, 380.0))
    _inc_edges_sk_Sketch27_21 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch27_21 = Wire.combine(_inc_edges_sk_Sketch27_21)[0]
_wire_sk_Sketch27_21 = _wire_sk_Sketch27_21.moved(_inclined_plane_21.location)
_mkf_sk_Sketch27_21 = BRepBuilderAPI_MakeFace(_inclined_plane_21.wrapped, _wire_sk_Sketch27_21.wrapped, True)
_face_sk_Sketch27_21 = Face(_mkf_sk_Sketch27_21.Face())

# 'Sketch28': 3 segments → Line/RadiusArc profile
_inclined_plane_22 = Plane(
    origin=Vector(0.0, 720.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_22) as sk_Sketch28_22:
    with BuildLine():
        RadiusArc((38.8909, -38.8909), (0.0, 54.7559), -54.8064)
        Line((0.0, 54.7559), (0.0, -77.7817))
        Line((0.0, -77.7817), (38.8909, -38.8909))
    _inc_edges_sk_Sketch28_22 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch28_22 = Wire.combine(_inc_edges_sk_Sketch28_22)[0]
_wire_sk_Sketch28_22 = _wire_sk_Sketch28_22.moved(_inclined_plane_22.location)
_mkf_sk_Sketch28_22 = BRepBuilderAPI_MakeFace(_inclined_plane_22.wrapped, _wire_sk_Sketch28_22.wrapped, True)
_face_sk_Sketch28_22 = Face(_mkf_sk_Sketch28_22.Face())

# 'Sketch29': 3 segments → Line/RadiusArc profile
_inclined_plane_23 = Plane(
    origin=Vector(0.0, 642.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_23) as sk_Sketch29_23:
    with BuildLine():
        Line((105.0, -187.5852), (119.2894, -172.9933))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((119.2894, -172.9933), (105.0, -139.0), -20.0)
        RadiusArc((105.0, -139.0), (90.7105, -172.9933), -20.0)
        Line((90.7105, -172.9933), (105.0, -187.5852))
    _inc_edges_sk_Sketch29_23 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch29_23 = Wire.combine(_inc_edges_sk_Sketch29_23)[0]
_wire_sk_Sketch29_23 = _wire_sk_Sketch29_23.moved(_inclined_plane_23.location)
_mkf_sk_Sketch29_23 = BRepBuilderAPI_MakeFace(_inclined_plane_23.wrapped, _wire_sk_Sketch29_23.wrapped, True)
_face_sk_Sketch29_23 = Face(_mkf_sk_Sketch29_23.Face())

# 'Sketch30': 3 segments → Line/RadiusArc profile
_inclined_plane_24 = Plane(
    origin=Vector(0.0, 642.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_24) as sk_Sketch30_24:
    with BuildLine():
        Line((112.1447, -165.9966), (105.0, -173.2926))
        Line((105.0, -173.2926), (97.8553, -165.9966))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((97.8553, -165.9966), (105.0, -149.0), 10.0)
        RadiusArc((105.0, -149.0), (112.1447, -165.9966), 10.0)
    _inc_edges_sk_Sketch30_24 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch30_24 = Wire.combine(_inc_edges_sk_Sketch30_24)[0]
_wire_sk_Sketch30_24 = _wire_sk_Sketch30_24.moved(_inclined_plane_24.location)
_mkf_sk_Sketch30_24 = BRepBuilderAPI_MakeFace(_inclined_plane_24.wrapped, _wire_sk_Sketch30_24.wrapped, True)
_face_sk_Sketch30_24 = Face(_mkf_sk_Sketch30_24.Face())

# 'Sketch31': 3 segments → Line/RadiusArc profile
_inclined_plane_25 = Plane(
    origin=Vector(0.0, 282.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_25) as sk_Sketch31_25:
    with BuildLine():
        Line((-95.3553, -130.9966), (-102.5, -138.2926))
        Line((-102.5, -138.2926), (-109.6447, -130.9966))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-109.6447, -130.9966), (-102.5, -114.0), 10.0)
        RadiusArc((-102.5, -114.0), (-95.3553, -130.9966), 10.0)
    _inc_edges_sk_Sketch31_25 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch31_25 = Wire.combine(_inc_edges_sk_Sketch31_25)[0]
_wire_sk_Sketch31_25 = _wire_sk_Sketch31_25.moved(_inclined_plane_25.location)
_mkf_sk_Sketch31_25 = BRepBuilderAPI_MakeFace(_inclined_plane_25.wrapped, _wire_sk_Sketch31_25.wrapped, True)
_face_sk_Sketch31_25 = Face(_mkf_sk_Sketch31_25.Face())

# 'Sketch32': 3 segments → Line/RadiusArc profile
_inclined_plane_26 = Plane(
    origin=Vector(0.0, 282.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_26) as sk_Sketch32_26:
    with BuildLine():
        Line((-92.0, -202.5973), (-95.0, -84.7094))
        RadiusArc((-95.0, -84.7094), (-130.6762, -152.3919), -40.0)
        Line((-130.6762, -152.3919), (-92.0, -202.5973))
    _inc_edges_sk_Sketch32_26 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch32_26 = Wire.combine(_inc_edges_sk_Sketch32_26)[0]
_wire_sk_Sketch32_26 = _wire_sk_Sketch32_26.moved(_inclined_plane_26.location)
_mkf_sk_Sketch32_26 = BRepBuilderAPI_MakeFace(_inclined_plane_26.wrapped, _wire_sk_Sketch32_26.wrapped, True)
_face_sk_Sketch32_26 = Face(_mkf_sk_Sketch32_26.Face())

# 'Sketch33': 3 segments → Line/RadiusArc profile
_inclined_plane_27 = Plane(
    origin=Vector(123.5, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_27) as sk_Sketch33_27:
    with BuildLine():
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-486.3585, -39.7301), (-481.0001, -52.4776), -7.5)
        RadiusArc((-481.0001, -52.4776), (-475.6414, -39.7301), -7.5)
        Line((-475.6414, -39.7301), (-481.0, -34.2581))
        Line((-481.0, -34.2581), (-486.3585, -39.7301))
    _inc_edges_sk_Sketch33_27 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch33_27 = Wire.combine(_inc_edges_sk_Sketch33_27)[0]
_wire_sk_Sketch33_27 = _wire_sk_Sketch33_27.moved(_inclined_plane_27.location)
_mkf_sk_Sketch33_27 = BRepBuilderAPI_MakeFace(_inclined_plane_27.wrapped, _wire_sk_Sketch33_27.wrapped, True)
_face_sk_Sketch33_27 = Face(_mkf_sk_Sketch33_27.Face())

# 'Sketch34': 23 segments → Line/RadiusArc profile
_inclined_plane_28 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_28) as sk_Sketch34_28:
    with BuildLine():
        Line((432.6539, 135.0), (432.6539, 6.6987))
        RadiusArc((432.6539, 6.6987), (436.0033, -5.8013), -25.0008)
        Line((436.0033, -5.8013), (551.2756, -205.4589))
        RadiusArc((551.2756, -205.4589), (554.625, -217.9589), 25.0006)
        Line((554.625, -217.9589), (554.625, -298.1181))
        RadiusArc((554.625, -298.1181), (551.2756, -310.6181), 24.9996)
        Line((551.2756, -310.6181), (327.9092, -697.5))
        RadiusArc((327.9092, -697.5), (306.2586, -710.0), 24.9997)
        Line((306.2586, -710.0), (249.2713, -710.0))
        RadiusArc((249.2713, -710.0), (227.6207, -697.5), 25.0)
        Line((227.6207, -697.5), (108.3494, -490.916))
        RadiusArc((108.3494, -490.916), (105.9057, -484.7426), 19.3964)
        RadiusArc((105.9057, -484.7426), (105.0, -468.416), 57.69)
        Line((105.0, -468.416), (105.0, -279.7777))
        RadiusArc((105.0, -279.7777), (92.0002, -257.8461), -25.0213)
        Line((92.0002, -257.8461), (92.0, -202.5973))
        Line((92.0, -202.5973), (130.6762, -152.3919))
        RadiusArc((130.6762, -152.3919), (95.0, -84.7094), -40.0)
        Line((95.0, -84.7094), (95.0, 135.0))
        RadiusArc((95.0, 135.0), (120.0, 160.0), 25.1347)
        Line((120.0, 160.0), (198.5, 160.0))
        Line((198.5, 160.0), (407.6539, 160.0))
        RadiusArc((407.6539, 160.0), (432.6539, 135.0), 24.9999)
    _inc_edges_sk_Sketch34_28 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch34_28 = Wire.combine(_inc_edges_sk_Sketch34_28)[0]
_wire_sk_Sketch34_28 = _wire_sk_Sketch34_28.moved(_inclined_plane_28.location)
_mkf_sk_Sketch34_28 = BRepBuilderAPI_MakeFace(_inclined_plane_28.wrapped, _wire_sk_Sketch34_28.wrapped, True)
_face_sk_Sketch34_28 = Face(_mkf_sk_Sketch34_28.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_29 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_29) as sk_Sketch40_29:
    with BuildLine():
        Line((339.782, -29.6668), (362.765, -69.4744))
        Line((362.765, -69.4744), (385.7479, -29.6668))
        Line((385.7479, -29.6668), (362.765, 10.1408))
        Line((362.765, 10.1408), (339.782, -29.6668))
    _inc_edges_sk_Sketch40_29 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_29 = Wire.combine(_inc_edges_sk_Sketch40_29)[0]
_wire_sk_Sketch40_29 = _wire_sk_Sketch40_29.moved(_inclined_plane_29.location)
_mkf_sk_Sketch40_29 = BRepBuilderAPI_MakeFace(_inclined_plane_29.wrapped, _wire_sk_Sketch40_29.wrapped, True)
_face_sk_Sketch40_29 = Face(_mkf_sk_Sketch40_29.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_30 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_30) as sk_Sketch40_30:
    with BuildLine():
        Line((237.765, -43.4936), (262.765, -86.7949))
        Line((262.765, -86.7949), (287.765, -43.4936))
        Line((287.765, -43.4936), (262.765, -0.1924))
        Line((262.765, -0.1924), (237.765, -43.4936))
    _inc_edges_sk_Sketch40_30 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_30 = Wire.combine(_inc_edges_sk_Sketch40_30)[0]
_wire_sk_Sketch40_30 = _wire_sk_Sketch40_30.moved(_inclined_plane_30.location)
_mkf_sk_Sketch40_30 = BRepBuilderAPI_MakeFace(_inclined_plane_30.wrapped, _wire_sk_Sketch40_30.wrapped, True)
_face_sk_Sketch40_30 = Face(_mkf_sk_Sketch40_30.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_31 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_31) as sk_Sketch40_31:
    with BuildLine():
        Line((182.765, -138.7564), (207.765, -182.0577))
        Line((207.765, -182.0577), (232.765, -138.7564))
        Line((232.765, -138.7564), (207.765, -95.4552))
        Line((207.765, -95.4552), (182.765, -138.7564))
    _inc_edges_sk_Sketch40_31 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_31 = Wire.combine(_inc_edges_sk_Sketch40_31)[0]
_wire_sk_Sketch40_31 = _wire_sk_Sketch40_31.moved(_inclined_plane_31.location)
_mkf_sk_Sketch40_31 = BRepBuilderAPI_MakeFace(_inclined_plane_31.wrapped, _wire_sk_Sketch40_31.wrapped, True)
_face_sk_Sketch40_31 = Face(_mkf_sk_Sketch40_31.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_32 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_32) as sk_Sketch40_32:
    with BuildLine():
        Line((127.765, -234.0192), (152.765, -277.3205))
        Line((152.765, -277.3205), (177.765, -234.0192))
        Line((177.765, -234.0192), (152.765, -190.718))
        Line((152.765, -190.718), (127.765, -234.0192))
    _inc_edges_sk_Sketch40_32 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_32 = Wire.combine(_inc_edges_sk_Sketch40_32)[0]
_wire_sk_Sketch40_32 = _wire_sk_Sketch40_32.moved(_inclined_plane_32.location)
_mkf_sk_Sketch40_32 = BRepBuilderAPI_MakeFace(_inclined_plane_32.wrapped, _wire_sk_Sketch40_32.wrapped, True)
_face_sk_Sketch40_32 = Face(_mkf_sk_Sketch40_32.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_33 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_33) as sk_Sketch40_33:
    with BuildLine():
        Line((172.765, -311.9615), (197.765, -268.6603))
        Line((197.765, -268.6603), (222.765, -311.9615))
        Line((222.765, -311.9615), (197.765, -355.2628))
        Line((197.765, -355.2628), (172.765, -311.9615))
    _inc_edges_sk_Sketch40_33 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_33 = Wire.combine(_inc_edges_sk_Sketch40_33)[0]
_wire_sk_Sketch40_33 = _wire_sk_Sketch40_33.moved(_inclined_plane_33.location)
_mkf_sk_Sketch40_33 = BRepBuilderAPI_MakeFace(_inclined_plane_33.wrapped, _wire_sk_Sketch40_33.wrapped, True)
_face_sk_Sketch40_33 = Face(_mkf_sk_Sketch40_33.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_34 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_34) as sk_Sketch40_34:
    with BuildLine():
        Line((117.765, -407.2243), (142.765, -363.923))
        Line((142.765, -363.923), (167.765, -407.2243))
        Line((167.765, -407.2243), (142.765, -450.5256))
        Line((142.765, -450.5256), (117.765, -407.2243))
    _inc_edges_sk_Sketch40_34 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_34 = Wire.combine(_inc_edges_sk_Sketch40_34)[0]
_wire_sk_Sketch40_34 = _wire_sk_Sketch40_34.moved(_inclined_plane_34.location)
_mkf_sk_Sketch40_34 = BRepBuilderAPI_MakeFace(_inclined_plane_34.wrapped, _wire_sk_Sketch40_34.wrapped, True)
_face_sk_Sketch40_34 = Face(_mkf_sk_Sketch40_34.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_35 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_35) as sk_Sketch40_35:
    with BuildLine():
        Line((162.765, -485.1666), (187.765, -441.8653))
        Line((187.765, -441.8653), (212.765, -485.1666))
        Line((212.765, -485.1666), (187.765, -528.4679))
        Line((187.765, -528.4679), (162.765, -485.1666))
    _inc_edges_sk_Sketch40_35 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_35 = Wire.combine(_inc_edges_sk_Sketch40_35)[0]
_wire_sk_Sketch40_35 = _wire_sk_Sketch40_35.moved(_inclined_plane_35.location)
_mkf_sk_Sketch40_35 = BRepBuilderAPI_MakeFace(_inclined_plane_35.wrapped, _wire_sk_Sketch40_35.wrapped, True)
_face_sk_Sketch40_35 = Face(_mkf_sk_Sketch40_35.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_36 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_36) as sk_Sketch40_36:
    with BuildLine():
        Line((207.765, -563.1089), (225.345, -593.5584))
        Line((225.345, -593.5584), (250.345, -550.2571))
        Line((250.345, -550.2571), (232.765, -519.8076))
        Line((232.765, -519.8076), (207.765, -563.1089))
    _inc_edges_sk_Sketch40_36 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_36 = Wire.combine(_inc_edges_sk_Sketch40_36)[0]
_wire_sk_Sketch40_36 = _wire_sk_Sketch40_36.moved(_inclined_plane_36.location)
_mkf_sk_Sketch40_36 = BRepBuilderAPI_MakeFace(_inclined_plane_36.wrapped, _wire_sk_Sketch40_36.wrapped, True)
_face_sk_Sketch40_36 = Face(_mkf_sk_Sketch40_36.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_37 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_37) as sk_Sketch40_37:
    with BuildLine():
        Line((307.765, -545.7884), (332.765, -502.4871))
        Line((332.765, -502.4871), (357.765, -545.7884))
        Line((357.765, -545.7884), (332.765, -589.0897))
        Line((332.765, -589.0897), (307.765, -545.7884))
    _inc_edges_sk_Sketch40_37 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_37 = Wire.combine(_inc_edges_sk_Sketch40_37)[0]
_wire_sk_Sketch40_37 = _wire_sk_Sketch40_37.moved(_inclined_plane_37.location)
_mkf_sk_Sketch40_37 = BRepBuilderAPI_MakeFace(_inclined_plane_37.wrapped, _wire_sk_Sketch40_37.wrapped, True)
_face_sk_Sketch40_37 = Face(_mkf_sk_Sketch40_37.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_38 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_38) as sk_Sketch40_38:
    with BuildLine():
        Line((262.765, -467.8461), (287.765, -424.5448))
        Line((287.765, -424.5448), (312.765, -467.8461))
        Line((312.765, -467.8461), (287.765, -511.1474))
        Line((287.765, -511.1474), (262.765, -467.8461))
    _inc_edges_sk_Sketch40_38 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_38 = Wire.combine(_inc_edges_sk_Sketch40_38)[0]
_wire_sk_Sketch40_38 = _wire_sk_Sketch40_38.moved(_inclined_plane_38.location)
_mkf_sk_Sketch40_38 = BRepBuilderAPI_MakeFace(_inclined_plane_38.wrapped, _wire_sk_Sketch40_38.wrapped, True)
_face_sk_Sketch40_38 = Face(_mkf_sk_Sketch40_38.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_39 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_39) as sk_Sketch40_39:
    with BuildLine():
        Line((217.765, -389.9038), (242.765, -346.6026))
        Line((242.765, -346.6026), (267.765, -389.9038))
        Line((267.765, -389.9038), (242.765, -433.2051))
        Line((242.765, -433.2051), (217.765, -389.9038))
    _inc_edges_sk_Sketch40_39 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_39 = Wire.combine(_inc_edges_sk_Sketch40_39)[0]
_wire_sk_Sketch40_39 = _wire_sk_Sketch40_39.moved(_inclined_plane_39.location)
_mkf_sk_Sketch40_39 = BRepBuilderAPI_MakeFace(_inclined_plane_39.wrapped, _wire_sk_Sketch40_39.wrapped, True)
_face_sk_Sketch40_39 = Face(_mkf_sk_Sketch40_39.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_40 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_40) as sk_Sketch40_40:
    with BuildLine():
        Line((272.765, -294.641), (297.765, -251.3397))
        Line((297.765, -251.3397), (322.765, -294.641))
        Line((322.765, -294.641), (297.765, -337.9423))
        Line((297.765, -337.9423), (272.765, -294.641))
    _inc_edges_sk_Sketch40_40 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_40 = Wire.combine(_inc_edges_sk_Sketch40_40)[0]
_wire_sk_Sketch40_40 = _wire_sk_Sketch40_40.moved(_inclined_plane_40.location)
_mkf_sk_Sketch40_40 = BRepBuilderAPI_MakeFace(_inclined_plane_40.wrapped, _wire_sk_Sketch40_40.wrapped, True)
_face_sk_Sketch40_40 = Face(_mkf_sk_Sketch40_40.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_41 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_41) as sk_Sketch40_41:
    with BuildLine():
        Line((227.765, -216.6987), (252.765, -173.3975))
        Line((252.765, -173.3975), (277.765, -216.6987))
        Line((277.765, -216.6987), (252.765, -260.0))
        Line((252.765, -260.0), (227.765, -216.6987))
    _inc_edges_sk_Sketch40_41 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_41 = Wire.combine(_inc_edges_sk_Sketch40_41)[0]
_wire_sk_Sketch40_41 = _wire_sk_Sketch40_41.moved(_inclined_plane_41.location)
_mkf_sk_Sketch40_41 = BRepBuilderAPI_MakeFace(_inclined_plane_41.wrapped, _wire_sk_Sketch40_41.wrapped, True)
_face_sk_Sketch40_41 = Face(_mkf_sk_Sketch40_41.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_42 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_42) as sk_Sketch40_42:
    with BuildLine():
        Line((317.765, -372.5833), (342.765, -329.282))
        Line((342.765, -329.282), (367.765, -372.5833))
        Line((367.765, -372.5833), (342.765, -415.8846))
        Line((342.765, -415.8846), (317.765, -372.5833))
    _inc_edges_sk_Sketch40_42 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_42 = Wire.combine(_inc_edges_sk_Sketch40_42)[0]
_wire_sk_Sketch40_42 = _wire_sk_Sketch40_42.moved(_inclined_plane_42.location)
_mkf_sk_Sketch40_42 = BRepBuilderAPI_MakeFace(_inclined_plane_42.wrapped, _wire_sk_Sketch40_42.wrapped, True)
_face_sk_Sketch40_42 = Face(_mkf_sk_Sketch40_42.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_43 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_43) as sk_Sketch40_43:
    with BuildLine():
        Line((387.765, -493.8269), (412.765, -450.5256))
        Line((412.765, -450.5256), (387.765, -407.2243))
        Line((387.765, -407.2243), (362.765, -450.5256))
        Line((362.765, -450.5256), (387.765, -493.8269))
    _inc_edges_sk_Sketch40_43 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_43 = Wire.combine(_inc_edges_sk_Sketch40_43)[0]
_wire_sk_Sketch40_43 = _wire_sk_Sketch40_43.moved(_inclined_plane_43.location)
_mkf_sk_Sketch40_43 = BRepBuilderAPI_MakeFace(_inclined_plane_43.wrapped, _wire_sk_Sketch40_43.wrapped, True)
_face_sk_Sketch40_43 = Face(_mkf_sk_Sketch40_43.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_44 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_44) as sk_Sketch40_44:
    with BuildLine():
        Line((417.765, -355.2628), (442.765, -311.9615))
        Line((442.765, -311.9615), (467.765, -355.2628))
        Line((467.765, -355.2628), (442.765, -398.5641))
        Line((442.765, -398.5641), (417.765, -355.2628))
    _inc_edges_sk_Sketch40_44 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_44 = Wire.combine(_inc_edges_sk_Sketch40_44)[0]
_wire_sk_Sketch40_44 = _wire_sk_Sketch40_44.moved(_inclined_plane_44.location)
_mkf_sk_Sketch40_44 = BRepBuilderAPI_MakeFace(_inclined_plane_44.wrapped, _wire_sk_Sketch40_44.wrapped, True)
_face_sk_Sketch40_44 = Face(_mkf_sk_Sketch40_44.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_45 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_45) as sk_Sketch40_45:
    with BuildLine():
        Line((372.765, -277.3205), (397.765, -234.0192))
        Line((397.765, -234.0192), (422.765, -277.3205))
        Line((422.765, -277.3205), (397.765, -320.6218))
        Line((397.765, -320.6218), (372.765, -277.3205))
    _inc_edges_sk_Sketch40_45 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_45 = Wire.combine(_inc_edges_sk_Sketch40_45)[0]
_wire_sk_Sketch40_45 = _wire_sk_Sketch40_45.moved(_inclined_plane_45.location)
_mkf_sk_Sketch40_45 = BRepBuilderAPI_MakeFace(_inclined_plane_45.wrapped, _wire_sk_Sketch40_45.wrapped, True)
_face_sk_Sketch40_45 = Face(_mkf_sk_Sketch40_45.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_46 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_46) as sk_Sketch40_46:
    with BuildLine():
        Line((327.765, -199.3782), (352.765, -242.6795))
        Line((352.765, -242.6795), (377.765, -199.3782))
        Line((377.765, -199.3782), (352.765, -156.077))
        Line((352.765, -156.077), (327.765, -199.3782))
    _inc_edges_sk_Sketch40_46 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_46 = Wire.combine(_inc_edges_sk_Sketch40_46)[0]
_wire_sk_Sketch40_46 = _wire_sk_Sketch40_46.moved(_inclined_plane_46.location)
_mkf_sk_Sketch40_46 = BRepBuilderAPI_MakeFace(_inclined_plane_46.wrapped, _wire_sk_Sketch40_46.wrapped, True)
_face_sk_Sketch40_46 = Face(_mkf_sk_Sketch40_46.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_47 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_47) as sk_Sketch40_47:
    with BuildLine():
        Line((282.765, -121.4359), (307.765, -78.1347))
        Line((307.765, -78.1347), (332.765, -121.4359))
        Line((332.765, -121.4359), (307.765, -164.7372))
        Line((307.765, -164.7372), (282.765, -121.4359))
    _inc_edges_sk_Sketch40_47 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_47 = Wire.combine(_inc_edges_sk_Sketch40_47)[0]
_wire_sk_Sketch40_47 = _wire_sk_Sketch40_47.moved(_inclined_plane_47.location)
_mkf_sk_Sketch40_47 = BRepBuilderAPI_MakeFace(_inclined_plane_47.wrapped, _wire_sk_Sketch40_47.wrapped, True)
_face_sk_Sketch40_47 = Face(_mkf_sk_Sketch40_47.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_48 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_48) as sk_Sketch40_48:
    with BuildLine():
        Line((382.765, -104.1154), (407.765, -60.8142))
        Line((407.765, -60.8142), (432.765, -104.1154))
        Line((432.765, -104.1154), (407.765, -147.4167))
        Line((407.765, -147.4167), (382.765, -104.1154))
    _inc_edges_sk_Sketch40_48 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_48 = Wire.combine(_inc_edges_sk_Sketch40_48)[0]
_wire_sk_Sketch40_48 = _wire_sk_Sketch40_48.moved(_inclined_plane_48.location)
_mkf_sk_Sketch40_48 = BRepBuilderAPI_MakeFace(_inclined_plane_48.wrapped, _wire_sk_Sketch40_48.wrapped, True)
_face_sk_Sketch40_48 = Face(_mkf_sk_Sketch40_48.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_49 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_49) as sk_Sketch40_49:
    with BuildLine():
        Line((427.765, -182.0577), (452.765, -138.7564))
        Line((452.765, -138.7564), (477.765, -182.0577))
        Line((477.765, -182.0577), (452.765, -225.359))
        Line((452.765, -225.359), (427.765, -182.0577))
    _inc_edges_sk_Sketch40_49 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_49 = Wire.combine(_inc_edges_sk_Sketch40_49)[0]
_wire_sk_Sketch40_49 = _wire_sk_Sketch40_49.moved(_inclined_plane_49.location)
_mkf_sk_Sketch40_49 = BRepBuilderAPI_MakeFace(_inclined_plane_49.wrapped, _wire_sk_Sketch40_49.wrapped, True)
_face_sk_Sketch40_49 = Face(_mkf_sk_Sketch40_49.Face())

# 'Sketch40': 4 segments → Line/RadiusArc profile
_inclined_plane_50 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_50) as sk_Sketch40_50:
    with BuildLine():
        Line((472.765, -260.0), (497.765, -216.6987))
        Line((497.765, -216.6987), (522.765, -260.0))
        Line((522.765, -260.0), (497.765, -303.3013))
        Line((497.765, -303.3013), (472.765, -260.0))
    _inc_edges_sk_Sketch40_50 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_50 = Wire.combine(_inc_edges_sk_Sketch40_50)[0]
_wire_sk_Sketch40_50 = _wire_sk_Sketch40_50.moved(_inclined_plane_50.location)
_mkf_sk_Sketch40_50 = BRepBuilderAPI_MakeFace(_inclined_plane_50.wrapped, _wire_sk_Sketch40_50.wrapped, True)
_face_sk_Sketch40_50 = Face(_mkf_sk_Sketch40_50.Face())

# 'Sketch40': 3 segments → Line/RadiusArc profile
_inclined_plane_51 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_51) as sk_Sketch40_51:
    with BuildLine():
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((335.3618, 57.5084), (317.5, 100.0), -25.0)
        RadiusArc((317.5, 100.0), (299.6382, 57.5084), -25.0)
        Line((299.6382, 57.5084), (317.5, 39.2685))
        Line((317.5, 39.2685), (335.3618, 57.5084))
    _inc_edges_sk_Sketch40_51 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_51 = Wire.combine(_inc_edges_sk_Sketch40_51)[0]
_wire_sk_Sketch40_51 = _wire_sk_Sketch40_51.moved(_inclined_plane_51.location)
_mkf_sk_Sketch40_51 = BRepBuilderAPI_MakeFace(_inclined_plane_51.wrapped, _wire_sk_Sketch40_51.wrapped, True)
_face_sk_Sketch40_51 = Face(_mkf_sk_Sketch40_51.Face())

# 'Sketch40': 3 segments → Line/RadiusArc profile
_inclined_plane_52 = Plane(
    origin=Vector(0.0, 175.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_52) as sk_Sketch40_52:
    with BuildLine():
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((295.6268, -640.2415), (277.765, -597.7499), -25.0)
        RadiusArc((277.765, -597.7499), (259.9032, -640.2415), -25.0)
        Line((259.9032, -640.2415), (277.765, -658.4814))
        Line((277.765, -658.4814), (295.6268, -640.2415))
    _inc_edges_sk_Sketch40_52 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch40_52 = Wire.combine(_inc_edges_sk_Sketch40_52)[0]
_wire_sk_Sketch40_52 = _wire_sk_Sketch40_52.moved(_inclined_plane_52.location)
_mkf_sk_Sketch40_52 = BRepBuilderAPI_MakeFace(_inclined_plane_52.wrapped, _wire_sk_Sketch40_52.wrapped, True)
_face_sk_Sketch40_52 = Face(_mkf_sk_Sketch40_52.Face())

# 'Sketch42': 3 segments → Line/RadiusArc profile
_inclined_plane_53 = Plane(
    origin=Vector(0.0, 152.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_53) as sk_Sketch42_53:
    with BuildLine():
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((335.3618, 57.5084), (317.5, 100.0), -25.0)
        RadiusArc((317.5, 100.0), (299.6382, 57.5084), -25.0)
        Line((299.6382, 57.5084), (317.5, 39.2685))
        Line((317.5, 39.2685), (335.3618, 57.5084))
    _inc_edges_sk_Sketch42_53 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch42_53 = Wire.combine(_inc_edges_sk_Sketch42_53)[0]
_wire_sk_Sketch42_53 = _wire_sk_Sketch42_53.moved(_inclined_plane_53.location)
_mkf_sk_Sketch42_53 = BRepBuilderAPI_MakeFace(_inclined_plane_53.wrapped, _wire_sk_Sketch42_53.wrapped, True)
_face_sk_Sketch42_53 = Face(_mkf_sk_Sketch42_53.Face())

_solid_sk_Sketch42_53 = extrude(_face_sk_Sketch42_53, amount=23.0, dir=Vector(-0.0, 1.0, 0.0), taper=-45.0).solid()

# 'Sketch45': 12 segments → Line/RadiusArc profile
_inclined_plane_54 = Plane(
    origin=Vector(0.0, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_54) as sk_Sketch45_54:
    with BuildLine():
        Line((-86.6777, -152.6777), (-81.5, -156.6506))
        Line((-81.5, -156.6506), (-75.4705, -159.1481))
        Line((-75.4705, -159.1481), (-71.4892, -159.7548))
        Line((-71.4892, -159.7548), (-69.0, -160.0))
        Line((-69.0, -160.0), (-24.0, -160.0))
        Line((-24.0, -160.0), (-24.0, 84.7094))
        Line((-24.0, 84.7094), (-94.0, 84.7094))
        Line((-94.0, 84.7094), (-94.0, -135.0))
        Line((-94.0, -135.0), (-93.8796, -137.4504))
        Line((-93.8796, -137.4504), (-93.1481, -141.4705))
        Line((-93.1481, -141.4705), (-90.6506, -147.5))
        Line((-90.6506, -147.5), (-86.6777, -152.6777))
    _inc_edges_sk_Sketch45_54 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch45_54 = Wire.combine(_inc_edges_sk_Sketch45_54)[0]
_wire_sk_Sketch45_54 = _wire_sk_Sketch45_54.moved(_inclined_plane_54.location)
_mkf_sk_Sketch45_54 = BRepBuilderAPI_MakeFace(_inclined_plane_54.wrapped, _wire_sk_Sketch45_54.wrapped, True)
_face_sk_Sketch45_54 = Face(_mkf_sk_Sketch45_54.Face())

# 'Sketch48': 3 segments → Line/RadiusArc profile
_inclined_plane_55 = Plane(
    origin=Vector(0.0, 152.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_55) as sk_Sketch48_55:
    with BuildLine():
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((295.6268, -640.2415), (277.765, -597.7499), -25.0)
        RadiusArc((277.765, -597.7499), (259.9032, -640.2415), -25.0)
        Line((259.9032, -640.2415), (277.765, -658.4814))
        Line((277.765, -658.4814), (295.6268, -640.2415))
    _inc_edges_sk_Sketch48_55 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch48_55 = Wire.combine(_inc_edges_sk_Sketch48_55)[0]
_wire_sk_Sketch48_55 = _wire_sk_Sketch48_55.moved(_inclined_plane_55.location)
_mkf_sk_Sketch48_55 = BRepBuilderAPI_MakeFace(_inclined_plane_55.wrapped, _wire_sk_Sketch48_55.wrapped, True)
_face_sk_Sketch48_55 = Face(_mkf_sk_Sketch48_55.Face())

_solid_sk_Sketch48_55 = extrude(_face_sk_Sketch48_55, amount=23.0, dir=Vector(-0.0, 1.0, 0.0), taper=-45.0).solid()

# 'Sketch57': 21 segments → Line/RadiusArc profile
_inclined_plane_56 = Plane(
    origin=Vector(0.0, 24.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_56) as sk_Sketch57_56:
    with BuildLine():
        Line((-332.5, 54.586), (-332.5, -689.5486))
        Line((-332.5, -689.5486), (-327.9092, -697.5))
        Line((-327.9092, -697.5), (-326.2544, -700.0056))
        Line((-326.2544, -700.0056), (-324.3111, -702.2947))
        Line((-324.3111, -702.2947), (-322.1074, -704.3343))
        Line((-322.1074, -704.3343), (-319.5659, -705.9321))
        Line((-319.5659, -705.9321), (-316.7073, -706.8491))
        Line((-316.7073, -706.8491), (-313.7106, -707.0278))
        Line((-313.7106, -707.0278), (-310.7633, -706.4572))
        Line((-310.7633, -706.4572), (-308.0498, -705.1729))
        Line((-308.0498, -705.1729), (-305.7401, -703.2553))
        Line((-305.7401, -703.2553), (-303.9785, -700.8244))
        Line((-303.9785, -700.8244), (-302.8755, -698.0323))
        Line((-302.8755, -698.0323), (-302.5, -695.0539))
        Line((-302.5, -695.0539), (-302.5, -626.3801))
        Line((-302.5, -626.3801), (-302.7355, -623.9638))
        Line((-302.7355, -623.9638), (-302.7355, -621.536))
        Line((-302.7355, -621.536), (-302.5, -619.1197))
        Line((-302.5, -619.1197), (-302.5, 54.586))
        Line((-302.5, 54.586), (-317.5, 39.2685))
        Line((-317.5, 39.2685), (-332.5, 54.586))
    _inc_edges_sk_Sketch57_56 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_56 = Wire.combine(_inc_edges_sk_Sketch57_56)[0]
_wire_sk_Sketch57_56 = _wire_sk_Sketch57_56.moved(_inclined_plane_56.location)
_mkf_sk_Sketch57_56 = BRepBuilderAPI_MakeFace(_inclined_plane_56.wrapped, _wire_sk_Sketch57_56.wrapped, True)
_face_sk_Sketch57_56 = Face(_mkf_sk_Sketch57_56.Face())

# 'Sketch57': 14 segments → Line/RadiusArc profile
_inclined_plane_57 = Plane(
    origin=Vector(0.0, 24.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_57) as sk_Sketch57_57:
    with BuildLine():
        Line((-143.75, 135.0), (-173.75, 135.0))
        Line((-173.75, 135.0), (-173.75, -559.4086))
        Line((-173.75, -559.4086), (-173.3411, -562.5145))
        Line((-173.3411, -562.5145), (-172.1423, -565.4086))
        Line((-172.1423, -565.4086), (-170.2353, -567.8939))
        Line((-170.2353, -567.8939), (-167.75, -569.8009))
        Line((-167.75, -569.8009), (-164.8558, -570.9997))
        Line((-164.8558, -570.9997), (-161.75, -571.4086))
        Line((-161.75, -571.4086), (-158.6442, -570.9997))
        Line((-158.6442, -570.9997), (-155.75, -569.8009))
        Line((-155.75, -569.8009), (-153.2647, -567.8939))
        Line((-153.2647, -567.8939), (-151.3577, -565.4086))
        Line((-151.3577, -565.4086), (-143.75, -552.2317))
        Line((-143.75, -552.2317), (-143.75, 135.0))
    _inc_edges_sk_Sketch57_57 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_57 = Wire.combine(_inc_edges_sk_Sketch57_57)[0]
_wire_sk_Sketch57_57 = _wire_sk_Sketch57_57.moved(_inclined_plane_57.location)
_mkf_sk_Sketch57_57 = BRepBuilderAPI_MakeFace(_inclined_plane_57.wrapped, _wire_sk_Sketch57_57.wrapped, True)
_face_sk_Sketch57_57 = Face(_mkf_sk_Sketch57_57.Face())

# 'Sketch57': 20 segments → Line/RadiusArc profile
_inclined_plane_58 = Plane(
    origin=Vector(0.0, 24.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_58) as sk_Sketch57_58:
    with BuildLine():
        Line((-253.125, -626.9774), (-253.125, -695.131))
        Line((-253.125, -695.131), (-252.7526, -698.0973))
        Line((-252.7526, -698.0973), (-251.6585, -700.8795))
        Line((-251.6585, -700.8795), (-249.9106, -703.3049))
        Line((-249.9106, -703.3049), (-247.6175, -705.223))
        Line((-247.6175, -705.223), (-244.9213, -706.5147))
        Line((-244.9213, -706.5147), (-241.9896, -707.0998))
        Line((-241.9896, -707.0998), (-239.0041, -706.9421))
        Line((-239.0041, -706.9421), (-236.1503, -706.0513))
        Line((-236.1503, -706.0513), (-233.6053, -704.4827))
        Line((-233.6053, -704.4827), (-231.3277, -702.4077))
        Line((-231.3277, -702.4077), (-229.3227, -700.0683))
        Line((-229.3227, -700.0683), (-227.6207, -697.5))
        Line((-227.6207, -697.5), (-223.125, -689.7132))
        Line((-223.125, -689.7132), (-223.125, 135.0))
        Line((-223.125, 135.0), (-253.125, 135.0))
        Line((-253.125, 135.0), (-253.125, -618.5224))
        Line((-253.125, -618.5224), (-252.8051, -621.3347))
        Line((-252.8051, -621.3347), (-252.8051, -624.1651))
        Line((-252.8051, -624.1651), (-253.125, -626.9774))
    _inc_edges_sk_Sketch57_58 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_58 = Wire.combine(_inc_edges_sk_Sketch57_58)[0]
_wire_sk_Sketch57_58 = _wire_sk_Sketch57_58.moved(_inclined_plane_58.location)
_mkf_sk_Sketch57_58 = BRepBuilderAPI_MakeFace(_inclined_plane_58.wrapped, _wire_sk_Sketch57_58.wrapped, True)
_face_sk_Sketch57_58 = Face(_mkf_sk_Sketch57_58.Face())

# 'Sketch57': 14 segments → Line/RadiusArc profile
_inclined_plane_59 = Plane(
    origin=Vector(0.0, 24.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_59) as sk_Sketch57_59:
    with BuildLine():
        Line((-411.875, 135.0), (-411.875, -552.0671))
        Line((-411.875, -552.0671), (-404.2673, -565.244))
        Line((-404.2673, -565.244), (-402.3603, -567.7293))
        Line((-402.3603, -567.7293), (-399.875, -569.6363))
        Line((-399.875, -569.6363), (-396.9808, -570.8351))
        Line((-396.9808, -570.8351), (-393.875, -571.244))
        Line((-393.875, -571.244), (-390.7692, -570.8351))
        Line((-390.7692, -570.8351), (-387.875, -569.6363))
        Line((-387.875, -569.6363), (-385.3897, -567.7293))
        Line((-385.3897, -567.7293), (-383.4827, -565.244))
        Line((-383.4827, -565.244), (-382.2839, -562.3498))
        Line((-382.2839, -562.3498), (-381.875, -559.244))
        Line((-381.875, -559.244), (-381.875, 135.0))
        Line((-381.875, 135.0), (-411.875, 135.0))
    _inc_edges_sk_Sketch57_59 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_59 = Wire.combine(_inc_edges_sk_Sketch57_59)[0]
_wire_sk_Sketch57_59 = _wire_sk_Sketch57_59.moved(_inclined_plane_59.location)
_mkf_sk_Sketch57_59 = BRepBuilderAPI_MakeFace(_inclined_plane_59.wrapped, _wire_sk_Sketch57_59.wrapped, True)
_face_sk_Sketch57_59 = Face(_mkf_sk_Sketch57_59.Face())

# 'Sketch57': 15 segments → Line/RadiusArc profile
_inclined_plane_60 = Plane(
    origin=Vector(0.0, 24.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_60) as sk_Sketch57_60:
    with BuildLine():
        Line((-461.6589, -424.8683), (-461.25, -421.7625))
        Line((-461.25, -421.7625), (-461.25, -91.0991))
        Line((-461.25, -91.0991), (-473.25, -70.3145))
        Line((-473.25, -70.3145), (-491.25, -101.4914))
        Line((-491.25, -101.4914), (-491.25, -414.5855))
        Line((-491.25, -414.5855), (-483.6423, -427.7625))
        Line((-483.6423, -427.7625), (-481.7353, -430.2477))
        Line((-481.7353, -430.2477), (-479.25, -432.1548))
        Line((-479.25, -432.1548), (-476.3558, -433.3536))
        Line((-476.3558, -433.3536), (-473.25, -433.7624))
        Line((-473.25, -433.7624), (-470.1442, -433.3536))
        Line((-470.1442, -433.3536), (-467.25, -432.1548))
        Line((-467.25, -432.1548), (-464.7647, -430.2477))
        Line((-464.7647, -430.2477), (-462.8577, -427.7625))
        Line((-462.8577, -427.7625), (-461.6589, -424.8683))
    _inc_edges_sk_Sketch57_60 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_60 = Wire.combine(_inc_edges_sk_Sketch57_60)[0]
_wire_sk_Sketch57_60 = _wire_sk_Sketch57_60.moved(_inclined_plane_60.location)
_mkf_sk_Sketch57_60 = BRepBuilderAPI_MakeFace(_inclined_plane_60.wrapped, _wire_sk_Sketch57_60.wrapped, True)
_face_sk_Sketch57_60 = Face(_mkf_sk_Sketch57_60.Face())

# 'Sketch57': 16 segments → Line/RadiusArc profile
_inclined_plane_61 = Plane(
    origin=Vector(0.0, 24.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_61) as sk_Sketch57_61:
    with BuildLine():
        Line((-542.0147, -304.2997), (-540.9776, -301.5818))
        Line((-540.9776, -301.5818), (-540.625, -298.6942))
        Line((-540.625, -298.6942), (-540.625, -214.7242))
        Line((-540.625, -214.7242), (-548.625, -200.8678))
        Line((-548.625, -200.8678), (-551.2756, -205.4589))
        Line((-551.2756, -205.4589), (-553.1173, -209.4084))
        Line((-553.1173, -209.4084), (-554.2452, -213.6177))
        Line((-554.2452, -213.6177), (-554.625, -217.9589))
        Line((-554.625, -217.9589), (-554.625, -298.1181))
        Line((-554.625, -298.1181), (-554.2452, -302.4593))
        Line((-554.2452, -302.4593), (-553.1173, -306.6686))
        Line((-553.1173, -306.6686), (-551.2756, -310.6181))
        Line((-551.2756, -310.6181), (-548.446, -309.943))
        Line((-548.446, -309.943), (-545.8619, -308.6069))
        Line((-545.8619, -308.6069), (-543.6753, -306.6882))
        Line((-543.6753, -306.6882), (-542.0147, -304.2997))
    _inc_edges_sk_Sketch57_61 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_61 = Wire.combine(_inc_edges_sk_Sketch57_61)[0]
_wire_sk_Sketch57_61 = _wire_sk_Sketch57_61.moved(_inclined_plane_61.location)
_mkf_sk_Sketch57_61 = BRepBuilderAPI_MakeFace(_inclined_plane_61.wrapped, _wire_sk_Sketch57_61.wrapped, True)
_face_sk_Sketch57_61 = Face(_mkf_sk_Sketch57_61.Face())

# 'Sketch57': 8 segments → Line/RadiusArc profile
_inclined_plane_62 = Plane(
    origin=Vector(0.0, 24.0, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_62) as sk_Sketch57_62:
    with BuildLine():
        Line((-308.0855, 98.1596), (-302.5, 95.0))
        Line((-302.5, 95.0), (-302.5, 135.0))
        Line((-302.5, 135.0), (-332.5, 135.0))
        Line((-332.5, 135.0), (-332.5, 95.0))
        Line((-332.5, 95.0), (-326.9145, 98.1596))
        Line((-326.9145, 98.1596), (-320.7086, 99.7932))
        Line((-320.7086, 99.7932), (-314.2914, 99.7932))
        Line((-314.2914, 99.7932), (-308.0855, 98.1596))
    _inc_edges_sk_Sketch57_62 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_62 = Wire.combine(_inc_edges_sk_Sketch57_62)[0]
_wire_sk_Sketch57_62 = _wire_sk_Sketch57_62.moved(_inclined_plane_62.location)
_mkf_sk_Sketch57_62 = BRepBuilderAPI_MakeFace(_inclined_plane_62.wrapped, _wire_sk_Sketch57_62.wrapped, True)
_face_sk_Sketch57_62 = Face(_mkf_sk_Sketch57_62.Face())

# 'SketchNewProfile': 6 segments → Line/RadiusArc profile
_inclined_plane_new_profile = Plane(
    origin=Vector(3.1148, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_new_profile) as sk_new_profile:
    with BuildLine():
        Line((307.0, -160.0), (249.7228, -160.0))
        RadiusArc((249.7228, -160.0), (241.7228, -152.0), 8.0)
        Line((241.7228, -152.0), (241.7228, -67.9996))
        RadiusArc((241.7228, -67.9996), (249.7228, -59.9996), 8.0)
        Line((249.7228, -59.9996), (307.0, -59.9996))
        Line((307.0, -59.9996), (307.0, -160.0))
    _inc_edges_new_profile = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_new_profile = Wire.combine(_inc_edges_new_profile)[0]
_wire_new_profile = _wire_new_profile.moved(_inclined_plane_new_profile.location)
_mkf_new_profile = BRepBuilderAPI_MakeFace(_inclined_plane_new_profile.wrapped, _wire_new_profile.wrapped, True)
_face_new_profile = Face(_mkf_new_profile.Face())

# 'SketchCutProfile': 9 segments → Line/RadiusArc profile (Z=-160 plane, cut to Z=-60)
_inclined_plane_cut_profile = Plane(
    origin=Vector(0.0, 0.0, -165.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 100.0),
)
with BuildSketch(_inclined_plane_cut_profile) as sk_cut_profile:
    with BuildLine():
        Line((-68.9426, 232.0352), (-68.9426, 255.0495))
        Line((-68.9426, 255.0495), (-81.6779, 268.1455))
        RadiusArc((-81.6779, 268.1455), (-75.9426, 282.0), 8.2459)
        Line((-75.9426, 282.0), (-61.3519, 282.0))
        Line((-61.3519, 282.0), (-40.9426, 282.0))
        RadiusArc((-40.9426, 282.0), (-35.2073, 268.1455), 8.2907)
        Line((-35.2073, 268.1455), (-47.9426, 255.0495))
        Line((-47.9426, 255.0495), (-47.9426, 232.0352))
        Line((-47.9426, 232.0352), (-68.9426, 232.0352))
    _inc_edges_cut_profile = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_cut_profile = Wire.combine(_inc_edges_cut_profile)[0]
_wire_cut_profile = _wire_cut_profile.moved(_inclined_plane_cut_profile.location)
_mkf_cut_profile = BRepBuilderAPI_MakeFace(_inclined_plane_cut_profile.wrapped, _wire_cut_profile.wrapped, True)
_face_cut_profile = Face(_mkf_cut_profile.Face())

# 'SketchCombProfile': 19 segments → Line/RadiusArc profile (Y=0 plane, extrude to Y=24)
_inclined_plane_comb_profile = Plane(
    origin=Vector(0.0, 0.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
with BuildSketch(_inclined_plane_comb_profile) as sk_comb_profile:
    with BuildLine():
        Line((-143.75, -160.0), (-143.75, -135.0))
        Line((-143.75, -135.0), (-173.75, -135.0))
        Line((-173.75, -135.0), (-173.75, -146.0))
        Line((-173.75, -146.0), (-223.125, -146.0))
        Line((-223.125, -146.0), (-223.125, -135.0))
        Line((-223.125, -135.0), (-253.125, -135.0))
        Line((-253.125, -135.0), (-253.125, -146.0))
        Line((-253.125, -146.0), (-302.5, -146.0))
        Line((-302.5, -146.0), (-302.5, -135.0))
        Line((-302.5, -135.0), (-332.5, -135.0))
        Line((-332.5, -135.0), (-332.5, -146.0))
        Line((-332.5, -146.0), (-381.875, -146.0))
        Line((-381.875, -146.0), (-381.875, -135.0))
        Line((-381.875, -135.0), (-411.875, -135.0))
        Line((-411.875, -135.0), (-411.875, -146.0))
        Line((-411.875, -146.0), (-430.1038, -146.0))
        RadiusArc((-430.1038, -146.0), (-407.6539, -160.0), -24.9999)
        Line((-407.6539, -160.0), (-198.5, -160.0))
        Line((-198.5, -160.0), (-143.75, -160.0))
    _inc_edges_comb_profile = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_comb_profile = Wire.combine(_inc_edges_comb_profile)[0]
_wire_comb_profile = _wire_comb_profile.moved(_inclined_plane_comb_profile.location)
_mkf_comb_profile = BRepBuilderAPI_MakeFace(_inclined_plane_comb_profile.wrapped, _wire_comb_profile.wrapped, True)
_face_comb_profile = Face(_mkf_comb_profile.Face())

# 'SketchRightFaceCut': 5 segments → Line/RadiusArc profile (X=554.625 plane, cut in -X)
_inclined_plane_rightface_cut = Plane(
    origin=Vector(554.625, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_rightface_cut) as sk_rightface_cut:
    with BuildLine():
        Line((25.0, -209.7198), (-63.0695, -209.7198))
        Line((-63.0695, -209.7198), (-63.0695, -135.0001))
        Line((-63.0695, -135.0001), (0.0, -135.0001))
        RadiusArc((0.0, -135.0001), (25.0, -160.0), -25.0)
        Line((25.0, -160.0), (25.0, -209.7198))
    _inc_edges_rightface_cut = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_rightface_cut = Wire.combine(_inc_edges_rightface_cut)[0]
_wire_rightface_cut = _wire_rightface_cut.moved(_inclined_plane_rightface_cut.location)
_mkf_rightface_cut = BRepBuilderAPI_MakeFace(_inclined_plane_rightface_cut.wrapped, _wire_rightface_cut.wrapped, True)
_face_rightface_cut = Face(_mkf_rightface_cut.Face())

# 'SketchCombProfileMirror': YZ-mirrored version of SketchCombProfile (X-negated, reversed winding)
_inclined_plane_comb_mirror = Plane(
    origin=Vector(0.0, 0.0, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
with BuildSketch(_inclined_plane_comb_mirror) as sk_comb_mirror:
    with BuildLine():
        Line((143.75, -160.0), (198.5, -160.0))
        Line((198.5, -160.0), (407.6539, -160.0))
        RadiusArc((407.6539, -160.0), (430.1038, -146.0), -24.9999)
        Line((430.1038, -146.0), (411.875, -146.0))
        Line((411.875, -146.0), (411.875, -135.0))
        Line((411.875, -135.0), (381.875, -135.0))
        Line((381.875, -135.0), (381.875, -146.0))
        Line((381.875, -146.0), (332.5, -146.0))
        Line((332.5, -146.0), (332.5, -135.0))
        Line((332.5, -135.0), (302.5, -135.0))
        Line((302.5, -135.0), (302.5, -146.0))
        Line((302.5, -146.0), (253.125, -146.0))
        Line((253.125, -146.0), (253.125, -135.0))
        Line((253.125, -135.0), (223.125, -135.0))
        Line((223.125, -135.0), (223.125, -146.0))
        Line((223.125, -146.0), (173.75, -146.0))
        Line((173.75, -146.0), (173.75, -135.0))
        Line((173.75, -135.0), (143.75, -135.0))
        Line((143.75, -135.0), (143.75, -160.0))
    _inc_edges_comb_mirror = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_comb_mirror = Wire.combine(_inc_edges_comb_mirror)[0]
_wire_comb_mirror = _wire_comb_mirror.moved(_inclined_plane_comb_mirror.location)
_mkf_comb_mirror = BRepBuilderAPI_MakeFace(_inclined_plane_comb_mirror.wrapped, _wire_comb_mirror.wrapped, True)
_face_comb_mirror = Face(_mkf_comb_mirror.Face())

# -- Build --
with BuildPart() as part:
    # --- FEATURE: Extrude1 ---
    # -- Extrude1 --
    _face = _face_sk_Sketch3
    _vec = Vector(-0.0, 1.0, 0.0) * -350.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid)
    # Fusion depth expression: -350.000000 mm
    
    # --- FEATURE: Extrude2 ---
    # -- Extrude2 --
    _face = _face_sk_Sketch4_2
    _vec = Vector(0.0, 0.0, -1.0) * -450.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -450.000000 mm
    
    # --- FEATURE: Extrude3 ---
    # -- Extrude3 --
    _face = _face_sk_Sketch5_3
    _vec = Vector(-1.0, 0.0, 0.0) * -200.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -200.000000 mm
    
    # --- FEATURE: Extrude4 ---
    # -- Extrude4 --
    _face = _face_sk_Sketch6_4
    _vec = Vector(-1.0, 0.0, 0.0) * -123.5
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -123.50001057 mm
    
    # --- FEATURE: Extrude5 ---
    # -- Extrude5 --
    _face = _face_sk_Sketch7_5
    _vec = Vector(-0.0, -1.0, -0.0) * 50.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 50.000000 mm
    
    # --- FEATURE: Extrude6 ---
    # -- Extrude6 --
    _face = _face_sk_Sketch8_6
    _vec = Vector(-1.0, 0.0, 0.0) * -146.1141
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -146.114110947 mm
    
    # --- FEATURE: Extrude7 ---
    # -- Extrude7 --
    _face = _face_sk_Sketch9_7
    _vec = Vector(-0.0, 1.0, 0.0) * -225.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -225.000000 mm
    
    # --- FEATURE: Extrude8 ---
    # -- Extrude8 --
    _face = _face_sk_Sketch13_8
    _vec = Vector(-0.0, 1.0, 0.0) * 279.1533
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 279.153293769 mm
    
    # --- FEATURE: Extrude9 ---
    # -- Extrude9 --
    _face = _face_sk_Sketch14_9
    _vec = Vector(-0.0, 1.0, 0.0) * -195.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -195.000000 mm
    
    # --- FEATURE: Sweep1 ---
    # -- Sweep1 --
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
        _profile_face = sk_Sketch15_9.sketch.faces()[0]
        _occ_wire = None
        _wire_exp = TopExp_Explorer(_profile_face.wrapped, TopAbs_WIRE)
        if _wire_exp.More():
            _occ_wire = TopoDS.Wire_s(_wire_exp.Current())
        _path_wire = path_Sweep1
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
            _sweep_shell = Solid.sweep(sk_Sketch15_9.sketch.faces()[0], path_Sweep1)
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
                print('WARNING: Sweep1 sweep — all solid attempts failed, result is Shell')
        # v17.95: final Shell→Solid coercion — add() rejects Shell in empty BuildPart
        from OCP.TopAbs import TopAbs_SHELL as _TS_SHELL, TopAbs_SOLID as _TS_SOLID
        if hasattr(_solid, 'wrapped') and _solid.wrapped.ShapeType() != _TS_SOLID:
            try:
                from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid as _MkSol2
                _mk2 = _MkSol2()
                _exp2 = TopExp_Explorer(_solid.wrapped, _TS_SHELL)
                while _exp2.More(): _mk2.Add(TopoDS.Shell_s(_exp2.Current())); _exp2.Next()
                _mk2.Build()
                if _mk2.IsDone(): _solid = Solid(_mk2.Shape())
            except Exception as _coerce_err:
                print('WARNING: Sweep1 Shell→Solid coercion failed:', _coerce_err)
        add(_solid, mode=Mode.ADD)
    except Exception as _sweep_err:
        print('WARNING: Sweep1 sweep failed:', _sweep_err)
    
    # --- FEATURE: Extrude10 ---
    # -- Extrude10 --
    _face = _face_sk_Sketch17_11
    _vec = Vector(-0.0, 1.0, 0.0) * 10.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 10.000000 mm
    
    # --- FEATURE: Extrude11 ---
    # -- Extrude11 --
    _face = _face_sk_Sketch18_12
    _vec = Vector(-0.0, 1.0, 0.0) * -725.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -725.000000 mm
    
    # --- FEATURE: Extrude12 ---
    # -- Extrude12 --
    _face = _face_sk_Sketch19_13
    _vec = Vector(-1.0, 0.0, 0.0) * -146.1141
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -146.114110947 mm
    
    # --- FEATURE: Extrude13 ---
    # -- Extrude13 --
    _face = _face_sk_Sketch20_14
    _vec = Vector(-0.0, -1.0, -0.0) * -131.8015
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -131.801468887 mm
    
    # --- FEATURE: Extrude14 ---
    # -- Extrude14 --
    _face = _face_sk_Sketch21_15
    _vec = Vector(-0.0, -1.0, -0.0) * 63.1985
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 63.198531113 mm
    
    # --- FEATURE: Extrude15 ---
    # -- Extrude15 --
    _face = _face_sk_Sketch22_16
    _vec = Vector(-0.0, 1.0, 0.0) * -20.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -20.000000 mm
    
    # --- FEATURE: Extrude16 ---
    # -- Extrude16 --
    _face = _face_sk_Sketch24_17
    _vec = Vector(-0.0, -1.0, -0.0) * 318.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 317.9999923706 mm
    
    # --- FEATURE: Extrude17 ---
    # -- Extrude17 --
    _face = _face_sk_Sketch23_18
    _vec = Vector(-0.0, 1.0, 0.0) * 20.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 20.000000 mm
    
    # --- FEATURE: Extrude18 ---
    # -- Extrude18 --
    _face = _face_sk_Sketch25_19
    _vec = Vector(0.579228, 0.707107, 0.40558) * 60.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 60.000000 mm
    
    # --- FEATURE: Extrude19 ---
    # -- Extrude19 --
    _face = _face_sk_Sketch26_20
    _vec = Vector(-0.0, -1.0, -0.0) * 29.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 29.000000 mm
    
    # --- FEATURE: Extrude20 ---
    # -- Extrude20 --
    _face = _face_sk_Sketch27_21
    _vec = Vector(0.991464, -0.0, 0.130384) * -23.7486
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -23.74864618 mm
    
    # --- FEATURE: Extrude21 ---
    # -- Extrude21 --
    _face = _face_sk_Sketch28_22
    _vec = Vector(-0.0, 1.0, 0.0) * -525.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -525.000000 mm
    
    # --- FEATURE: Extrude22 ---
    # -- Extrude22 --
    _face = _face_sk_Sketch29_23
    _vec = Vector(-0.0, 1.0, 0.0) * 240.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 240.000000 mm
    
    # --- FEATURE: Extrude23 ---
    # -- Extrude23 --
    _face = _face_sk_Sketch30_24
    _vec = Vector(-0.0, 1.0, 0.0) * -22.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -21.999969482 mm
    
    # --- FEATURE: Extrude24 ---
    # -- Extrude24 --
    _face = _face_sk_Sketch31_25
    _vec = Vector(-0.0, -1.0, -0.0) * -20.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -20.000000 mm
    
    # --- FEATURE: Extrude25 ---
    # -- Extrude25 --
    _face = _face_sk_Sketch32_26
    _vec = Vector(-0.0, -1.0, -0.0) * 107.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 107.000007629 mm
    
    # --- FEATURE: Extrude26 ---
    # -- Extrude26 --
    _face = _face_sk_Sketch33_27
    _vec = Vector(-1.0, 0.0, 0.0) * -50.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -50.000000 mm
    
    # --- FEATURE: Extrude27 ---
    # -- Extrude27 --
    _face = _face_sk_Sketch34_28
    _vec = Vector(-0.0, 1.0, 0.0) * -151.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -150.9999990463 mm
    
    # --- FEATURE: Extrude29 ---
    # -- Extrude29_p0 --
    _face = _face_sk_Sketch40_29
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p1 --
    _face = _face_sk_Sketch40_30
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p2 --
    _face = _face_sk_Sketch40_31
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p3 --
    _face = _face_sk_Sketch40_32
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p4 --
    _face = _face_sk_Sketch40_33
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p5 --
    _face = _face_sk_Sketch40_34
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p6 --
    _face = _face_sk_Sketch40_35
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p7 --
    _face = _face_sk_Sketch40_36
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p8 --
    _face = _face_sk_Sketch40_37
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p9 --
    _face = _face_sk_Sketch40_38
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p10 --
    _face = _face_sk_Sketch40_39
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p11 --
    _face = _face_sk_Sketch40_40
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p12 --
    _face = _face_sk_Sketch40_41
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p13 --
    _face = _face_sk_Sketch40_42
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p14 --
    _face = _face_sk_Sketch40_43
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p15 --
    _face = _face_sk_Sketch40_44
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p16 --
    _face = _face_sk_Sketch40_45
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p17 --
    _face = _face_sk_Sketch40_46
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p18 --
    _face = _face_sk_Sketch40_47
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p19 --
    _face = _face_sk_Sketch40_48
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p20 --
    _face = _face_sk_Sketch40_49
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p21 --
    _face = _face_sk_Sketch40_50
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p22 --
    _face = _face_sk_Sketch40_51
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # -- Extrude29_p23 --
    _face = _face_sk_Sketch40_52
    _vec = Vector(-0.0, 1.0, 0.0) * -900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -900.000000 mm
    
    # --- FEATURE: Extrude31 ---
    # -- Extrude31 --
    _face = _face_sk_Sketch42_53
    _solid = _solid_sk_Sketch42_53
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 23.000001907 mm
    # Fusion taper angle expression: 45 deg
    
    # --- FEATURE: Extrude33 ---
    # -- Extrude33 --
    _face = _face_sk_Sketch45_54
    _vec = Vector(-1.0, 0.0, 0.0) * -120.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -120.000000 mm
    
    # --- FEATURE: Extrude35 ---
    # -- Extrude35 --
    _face = _face_sk_Sketch48_55
    _solid = _solid_sk_Sketch48_55
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 23.000001907 mm
    # Fusion taper angle expression: 45.0 deg
    
    # --- FEATURE: Extrude41 ---
    # -- Extrude41_p0 --
    _face = _face_sk_Sketch57_56
    _vec = Vector(-0.0, -1.0, -0.0) * 24.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 24.000000954 mm
    
    # -- Extrude41_p1 --
    _face = _face_sk_Sketch57_57
    _vec = Vector(-0.0, -1.0, -0.0) * 24.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 24.000000954 mm
    
    # -- Extrude41_p2 --
    _face = _face_sk_Sketch57_58
    _vec = Vector(-0.0, -1.0, -0.0) * 24.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 24.000000954 mm
    
    # -- Extrude41_p3 --
    _face = _face_sk_Sketch57_59
    _vec = Vector(-0.0, -1.0, -0.0) * 24.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 24.000000954 mm
    
    # -- Extrude41_p4 --
    _face = _face_sk_Sketch57_60
    _vec = Vector(-0.0, -1.0, -0.0) * 24.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 24.000000954 mm
    
    # -- Extrude41_p5 --
    _face = _face_sk_Sketch57_61
    _vec = Vector(-0.0, -1.0, -0.0) * 24.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 24.000000954 mm
    
    # -- Extrude41_p6 --
    _face = _face_sk_Sketch57_62
    _vec = Vector(-0.0, -1.0, -0.0) * 24.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 24.000000954 mm

    # --- FEATURE: Fillet1 ---
    fillet(part.edges()[1092], radius=25.0)

    # --- FEATURE: Fillet2 ---
    fillet(part.edges()[73], radius=10.0)

    # --- FEATURE: Fillet3 ---
    fillet([part.edges()[175], part.edges()[266]], radius=10.0)

    # --- FEATURE: Mirror1 ---
    mirror(about=Plane.YZ)

    # --- FEATURE: ExtrudeNewProfile ---
    _vec = Vector(-1.0, 0.0, 0.0) * 123.1148
    _solid = Solid.extrude(_face_new_profile, _vec)
    add(_solid, mode=Mode.ADD)
    # Extrude from x=3.1148 till x=-120.000000 mm

    # --- FEATURE: Fillet4 ---
    fillet([part.edges()[26], part.edges()[19]], radius=8.0)

    # --- FEATURE: CutProfile ---
    _vec = Vector(0.0, 0.0, 1.0) * 110.0
    _solid = Solid.extrude(_face_cut_profile, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Cut from z=-165.0 till z=-55.0 mm (extended 5mm each side)

    # --- FEATURE: CombProfileExtrude ---
    _vec = Vector(0.0, 1.0, 0.0) * 24.0
    _solid = Solid.extrude(_face_comb_profile, _vec)
    add(_solid, mode=Mode.ADD)
    # Extrude from y=0.0 till y=24.0 mm

    # --- FEATURE: MirrorCombProfileExtrude ---
    _vec = Vector(0.0, 1.0, 0.0) * 24.0
    _solid = Solid.extrude(_face_comb_mirror, _vec)
    add(_solid, mode=Mode.ADD)
    # Mirrored comb profile extruded independently (y=0.0 till y=24.0 mm)

    # --- FEATURE: RightFaceCut ---
    _vec = Vector(-1.0, 0.0, 0.0) * 1000.0
    _solid = Solid.extrude(_face_rightface_cut, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Cut from x=554.625 in -X direction by 1000mm (reaches x=-445.375)

# -- Shape repair: stitch open shells and ensure watertight solid --
def _repair_for_export(shape):
    if shape is None:
        return shape
    from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Solid
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID
    from OCP.TopoDS import TopoDS

    raw = shape.wrapped if hasattr(shape, 'wrapped') else shape

    # Pass 1: general topology / orientation / connectivity fix
    try:
        sf = ShapeFix_Shape(raw)
        sf.SetPrecision(0.01)
        sf.SetMaxTolerance(1.0)
        sf.Perform()
        raw = sf.Shape()
        print('ShapeFix_Shape: done')
    except Exception as _e:
        print(f'ShapeFix_Shape failed: {_e}')

    # Pass 2: merge coplanar/coincident faces — eliminates the seam at the YZ
    # mirror plane where mirror(about=Plane.YZ) leaves two touching faces per
    # surface (one from each half).  Without this the tessellator creates
    # disconnected triangle patches that look like tears.
    try:
        from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
        usd = ShapeUpgrade_UnifySameDomain(raw, True, True, True)
        usd.Build()
        raw = usd.Shape()
        print('ShapeUpgrade_UnifySameDomain: done')
    except Exception as _e:
        print(f'ShapeUpgrade_UnifySameDomain failed: {_e}')

    # Pass 3: sewing — closes gaps between adjacent faces (1.0 mm tolerance)
    try:
        sew = BRepBuilderAPI_Sewing(1.0)
        sew.Add(raw)
        sew.Perform()
        raw = sew.SewedShape()
        print('BRepBuilderAPI_Sewing: done')
    except Exception as _e:
        print(f'Sewing failed: {_e}')

    # Pass 4: if result has no solid, promote shells → solid
    _exp_s = TopExp_Explorer(raw, TopAbs_SOLID)
    if not _exp_s.More():
        print('No solid found after sewing — promoting shells to solid')
        try:
            mk = BRepBuilderAPI_MakeSolid()
            _exp_sh = TopExp_Explorer(raw, TopAbs_SHELL)
            _n = 0
            while _exp_sh.More():
                mk.Add(TopoDS.Shell_s(_exp_sh.Current()))
                _exp_sh.Next()
                _n += 1
            print(f'  {_n} shell(s) found')
            if _n > 0 and mk.IsDone():
                sf2 = ShapeFix_Solid(mk.Solid())
                sf2.Perform()
                raw = sf2.Shape()
                print('  ShapeFix_Solid: done')
        except Exception as _e:
            print(f'MakeSolid failed: {_e}')

    # Wrap back into build123d type
    try:
        _exp2 = TopExp_Explorer(raw, TopAbs_SOLID)
        _solids = []
        while _exp2.More():
            _solids.append(Solid(TopoDS.Solid_s(_exp2.Current())))
            _exp2.Next()
        if _solids:
            _result = _solids[0] if len(_solids) == 1 else Compound(_solids)
            print(f'Repair complete: {len(_solids)} solid(s)')
            return _result
    except Exception as _e:
        print(f'Wrap failed: {_e}')

    return shape

_export_shape = _repair_for_export(part.part)

# -- Export --
# PREFERRED for Fusion 360: import fusion_features.step — STEP preserves B-Rep topology
# and avoids all mesh/tessellation issues. Use the STL only for 3D printing.
# export_step(_export_shape, 'fusion_features.step')
# # Fine tessellation (tolerance=0.05 mm, angular_tolerance=0.1 rad) reduces gap artefacts
# export_stl(_export_shape, 'fusion_features.stl', tolerance=0.05, angular_tolerance=0.1)

if _has_ocp: show(part)
# EXPORT STL + STEP
export_stl(part.part, GENERATED_STL)
print(f"Exported STL  -> {GENERATED_STL}")
export_step(_export_shape, GENERATED_STEP)
print(f"Exported STEP -> {GENERATED_STEP}")
# VOLUME COMPARISON
try:
    if os.path.exists(REFERENCE_STL):
        reference_volume = trimesh.load_mesh(REFERENCE_STL).volume * REFERENCE_SCALE
        generated_volume = trimesh.load_mesh(GENERATED_STL).volume
        difference       = generated_volume - reference_volume
        print("\n========== VOLUME COMPARISON ==========\n")
        print(f"Reference Volume : {reference_volume:.3f} mm³")
        print(f"Generated Volume : {generated_volume:.3f} mm³")
        print(f"Difference       : {difference:.3f} mm³  ({difference/reference_volume*100:.2f}%)")
    else:
        print(f"[Volume] Reference STL not found at {REFERENCE_STL} — skipping comparison")
except ImportError:
    print("[Volume] trimesh not installed — skipping comparison")

# # ── STL mesh repair ───────────────────────────────────────────────────────────
# # OCC tessellates every B-Rep face independently: vertices at shared edges are
# # written twice (once per face).  trimesh's default merge tolerance (~1e-8 mm)
# # is far too tight for CAD — boundary vertices that are ≤0.01 mm apart stay
# # disconnected and render as visible tears.
# # Fix order:
# #   1. round-and-merge vertices at 0.01 mm tolerance  → reconnects seam vertices
# #   2. remove duplicate / degenerate triangles
# #   3. fix winding + outward normals
# #   4. flip if volume is negative
# # ─────────────────────────────────────────────────────────────────────────────
# def _stl_repair(path):
#     import numpy as _np
#     try:
#         import trimesh as _tm
#     except ImportError:
#         print('trimesh not installed — skipping mesh repair')
#         return

#     _mesh = _tm.load(path, force='mesh')
#     _n0v, _n0f = len(_mesh.vertices), len(_mesh.faces)
#     print(f'[repair] loaded: {_n0v} verts, {_n0f} faces')
#     print(f'[repair] watertight={_mesh.is_watertight}, volume={_mesh.volume:.3f}')

#     # Step 1: merge vertices within 0.01 mm
#     _vk = _np.round(_mesh.vertices, decimals=2)
#     _uv, _fi, _inv = _np.unique(_vk, axis=0, return_index=True, return_inverse=True)
#     if len(_fi) < _n0v:
#         _mesh = _tm.Trimesh(
#             vertices=_mesh.vertices[_fi],
#             faces=_inv[_mesh.faces],
#             process=True,
#         )
#         print(f'[repair] vertex merge: {_n0v} → {len(_mesh.vertices)} '
#               f'({_n0v - len(_mesh.vertices)} merged, ≤0.01 mm tolerance)')
#     _mesh.remove_duplicate_faces()
#     _mesh.remove_degenerate_faces()
#     print(f'[repair] after merge+dedup: {len(_mesh.vertices)} verts, '
#           f'{len(_mesh.faces)} faces, watertight={_mesh.is_watertight}, '
#           f'volume={_mesh.volume:.3f}')

#     # Step 2: fix winding + normals
#     _tm.repair.fix_winding(_mesh)
#     _tm.repair.fix_normals(_mesh, multibody=False)
#     print(f'[repair] after orientation: watertight={_mesh.is_watertight}, volume={_mesh.volume:.3f}')

#     # Step 3: force positive volume
#     if _mesh.volume < 0:
#         print('[repair] volume negative — inverting')
#         _mesh.invert()
#         print(f'[repair] after invert: volume={_mesh.volume:.3f}')

#     _mesh.export(path)
#     if _mesh.is_watertight and _mesh.volume > 0:
#         print(f'[repair] saved clean mesh — volume={_mesh.volume:.3f} mm³')
#     else:
#         print(f'[repair] saved (best effort) — watertight={_mesh.is_watertight}, '
#               f'volume={_mesh.volume:.3f}')
#         print('[repair] TIP: open fusion_features.step in Fusion 360 for a clean solid import')

# try:
#     _stl_repair('fusion_features.stl')
# except Exception as _rep_err:
#     print(f'[repair] pipeline error: {_rep_err}')

# if _has_ocp: show(part)
