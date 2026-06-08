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

# 'Sketch3': 4 segments → Line/RadiusArc profile
_inclined_plane_1 = Plane(
    origin=Vector(756.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch3:
    with BuildLine():
        Line((626.5882, 4.6648), (146.5882, 4.6648))
        Line((146.5882, 4.6648), (146.5882, 656.6647))
        Line((146.5882, 656.6647), (626.5882, 656.6647))
        Line((626.5882, 656.6647), (626.5882, 4.6648))
    _inc_edges_sk_Sketch3 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch3 = Wire.combine(_inc_edges_sk_Sketch3)[0]
_wire_sk_Sketch3 = _wire_sk_Sketch3.moved(_inclined_plane_1.location)
_mkf_sk_Sketch3 = BRepBuilderAPI_MakeFace(_inclined_plane_1.wrapped, _wire_sk_Sketch3.wrapped, True)
_face_sk_Sketch3 = Face(_mkf_sk_Sketch3.Face())

# Path wire for Sweep1
with BuildLine() as _bl_Sweep1:
    Line((756.875, 209.2956, 4.6648), (756.875, 209.2956, 556.6648))
    ThreePointArc((756.875, 209.2956, 556.6648), (756.875, 220.2183, 583.0347), (756.875, 246.5882, 593.9575))
    Line((756.875, 246.5882, 593.9575), (756.875, 526.5882, 593.9575))
    ThreePointArc((756.875, 526.5882, 593.9575), (756.875, 552.9582, 583.0347), (756.875, 563.8809, 556.6648))
    Line((756.875, 563.8809, 556.6648), (756.875, 563.8809, -100.0307))
path_Sweep1 = _bl_Sweep1.wires()[0]

# Profile plane from sketch (origin at sketch_origin)
_plane_Sweep1 = Plane(origin=Vector(0.0, 0.0, 4.6648), x_dir=Vector(1.0, 0.0, 0.0), z_dir=Vector(0.0, 0.0, -1.0))

# 'Sketch4': 8 segments -> sweep profile
with BuildSketch(_plane_Sweep1) as sk_Sketch4_1:
    with BuildLine():
        Line((756.875, -176.5882), (756.875, -209.2956))
        Line((756.875, -209.2956), (839.4419, -209.2956))
        Line((839.4419, -209.2956), (839.4419, -66.2804))
        Line((839.4419, -66.2804), (696.875, -66.2804))
        Line((696.875, -66.2804), (696.875, -146.5882))
        Line((696.875, -146.5882), (696.875, -176.5882))
        RadiusArc((696.875, -176.5882), (726.875, -146.5882), 30.0)
        RadiusArc((726.875, -146.5882), (756.875, -176.5882), 30.0)
    make_face()
# 'Sketch6': 8 segments → Line/RadiusArc profile
_inclined_plane_3 = Plane(
    origin=Vector(0.0, 0.0, 206.6648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_3) as sk_Sketch6_3:
    with BuildLine():
        Line((-449.375, -226.5882), (-449.375, -546.5882))
        Line((-449.375, -546.5882), (-696.875, -546.5882))
        Line((-696.875, -546.5882), (-696.875, -226.5882))
        Line((-696.875, -226.5882), (-642.875, -226.5882))
        Line((-642.875, -226.5882), (-642.875, -214.5882))
        Line((-642.875, -214.5882), (-502.875, -214.5882))
        Line((-502.875, -214.5882), (-502.875, -226.5882))
        Line((-502.875, -226.5882), (-449.375, -226.5882))
    _inc_edges_sk_Sketch6_3 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch6_3 = Wire.combine(_inc_edges_sk_Sketch6_3)[0]
_wire_sk_Sketch6_3 = _wire_sk_Sketch6_3.moved(_inclined_plane_3.location)
_mkf_sk_Sketch6_3 = BRepBuilderAPI_MakeFace(_inclined_plane_3.wrapped, _wire_sk_Sketch6_3.wrapped, True)
_face_sk_Sketch6_3 = Face(_mkf_sk_Sketch6_3.Face())

# 'Sketch7': 19 segments → Line/RadiusArc profile
_inclined_plane_4 = Plane(
    origin=Vector(0.0, 146.5882, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch7_4:
    with BuildLine():
        Line((487.3349, 396.2529), (523.7717, 413.8973))
        Line((523.7717, 413.8973), (610.2766, 459.389))
        RadiusArc((610.2766, 459.389), (669.3591, 516.6648), -113.5456)
        Line((669.3591, 516.6648), (696.875, 516.6648))
        Line((696.875, 516.6648), (696.875, 626.6648))
        Line((696.875, 626.6648), (696.875, 765.52))
        Line((696.875, 765.52), (315.0884, 765.52))
        Line((315.0884, 765.52), (315.0884, -72.2627))
        Line((315.0884, -72.2627), (762.1271, -72.2627))
        Line((762.1271, -72.2627), (756.875, 4.6648))
        Line((756.875, 4.6648), (436.3721, 4.6648))
        Line((436.3721, 4.6648), (436.3721, 18.7303))
        RadiusArc((436.3721, 18.7303), (440.2944, 43.3513), -65.0629)
        RadiusArc((440.2944, 43.3513), (434.5121, 79.3031), -203.7508)
        Line((434.5121, 79.3031), (388.375, 130.5436))
        Line((388.375, 130.5436), (388.375, 299.1512))
        Line((388.375, 299.1512), (427.375, 299.3031))
        Line((427.375, 299.3031), (427.375, 369.5351))
        Line((427.375, 369.5351), (487.3349, 396.2529))
    _inc_edges_sk_Sketch7_4 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch7_4 = Wire.combine(_inc_edges_sk_Sketch7_4)[0]
_wire_sk_Sketch7_4 = _wire_sk_Sketch7_4.moved(_inclined_plane_4.location)
_mkf_sk_Sketch7_4 = BRepBuilderAPI_MakeFace(_inclined_plane_4.wrapped, _wire_sk_Sketch7_4.wrapped, True)
_face_sk_Sketch7_4 = Face(_mkf_sk_Sketch7_4.Face())

# 'Sketch9': 3 segments → Line/RadiusArc profile
_inclined_plane_5 = Plane(
    origin=Vector(0.0, 0.0, 516.6648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch9_5:
    with BuildLine():
        Line((-696.875, -626.5882), (-726.875, -626.5882))
        RadiusArc((-726.875, -626.5882), (-696.875, -596.5882), -30.0)
        Line((-696.875, -596.5882), (-696.875, -626.5882))
    _inc_edges_sk_Sketch9_5 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch9_5 = Wire.combine(_inc_edges_sk_Sketch9_5)[0]
_wire_sk_Sketch9_5 = _wire_sk_Sketch9_5.moved(_inclined_plane_5.location)
_mkf_sk_Sketch9_5 = BRepBuilderAPI_MakeFace(_inclined_plane_5.wrapped, _wire_sk_Sketch9_5.wrapped, True)
_face_sk_Sketch9_5 = Face(_mkf_sk_Sketch9_5.Face())

# 'Sketch9': 3 segments → Line/RadiusArc profile
_inclined_plane_6 = Plane(
    origin=Vector(0.0, 0.0, 516.6648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_6) as sk_Sketch9_6:
    with BuildLine():
        Line((-696.875, -146.5882), (-726.875, -146.5882))
        RadiusArc((-726.875, -146.5882), (-696.875, -176.5882), 30.0)
        Line((-696.875, -176.5882), (-696.875, -146.5882))
    _inc_edges_sk_Sketch9_6 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch9_6 = Wire.combine(_inc_edges_sk_Sketch9_6)[0]
_wire_sk_Sketch9_6 = _wire_sk_Sketch9_6.moved(_inclined_plane_6.location)
_mkf_sk_Sketch9_6 = BRepBuilderAPI_MakeFace(_inclined_plane_6.wrapped, _wire_sk_Sketch9_6.wrapped, True)
_face_sk_Sketch9_6 = Face(_mkf_sk_Sketch9_6.Face())

# 'Sketch8': 20 segments → Line/RadiusArc profile
_inclined_plane_7 = Plane(
    origin=Vector(388.375, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_7) as sk_Sketch8_7:
    with BuildLine():
        Line((-626.5882, 253.4867), (-767.8897, 334.3887))
        Line((-767.8897, 334.3887), (-767.8897, -109.7255))
        Line((-767.8897, -109.7255), (-5.2868, -109.7255))
        Line((-5.2868, -109.7255), (-5.2868, 334.3887))
        Line((-5.2868, 334.3887), (-146.5882, 253.4867))
        RadiusArc((-146.5882, 253.4867), (-154.6321, 214.5665), 83.8617)
        RadiusArc((-154.6321, 214.5665), (-160.6992, 204.156), 71.274)
        RadiusArc((-160.6992, 204.156), (-184.5306, 169.5484), -2270.9751)
        Line((-184.5306, 169.5484), (-271.9319, 42.6251))
        RadiusArc((-271.9319, 42.6251), (-294.8902, 18.7303), 89.5973)
        RadiusArc((-294.8902, 18.7303), (-340.5804, 4.6648), 80.1982)
        Line((-340.5804, 4.6648), (-340.5804, -21.9491))
        Line((-340.5804, -21.9491), (-432.5961, -21.9491))
        Line((-432.5961, -21.9491), (-432.5961, 4.6648))
        RadiusArc((-432.5961, 4.6648), (-478.2863, 18.7303), 80.1982)
        RadiusArc((-478.2863, 18.7303), (-501.2446, 42.6251), 89.5973)
        Line((-501.2446, 42.6251), (-588.6459, 169.5484))
        RadiusArc((-588.6459, 169.5484), (-612.4773, 204.156), -2270.9751)
        RadiusArc((-612.4773, 204.156), (-618.5444, 214.5665), 71.274)
        RadiusArc((-618.5444, 214.5665), (-626.5882, 253.4867), 83.8617)
    _inc_edges_sk_Sketch8_7 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch8_7 = Wire.combine(_inc_edges_sk_Sketch8_7)[0]
_wire_sk_Sketch8_7 = _wire_sk_Sketch8_7.moved(_inclined_plane_7.location)
_mkf_sk_Sketch8_7 = BRepBuilderAPI_MakeFace(_inclined_plane_7.wrapped, _wire_sk_Sketch8_7.wrapped, True)
_face_sk_Sketch8_7 = Face(_mkf_sk_Sketch8_7.Face())

# 'Sketch10': 10 segments → Line/RadiusArc profile
_inclined_plane_8 = Plane(
    origin=Vector(0.0, 626.5882, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 1.0, -0.0),
)
with BuildSketch(_inclined_plane_8) as sk_Sketch10_8:
    with BuildLine():
        Line((-523.7717, 334.3887), (-427.375, 299.3031))
        Line((-427.375, 299.3031), (-384.2036, 299.3031))
        Line((-384.2036, 299.3031), (-376.0975, 522.5643))
        Line((-376.0975, 522.5643), (-645.375, 522.5643))
        Line((-645.375, 522.5643), (-645.375, 482.4746))
        Line((-645.375, 482.4746), (-645.375, 464.1488))
        Line((-645.375, 464.1488), (-674.875, 431.3858))
        Line((-674.875, 431.3858), (-674.875, 389.3858))
        Line((-674.875, 389.3858), (-529.9143, 336.6244))
        Line((-529.9143, 336.6244), (-523.7717, 334.3887))
    _inc_edges_sk_Sketch10_8 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch10_8 = Wire.combine(_inc_edges_sk_Sketch10_8)[0]
_wire_sk_Sketch10_8 = _wire_sk_Sketch10_8.moved(_inclined_plane_8.location)
_mkf_sk_Sketch10_8 = BRepBuilderAPI_MakeFace(_inclined_plane_8.wrapped, _wire_sk_Sketch10_8.wrapped, True)
_face_sk_Sketch10_8 = Face(_mkf_sk_Sketch10_8.Face())

# 'Sketch14': 8 segments → Line/RadiusArc profile
_inclined_plane_9 = Plane(
    origin=Vector(0.0, 0.0, 299.3031),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_9) as sk_Sketch14_9:
    with BuildLine():
        Line((-388.375, -446.5882), (-427.375, -433.9164))
        Line((-427.375, -433.9164), (-427.375, -643.1885))
        Line((-427.375, -643.1885), (-231.292, -643.1885))
        Line((-231.292, -643.1885), (-231.292, -106.3619))
        Line((-231.292, -106.3619), (-427.375, -106.3619))
        Line((-427.375, -106.3619), (-427.375, -339.2601))
        Line((-427.375, -339.2601), (-388.375, -326.6283))
        Line((-388.375, -326.6283), (-388.375, -446.5882))
    _inc_edges_sk_Sketch14_9 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch14_9 = Wire.combine(_inc_edges_sk_Sketch14_9)[0]
_wire_sk_Sketch14_9 = _wire_sk_Sketch14_9.moved(_inclined_plane_9.location)
_mkf_sk_Sketch14_9 = BRepBuilderAPI_MakeFace(_inclined_plane_9.wrapped, _wire_sk_Sketch14_9.wrapped, True)
_face_sk_Sketch14_9 = Face(_mkf_sk_Sketch14_9.Face())

# 'Sketch15': 4 segments → Line/RadiusArc profile
_inclined_plane_10 = Plane(
    origin=Vector(664.875, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_10) as sk_Sketch15_10:
    with BuildLine():
        Line((-536.6984, 525.1978), (-565.5882, 525.1978))
        Line((-565.5882, 525.1978), (-565.5882, 428.1408))
        Line((-565.5882, 428.1408), (-536.6984, 428.1408))
        Line((-536.6984, 428.1408), (-536.6984, 525.1978))
    _inc_edges_sk_Sketch15_10 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch15_10 = Wire.combine(_inc_edges_sk_Sketch15_10)[0]
_wire_sk_Sketch15_10 = _wire_sk_Sketch15_10.moved(_inclined_plane_10.location)
_mkf_sk_Sketch15_10 = BRepBuilderAPI_MakeFace(_inclined_plane_10.wrapped, _wire_sk_Sketch15_10.wrapped, True)
_face_sk_Sketch15_10 = Face(_mkf_sk_Sketch15_10.Face())

_inclined_plane_11 = Plane(
    origin=Vector(0.0, 386.5882, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
# 'Sketch23': 7 segments → revolve profile
with BuildSketch(_inclined_plane_11) as sk_Sketch23_10:
    with BuildLine():
        Line((756.875, -476.6648), (816.875, -476.6648))
        Line((816.875, -476.6648), (816.875, -468.6647))
        Line((816.875, -468.6647), (806.875, -458.6648))
        Line((806.875, -458.6648), (806.875, -356.6648))
        Line((806.875, -356.6648), (756.875, -356.6648))
        Line((756.875, -356.6648), (756.875, -458.6648))
        Line((756.875, -458.6648), (756.875, -476.6648))
    make_face()
# 'Sketch25': 5 segments → Line/RadiusArc profile
_inclined_plane_12 = Plane(
    origin=Vector(816.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_12) as sk_Sketch25_12:
    with BuildLine():
        Line((313.5009, 441.5308), (313.5009, 451.8396))
        RadiusArc((313.5009, 451.8396), (274.4382, 313.9757), -120.0)
        Line((274.4382, 313.9757), (296.1579, 313.9757))
        RadiusArc((296.1579, 313.9757), (313.5009, 424.9161), 99.9999)
        Line((313.5009, 424.9161), (313.5009, 441.5308))
    _inc_edges_sk_Sketch25_12 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch25_12 = Wire.combine(_inc_edges_sk_Sketch25_12)[0]
_wire_sk_Sketch25_12 = _wire_sk_Sketch25_12.moved(_inclined_plane_12.location)
_mkf_sk_Sketch25_12 = BRepBuilderAPI_MakeFace(_inclined_plane_12.wrapped, _wire_sk_Sketch25_12.wrapped, True)
_face_sk_Sketch25_12 = Face(_mkf_sk_Sketch25_12.Face())

# 'Sketch26': 4 segments → Line/RadiusArc profile
_inclined_plane_13 = Plane(
    origin=Vector(816.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_13) as sk_Sketch26_13:
    with BuildLine():
        Line((477.0185, 313.9757), (498.7383, 313.9757))
        RadiusArc((498.7383, 313.9757), (459.6756, 451.8396), -120.0001)
        Line((459.6756, 451.8396), (459.6756, 424.9161))
        RadiusArc((459.6756, 424.9161), (477.0185, 313.9757), 100.0)
    _inc_edges_sk_Sketch26_13 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch26_13 = Wire.combine(_inc_edges_sk_Sketch26_13)[0]
_wire_sk_Sketch26_13 = _wire_sk_Sketch26_13.moved(_inclined_plane_13.location)
_mkf_sk_Sketch26_13 = BRepBuilderAPI_MakeFace(_inclined_plane_13.wrapped, _wire_sk_Sketch26_13.wrapped, True)
_face_sk_Sketch26_13 = Face(_mkf_sk_Sketch26_13.Face())

# 'Sketch28': 5 segments → Line/RadiusArc profile
_inclined_plane_14 = Plane(
    origin=Vector(806.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_14) as sk_Sketch28_14:
    with BuildLine():
        Line((356.3395, 245.4333), (341.5598, 245.4333))
        Line((341.5598, 245.4333), (341.5598, 189.9027))
        Line((341.5598, 189.9027), (431.6167, 189.9027))
        Line((431.6167, 189.9027), (431.6167, 245.4333))
        Line((431.6167, 245.4333), (356.3395, 245.4333))
    _inc_edges_sk_Sketch28_14 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch28_14 = Wire.combine(_inc_edges_sk_Sketch28_14)[0]
_wire_sk_Sketch28_14 = _wire_sk_Sketch28_14.moved(_inclined_plane_14.location)
_mkf_sk_Sketch28_14 = BRepBuilderAPI_MakeFace(_inclined_plane_14.wrapped, _wire_sk_Sketch28_14.wrapped, True)
_face_sk_Sketch28_14 = Face(_mkf_sk_Sketch28_14.Face())

# 'Sketch27': 8 segments → Line/RadiusArc profile
_inclined_plane_15 = Plane(
    origin=Vector(0.0, 386.5882, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_15) as sk_Sketch27_15:
    with BuildLine():
        Line((816.875, -450.3053), (888.5068, -450.3053))
        Line((888.5068, -450.3053), (888.5068, -176.9489))
        Line((888.5068, -176.9489), (756.875, -176.9489))
        Line((756.875, -176.9489), (756.875, -189.9027))
        Line((756.875, -189.9027), (806.875, -245.4333))
        Line((806.875, -245.4333), (806.875, -313.9757))
        Line((806.875, -313.9757), (816.875, -325.8932))
        Line((816.875, -325.8932), (816.875, -450.3053))
    _inc_edges_sk_Sketch27_15 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch27_15 = Wire.combine(_inc_edges_sk_Sketch27_15)[0]
_wire_sk_Sketch27_15 = _wire_sk_Sketch27_15.moved(_inclined_plane_15.location)
_mkf_sk_Sketch27_15 = BRepBuilderAPI_MakeFace(_inclined_plane_15.wrapped, _wire_sk_Sketch27_15.wrapped, True)
_face_sk_Sketch27_15 = Face(_mkf_sk_Sketch27_15.Face())

# 'Sketch27': 8 segments → Line/RadiusArc profile
_inclined_plane_16 = Plane(
    origin=Vector(0.0, 386.5882, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_16) as sk_Sketch27_16:
    with BuildLine():
        Line((816.875, -450.3053), (888.5068, -450.3053))
        Line((888.5068, -450.3053), (888.5068, -176.9489))
        Line((888.5068, -176.9489), (756.875, -176.9489))
        Line((756.875, -176.9489), (756.875, -189.9027))
        Line((756.875, -189.9027), (806.875, -245.4333))
        Line((806.875, -245.4333), (806.875, -313.9757))
        Line((806.875, -313.9757), (816.875, -325.8932))
        Line((816.875, -325.8932), (816.875, -450.3053))
    _inc_edges_sk_Sketch27_16 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch27_16 = Wire.combine(_inc_edges_sk_Sketch27_16)[0]
_wire_sk_Sketch27_16 = _wire_sk_Sketch27_16.moved(_inclined_plane_16.location)
_mkf_sk_Sketch27_16 = BRepBuilderAPI_MakeFace(_inclined_plane_16.wrapped, _wire_sk_Sketch27_16.wrapped, True)
_face_sk_Sketch27_16 = Face(_mkf_sk_Sketch27_16.Face())

# 'Sketch29': 3 segments → Line/RadiusArc profile
_inclined_plane_17 = Plane(
    origin=Vector(806.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_17) as sk_Sketch29_17:
    with BuildLine():
        Line((348.5223, 417.3569), (337.0908, 429.0304))
        Line((337.0908, 429.0304), (325.6592, 417.3569))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((325.6592, 417.3569), (337.0908, 390.1622), -16.0)
        RadiusArc((337.0908, 390.1622), (348.5223, 417.3569), -16.0)
    _inc_edges_sk_Sketch29_17 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch29_17 = Wire.combine(_inc_edges_sk_Sketch29_17)[0]
_wire_sk_Sketch29_17 = _wire_sk_Sketch29_17.moved(_inclined_plane_17.location)
_mkf_sk_Sketch29_17 = BRepBuilderAPI_MakeFace(_inclined_plane_17.wrapped, _wire_sk_Sketch29_17.wrapped, True)
_face_sk_Sketch29_17 = Face(_mkf_sk_Sketch29_17.Face())

# 'Sketch30': 3 segments → Line/RadiusArc profile
_inclined_plane_18 = Plane(
    origin=Vector(806.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_18) as sk_Sketch30_18:
    with BuildLine():
        Line((436.0857, 429.0304), (424.6541, 417.3569))
        # Arc split: sweep=271.34deg >= 150 — emitted as two half-arcs
        RadiusArc((424.6541, 417.3569), (436.4401, 390.1661), -16.0)
        RadiusArc((436.4401, 390.1661), (447.0102, 417.8522), -16.0)
        Line((447.0102, 417.8522), (436.0857, 429.0304))
    _inc_edges_sk_Sketch30_18 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch30_18 = Wire.combine(_inc_edges_sk_Sketch30_18)[0]
_wire_sk_Sketch30_18 = _wire_sk_Sketch30_18.moved(_inclined_plane_18.location)
_mkf_sk_Sketch30_18 = BRepBuilderAPI_MakeFace(_inclined_plane_18.wrapped, _wire_sk_Sketch30_18.wrapped, True)
_face_sk_Sketch30_18 = Face(_mkf_sk_Sketch30_18.Face())

# 'Sketch31': 3 segments → Line/RadiusArc profile
_inclined_plane_19 = Plane(
    origin=Vector(806.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_19) as sk_Sketch31_19:
    with BuildLine():
        Line((436.0857, 330.0354), (424.6542, 318.3619))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((424.6542, 318.3619), (436.0857, 291.1673), -16.0)
        RadiusArc((436.0857, 291.1673), (447.5173, 318.3619), -16.0)
        Line((447.5173, 318.3619), (436.0857, 330.0354))
    _inc_edges_sk_Sketch31_19 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch31_19 = Wire.combine(_inc_edges_sk_Sketch31_19)[0]
_wire_sk_Sketch31_19 = _wire_sk_Sketch31_19.moved(_inclined_plane_19.location)
_mkf_sk_Sketch31_19 = BRepBuilderAPI_MakeFace(_inclined_plane_19.wrapped, _wire_sk_Sketch31_19.wrapped, True)
_face_sk_Sketch31_19 = Face(_mkf_sk_Sketch31_19.Face())

# 'Sketch32': 3 segments → Line/RadiusArc profile
_inclined_plane_20 = Plane(
    origin=Vector(806.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_20) as sk_Sketch32_20:
    with BuildLine():
        Line((337.0908, 330.0354), (325.6592, 318.3619))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((325.6592, 318.3619), (337.0908, 291.1673), -16.0)
        RadiusArc((337.0908, 291.1673), (348.5223, 318.3619), -16.0)
        Line((348.5223, 318.3619), (337.0908, 330.0354))
    _inc_edges_sk_Sketch32_20 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch32_20 = Wire.combine(_inc_edges_sk_Sketch32_20)[0]
_wire_sk_Sketch32_20 = _wire_sk_Sketch32_20.moved(_inclined_plane_20.location)
_mkf_sk_Sketch32_20 = BRepBuilderAPI_MakeFace(_inclined_plane_20.wrapped, _wire_sk_Sketch32_20.wrapped, True)
_face_sk_Sketch32_20 = Face(_mkf_sk_Sketch32_20.Face())

# 'Sketch35': 3 segments → Line/RadiusArc profile
_inclined_plane_21 = Plane(
    origin=Vector(806.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_21) as sk_Sketch35_21:
    with BuildLine():
        Line((386.5882, 395.2547), (367.2975, 375.5557))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((367.2975, 375.5557), (386.5882, 329.6653), -26.9998)
        RadiusArc((386.5882, 329.6653), (405.879, 375.5557), -26.9998)
        Line((405.879, 375.5557), (386.5882, 395.2547))
    _inc_edges_sk_Sketch35_21 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch35_21 = Wire.combine(_inc_edges_sk_Sketch35_21)[0]
_wire_sk_Sketch35_21 = _wire_sk_Sketch35_21.moved(_inclined_plane_21.location)
_mkf_sk_Sketch35_21 = BRepBuilderAPI_MakeFace(_inclined_plane_21.wrapped, _wire_sk_Sketch35_21.wrapped, True)
_face_sk_Sketch35_21 = Face(_mkf_sk_Sketch35_21.Face())

# 'Sketch36': 3 segments → Line/RadiusArc profile
_inclined_plane_22 = Plane(
    origin=Vector(776.875, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_22) as sk_Sketch36_22:
    with BuildLine():
        Line((-436.0857, 449.04), (-457.5199, 427.1521))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-457.5199, 427.1521), (-436.0857, 376.1622), -30.0)
        RadiusArc((-436.0857, 376.1622), (-414.6515, 427.1521), -30.0)
        Line((-414.6515, 427.1521), (-436.0857, 449.04))
    _inc_edges_sk_Sketch36_22 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch36_22 = Wire.combine(_inc_edges_sk_Sketch36_22)[0]
_wire_sk_Sketch36_22 = _wire_sk_Sketch36_22.moved(_inclined_plane_22.location)
_mkf_sk_Sketch36_22 = BRepBuilderAPI_MakeFace(_inclined_plane_22.wrapped, _wire_sk_Sketch36_22.wrapped, True)
_face_sk_Sketch36_22 = Face(_mkf_sk_Sketch36_22.Face())

# 'Sketch36': 3 segments → Line/RadiusArc profile
_inclined_plane_23 = Plane(
    origin=Vector(776.875, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_23) as sk_Sketch36_23:
    with BuildLine():
        Line((-337.0908, 449.04), (-358.5249, 427.1521))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-358.5249, 427.1521), (-337.0908, 376.1622), -30.0)
        RadiusArc((-337.0908, 376.1622), (-315.6566, 427.1521), -30.0)
        Line((-315.6566, 427.1521), (-337.0908, 449.04))
    _inc_edges_sk_Sketch36_23 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch36_23 = Wire.combine(_inc_edges_sk_Sketch36_23)[0]
_wire_sk_Sketch36_23 = _wire_sk_Sketch36_23.moved(_inclined_plane_23.location)
_mkf_sk_Sketch36_23 = BRepBuilderAPI_MakeFace(_inclined_plane_23.wrapped, _wire_sk_Sketch36_23.wrapped, True)
_face_sk_Sketch36_23 = Face(_mkf_sk_Sketch36_23.Face())

# 'Sketch36': 3 segments → Line/RadiusArc profile
_inclined_plane_24 = Plane(
    origin=Vector(776.875, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_24) as sk_Sketch36_24:
    with BuildLine():
        Line((-337.0908, 350.0451), (-358.5249, 328.1572))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-358.5249, 328.1572), (-337.0908, 277.1673), -30.0)
        RadiusArc((-337.0908, 277.1673), (-315.6566, 328.1572), -30.0)
        Line((-315.6566, 328.1572), (-337.0908, 350.0451))
    _inc_edges_sk_Sketch36_24 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch36_24 = Wire.combine(_inc_edges_sk_Sketch36_24)[0]
_wire_sk_Sketch36_24 = _wire_sk_Sketch36_24.moved(_inclined_plane_24.location)
_mkf_sk_Sketch36_24 = BRepBuilderAPI_MakeFace(_inclined_plane_24.wrapped, _wire_sk_Sketch36_24.wrapped, True)
_face_sk_Sketch36_24 = Face(_mkf_sk_Sketch36_24.Face())

# 'Sketch36': 3 segments → Line/RadiusArc profile
_inclined_plane_25 = Plane(
    origin=Vector(776.875, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_25) as sk_Sketch36_25:
    with BuildLine():
        Line((-436.0857, 350.0451), (-457.5199, 328.1572))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-457.5199, 328.1572), (-436.0857, 277.1673), -30.0)
        RadiusArc((-436.0857, 277.1673), (-414.6515, 328.1572), -30.0)
        Line((-414.6515, 328.1572), (-436.0857, 350.0451))
    _inc_edges_sk_Sketch36_25 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch36_25 = Wire.combine(_inc_edges_sk_Sketch36_25)[0]
_wire_sk_Sketch36_25 = _wire_sk_Sketch36_25.moved(_inclined_plane_25.location)
_mkf_sk_Sketch36_25 = BRepBuilderAPI_MakeFace(_inclined_plane_25.wrapped, _wire_sk_Sketch36_25.wrapped, True)
_face_sk_Sketch36_25 = Face(_mkf_sk_Sketch36_25.Face())

# 'Sketch37': circle on inclined plane
_inclined_plane_26 = Plane(
    origin=Vector(716.875, 0.0, 0.0),
    x_dir=Vector(0.0, -1.0, 0.0),
    z_dir=Vector(-1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_26) as sk_Sketch37_26:
    with Locations((-386.5883, 356.6644)):
        Circle(radius=112.4267)

# 'Sketch38': 10 segments → Line/RadiusArc profile
_inclined_plane_27 = Plane(
    origin=Vector(0.0, 565.5882, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
with BuildSketch(_inclined_plane_27) as sk_Sketch38_27:
    with BuildLine():
        Line((473.5435, 316.1071), (480.875, 308.7755))
        Line((480.875, 308.7755), (480.875, 256.6648))
        Line((480.875, 256.6648), (664.875, 256.6648))
        Line((664.875, 256.6648), (664.875, 375.1043))
        Line((664.875, 375.1043), (664.875, 375.7461))
        Line((664.875, 375.7461), (674.875, 385.7461))
        Line((674.875, 385.7461), (674.875, 389.3858))
        Line((674.875, 389.3858), (674.875, 431.3858))
        Line((674.875, 431.3858), (452.9507, 336.7))
        Line((452.9507, 336.7), (473.5435, 316.1071))
    _inc_edges_sk_Sketch38_27 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch38_27 = Wire.combine(_inc_edges_sk_Sketch38_27)[0]
_wire_sk_Sketch38_27 = _wire_sk_Sketch38_27.moved(_inclined_plane_27.location)
_mkf_sk_Sketch38_27 = BRepBuilderAPI_MakeFace(_inclined_plane_27.wrapped, _wire_sk_Sketch38_27.wrapped, True)
_face_sk_Sketch38_27 = Face(_mkf_sk_Sketch38_27.Face())

# Path wire for Sweep3
with BuildLine() as _bl_Sweep3:
    Line((427.375, 433.9164, 299.3031), (388.375, 446.5882, 299.1512))
path_Sweep3 = _bl_Sweep3.wires()[0]

# Profile plane from sketch (origin at sketch_origin)
_plane_Sweep3 = Plane(origin=Vector(388.375, 0.0, 0.0), x_dir=Vector(0.0, -1.0, 0.0), z_dir=Vector(-1.0, 0.0, 0.0))

# 'Sketch42': 3 segments -> sweep profile
with BuildSketch(_plane_Sweep3) as sk_Sketch42_27:
    with BuildLine():
        Line((-446.5882, 299.1512), (-446.5882, 290.9462))
        RadiusArc((-446.5882, 290.9462), (-437.8075, 299.1512), 10.5308)
        Line((-437.8075, 299.1512), (-446.5882, 299.1512))
    make_face()
# Path wire for Sweep4
with BuildLine() as _bl_Sweep4:
    Line((388.375, 326.6283, 299.1512), (427.375, 339.2601, 299.3031))
path_Sweep4 = _bl_Sweep4.wires()[0]

# Profile plane from sketch (origin at sketch_origin)
_plane_Sweep4 = Plane(origin=Vector(388.375, 0.0, 0.0), x_dir=Vector(0.0, -1.0, 0.0), z_dir=Vector(-1.0, 0.0, 0.0))

# 'Sketch46': 3 segments -> sweep profile
with BuildSketch(_plane_Sweep4) as sk_Sketch46_28:
    with BuildLine():
        Line((-335.409, 299.1512), (-326.6283, 299.1512))
        Line((-326.6283, 299.1512), (-326.6283, 290.4299))
        RadiusArc((-326.6283, 290.4299), (-335.409, 299.1512), -10.548)
    make_face()
# 'Sketch48': circle on inclined plane
_inclined_plane_30 = Plane(
    origin=Vector(0.0, 0.0, 206.6648),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_30) as sk_Sketch48_30:
    with Locations((572.875, 390.0882)):
        Circle(radius=50.0001)

# 'Sketch49': 3 segments → Line/RadiusArc profile
_inclined_plane_31 = Plane(
    origin=Vector(0.0, 204.5882, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_31) as sk_Sketch49_31:
    with BuildLine():
        Line((-661.0855, -282.658), (-675.375, -297.2499))
        Line((-675.375, -297.2499), (-689.6645, -282.658))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-689.6645, -282.658), (-675.3749, -248.6648), 20.0)
        RadiusArc((-675.3749, -248.6648), (-661.0855, -282.658), 20.0)
    _inc_edges_sk_Sketch49_31 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch49_31 = Wire.combine(_inc_edges_sk_Sketch49_31)[0]
_wire_sk_Sketch49_31 = _wire_sk_Sketch49_31.moved(_inclined_plane_31.location)
_mkf_sk_Sketch49_31 = BRepBuilderAPI_MakeFace(_inclined_plane_31.wrapped, _wire_sk_Sketch49_31.wrapped, True)
_face_sk_Sketch49_31 = Face(_mkf_sk_Sketch49_31.Face())

# 'Sketch49': 3 segments → Line/RadiusArc profile
_inclined_plane_32 = Plane(
    origin=Vector(0.0, 204.5882, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_32) as sk_Sketch49_32:
    with BuildLine():
        Line((-456.0855, -282.658), (-470.375, -297.2499))
        Line((-470.375, -297.2499), (-484.6645, -282.658))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-484.6645, -282.658), (-470.3749, -248.6648), 20.0)
        RadiusArc((-470.3749, -248.6648), (-456.0855, -282.658), 20.0)
    _inc_edges_sk_Sketch49_32 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch49_32 = Wire.combine(_inc_edges_sk_Sketch49_32)[0]
_wire_sk_Sketch49_32 = _wire_sk_Sketch49_32.moved(_inclined_plane_32.location)
_mkf_sk_Sketch49_32 = BRepBuilderAPI_MakeFace(_inclined_plane_32.wrapped, _wire_sk_Sketch49_32.wrapped, True)
_face_sk_Sketch49_32 = Face(_mkf_sk_Sketch49_32.Face())

# 'Sketch49': 3 segments → Line/RadiusArc profile
_inclined_plane_33 = Plane(
    origin=Vector(0.0, 204.5882, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_33) as sk_Sketch49_33:
    with BuildLine():
        Line((-675.375, -504.25), (-661.0855, -489.658))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-661.0855, -489.658), (-675.375, -455.6647), -20.0)
        RadiusArc((-675.375, -455.6647), (-689.6645, -489.658), -20.0)
        Line((-689.6645, -489.658), (-675.375, -504.25))
    _inc_edges_sk_Sketch49_33 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch49_33 = Wire.combine(_inc_edges_sk_Sketch49_33)[0]
_wire_sk_Sketch49_33 = _wire_sk_Sketch49_33.moved(_inclined_plane_33.location)
_mkf_sk_Sketch49_33 = BRepBuilderAPI_MakeFace(_inclined_plane_33.wrapped, _wire_sk_Sketch49_33.wrapped, True)
_face_sk_Sketch49_33 = Face(_mkf_sk_Sketch49_33.Face())

# 'Sketch50': 3 segments → Line/RadiusArc profile
_inclined_plane_34 = Plane(
    origin=Vector(0.0, 204.5882, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_34) as sk_Sketch50_34:
    with BuildLine():
        # Arc split: sweep=268.81deg >= 150 — emitted as two half-arcs
        RadiusArc((-668.231, -482.6622), (-675.3745, -465.6648), -10.0)
        RadiusArc((-675.3745, -465.6648), (-682.5197, -482.6614), -10.0)
        Line((-682.5197, -482.6614), (-675.375, -489.9574))
        Line((-675.375, -489.9574), (-668.231, -482.6622))
    _inc_edges_sk_Sketch50_34 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch50_34 = Wire.combine(_inc_edges_sk_Sketch50_34)[0]
_wire_sk_Sketch50_34 = _wire_sk_Sketch50_34.moved(_inclined_plane_34.location)
_mkf_sk_Sketch50_34 = BRepBuilderAPI_MakeFace(_inclined_plane_34.wrapped, _wire_sk_Sketch50_34.wrapped, True)
_face_sk_Sketch50_34 = Face(_mkf_sk_Sketch50_34.Face())

# 'Sketch50': 3 segments → Line/RadiusArc profile
_inclined_plane_35 = Plane(
    origin=Vector(0.0, 204.5882, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_35) as sk_Sketch50_35:
    with BuildLine():
        Line((-470.375, -282.9573), (-463.2302, -275.6614))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-463.2302, -275.6614), (-470.3751, -258.6648), -10.0)
        RadiusArc((-470.3751, -258.6648), (-477.5197, -275.6614), -10.0)
        Line((-477.5197, -275.6614), (-470.375, -282.9573))
    _inc_edges_sk_Sketch50_35 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch50_35 = Wire.combine(_inc_edges_sk_Sketch50_35)[0]
_wire_sk_Sketch50_35 = _wire_sk_Sketch50_35.moved(_inclined_plane_35.location)
_mkf_sk_Sketch50_35 = BRepBuilderAPI_MakeFace(_inclined_plane_35.wrapped, _wire_sk_Sketch50_35.wrapped, True)
_face_sk_Sketch50_35 = Face(_mkf_sk_Sketch50_35.Face())

# 'Sketch50': 3 segments → Line/RadiusArc profile
_inclined_plane_36 = Plane(
    origin=Vector(0.0, 204.5882, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_36) as sk_Sketch50_36:
    with BuildLine():
        Line((-668.2303, -275.6614), (-675.375, -282.9573))
        Line((-675.375, -282.9573), (-682.5197, -275.6614))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((-682.5197, -275.6614), (-675.375, -258.6649), 9.9999)
        RadiusArc((-675.375, -258.6649), (-668.2303, -275.6614), 9.9999)
    _inc_edges_sk_Sketch50_36 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch50_36 = Wire.combine(_inc_edges_sk_Sketch50_36)[0]
_wire_sk_Sketch50_36 = _wire_sk_Sketch50_36.moved(_inclined_plane_36.location)
_mkf_sk_Sketch50_36 = BRepBuilderAPI_MakeFace(_inclined_plane_36.wrapped, _wire_sk_Sketch50_36.wrapped, True)
_face_sk_Sketch50_36 = Face(_mkf_sk_Sketch50_36.Face())

# 'Sketch52': 3 segments → Line/RadiusArc profile
_inclined_plane_37 = Plane(
    origin=Vector(0.0, 568.5883, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_37) as sk_Sketch52_37:
    with BuildLine():
        Line((675.375, -504.25), (689.6645, -489.658))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((689.6645, -489.658), (675.375, -455.6648), -20.0)
        RadiusArc((675.375, -455.6648), (661.0855, -489.658), -20.0)
        Line((661.0855, -489.658), (675.375, -504.25))
    _inc_edges_sk_Sketch52_37 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch52_37 = Wire.combine(_inc_edges_sk_Sketch52_37)[0]
_wire_sk_Sketch52_37 = _wire_sk_Sketch52_37.moved(_inclined_plane_37.location)
_mkf_sk_Sketch52_37 = BRepBuilderAPI_MakeFace(_inclined_plane_37.wrapped, _wire_sk_Sketch52_37.wrapped, True)
_face_sk_Sketch52_37 = Face(_mkf_sk_Sketch52_37.Face())

# 'Sketch52': 3 segments → Line/RadiusArc profile
_inclined_plane_38 = Plane(
    origin=Vector(0.0, 568.5883, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_38) as sk_Sketch52_38:
    with BuildLine():
        Line((689.6645, -244.658), (675.375, -259.2499))
        Line((675.375, -259.2499), (661.0855, -244.658))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((661.0855, -244.658), (675.3751, -210.6648), 20.0)
        RadiusArc((675.3751, -210.6648), (689.6645, -244.658), 20.0)
    _inc_edges_sk_Sketch52_38 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch52_38 = Wire.combine(_inc_edges_sk_Sketch52_38)[0]
_wire_sk_Sketch52_38 = _wire_sk_Sketch52_38.moved(_inclined_plane_38.location)
_mkf_sk_Sketch52_38 = BRepBuilderAPI_MakeFace(_inclined_plane_38.wrapped, _wire_sk_Sketch52_38.wrapped, True)
_face_sk_Sketch52_38 = Face(_mkf_sk_Sketch52_38.Face())

# 'Sketch52': 3 segments → Line/RadiusArc profile
_inclined_plane_39 = Plane(
    origin=Vector(0.0, 568.5883, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_39) as sk_Sketch52_39:
    with BuildLine():
        Line((484.6645, -244.658), (470.375, -259.2499))
        Line((470.375, -259.2499), (456.0855, -244.658))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((456.0855, -244.658), (470.3751, -210.6648), 20.0)
        RadiusArc((470.3751, -210.6648), (484.6645, -244.658), 20.0)
    _inc_edges_sk_Sketch52_39 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch52_39 = Wire.combine(_inc_edges_sk_Sketch52_39)[0]
_wire_sk_Sketch52_39 = _wire_sk_Sketch52_39.moved(_inclined_plane_39.location)
_mkf_sk_Sketch52_39 = BRepBuilderAPI_MakeFace(_inclined_plane_39.wrapped, _wire_sk_Sketch52_39.wrapped, True)
_face_sk_Sketch52_39 = Face(_mkf_sk_Sketch52_39.Face())

# 'Sketch53': 3 segments → Line/RadiusArc profile
_inclined_plane_40 = Plane(
    origin=Vector(0.0, 568.5883, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_40) as sk_Sketch53_40:
    with BuildLine():
        Line((675.375, -489.9574), (682.5197, -482.6614))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((682.5197, -482.6614), (675.375, -465.6647), -10.0)
        RadiusArc((675.375, -465.6647), (668.2303, -482.6614), -10.0)
        Line((668.2303, -482.6614), (675.375, -489.9574))
    _inc_edges_sk_Sketch53_40 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch53_40 = Wire.combine(_inc_edges_sk_Sketch53_40)[0]
_wire_sk_Sketch53_40 = _wire_sk_Sketch53_40.moved(_inclined_plane_40.location)
_mkf_sk_Sketch53_40 = BRepBuilderAPI_MakeFace(_inclined_plane_40.wrapped, _wire_sk_Sketch53_40.wrapped, True)
_face_sk_Sketch53_40 = Face(_mkf_sk_Sketch53_40.Face())

# 'Sketch53': 3 segments → Line/RadiusArc profile
_inclined_plane_41 = Plane(
    origin=Vector(0.0, 568.5883, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_41) as sk_Sketch53_41:
    with BuildLine():
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((682.5197, -237.6614), (675.375, -220.6647), -10.0)
        RadiusArc((675.375, -220.6647), (668.2303, -237.6614), -10.0)
        Line((668.2303, -237.6614), (675.375, -244.9574))
        Line((675.375, -244.9574), (682.5197, -237.6614))
    _inc_edges_sk_Sketch53_41 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch53_41 = Wire.combine(_inc_edges_sk_Sketch53_41)[0]
_wire_sk_Sketch53_41 = _wire_sk_Sketch53_41.moved(_inclined_plane_41.location)
_mkf_sk_Sketch53_41 = BRepBuilderAPI_MakeFace(_inclined_plane_41.wrapped, _wire_sk_Sketch53_41.wrapped, True)
_face_sk_Sketch53_41 = Face(_mkf_sk_Sketch53_41.Face())

# 'Sketch53': 3 segments → Line/RadiusArc profile
_inclined_plane_42 = Plane(
    origin=Vector(0.0, 568.5883, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_42) as sk_Sketch53_42:
    with BuildLine():
        Line((477.5197, -237.6614), (470.375, -244.9574))
        Line((470.375, -244.9574), (463.2302, -237.6614))
        # Arc split: sweep=268.8deg >= 150 — emitted as two half-arcs
        RadiusArc((463.2302, -237.6614), (470.375, -220.6647), 10.0)
        RadiusArc((470.375, -220.6647), (477.5197, -237.6614), 10.0)
    _inc_edges_sk_Sketch53_42 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch53_42 = Wire.combine(_inc_edges_sk_Sketch53_42)[0]
_wire_sk_Sketch53_42 = _wire_sk_Sketch53_42.moved(_inclined_plane_42.location)
_mkf_sk_Sketch53_42 = BRepBuilderAPI_MakeFace(_inclined_plane_42.wrapped, _wire_sk_Sketch53_42.wrapped, True)
_face_sk_Sketch53_42 = Face(_mkf_sk_Sketch53_42.Face())

# 'Sketch54': circle on inclined plane
_inclined_plane_43 = Plane(
    origin=Vector(94.4676, -0.0007, 290.7331),
    x_dir=Vector(-7e-06, -1.0, -0.0),
    z_dir=Vector(-0.309025, 2e-06, -0.951054),
)
with BuildSketch(_inclined_plane_43) as sk_Sketch54_43:
    with Locations((-386.5912, -361.0218)):
        Circle(radius=6.0)

# 'Sketch56': 6 segments → Line/RadiusArc profile
_inclined_plane_44 = Plane(
    origin=Vector(0.0, 0.0, 662.5257),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_44) as sk_Sketch56_44:
    with BuildLine():
        Line((523.7717, 626.5882), (394.9959, 626.5882))
        Line((394.9959, 626.5882), (394.9959, 532.3163))
        Line((394.9959, 532.3163), (427.375, 532.3163))
        Line((427.375, 532.3163), (427.375, 583.0594))
        RadiusArc((427.375, 583.0594), (449.1104, 606.5828), 30.0002)
        Line((449.1104, 606.5828), (523.7717, 626.5882))
    _inc_edges_sk_Sketch56_44 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch56_44 = Wire.combine(_inc_edges_sk_Sketch56_44)[0]
_wire_sk_Sketch56_44 = _wire_sk_Sketch56_44.moved(_inclined_plane_44.location)
_mkf_sk_Sketch56_44 = BRepBuilderAPI_MakeFace(_inclined_plane_44.wrapped, _wire_sk_Sketch56_44.wrapped, True)
_face_sk_Sketch56_44 = Face(_mkf_sk_Sketch56_44.Face())

# 'Sketch57': 11 segments → Line/RadiusArc profile
_inclined_plane_45 = Plane(
    origin=Vector(0.0, 0.0, 662.5257),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_45) as sk_Sketch57_45:
    with BuildLine():
        Line((427.375, 261.1519), (427.375, 190.1171))
        RadiusArc((427.375, 190.1171), (449.1104, 166.5937), -30.0)
        Line((449.1104, 166.5937), (487.3349, 156.3515))
        Line((487.3349, 156.3515), (529.8388, 144.9626))
        Line((529.8388, 144.9626), (529.8388, 136.0768))
        Line((529.8388, 136.0768), (404.1305, 136.0768))
        Line((404.1305, 136.0768), (404.1305, 169.3615))
        Line((404.1305, 169.3615), (404.1305, 261.1519))
        Line((404.1305, 261.1519), (427.375, 261.1519))
        Line((427.375, 261.1519), (427.375, 190.1171))
        Line((427.375, 190.1171), (427.375, 261.1519))
    _inc_edges_sk_Sketch57_45 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch57_45 = Wire.combine(_inc_edges_sk_Sketch57_45)[0]
_wire_sk_Sketch57_45 = _wire_sk_Sketch57_45.moved(_inclined_plane_45.location)
_mkf_sk_Sketch57_45 = BRepBuilderAPI_MakeFace(_inclined_plane_45.wrapped, _wire_sk_Sketch57_45.wrapped, True)
_face_sk_Sketch57_45 = Face(_mkf_sk_Sketch57_45.Face())

# 'Sketch59': 8 segments → Line/RadiusArc profile
_inclined_plane_46 = Plane(
    origin=Vector(0.0, 339.2601, 0.0),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, -1.0, -0.0),
)
with BuildSketch(_inclined_plane_46) as sk_Sketch59_46:
    with BuildLine():
        RadiusArc((-427.9968, -120.5426), (-431.8791, -91.1834), -240.0921)
        RadiusArc((-431.8791, -91.1834), (-435.6652, -74.2567), -568.7541)
        RadiusArc((-435.6652, -74.2567), (-439.192, -56.0369), 239.2452)
        RadiusArc((-439.192, -56.0369), (-440.3547, -42.8807), 104.8292)
        Line((-440.3547, -42.8807), (-400.5543, -38.8299))
        Line((-400.5543, -38.8299), (-427.375, -87.2297))
        Line((-427.375, -87.2297), (-427.375, -138.2925))
        Line((-427.375, -138.2925), (-427.9968, -120.5426))
    _inc_edges_sk_Sketch59_46 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch59_46 = Wire.combine(_inc_edges_sk_Sketch59_46)[0]
_wire_sk_Sketch59_46 = _wire_sk_Sketch59_46.moved(_inclined_plane_46.location)
_mkf_sk_Sketch59_46 = BRepBuilderAPI_MakeFace(_inclined_plane_46.wrapped, _wire_sk_Sketch59_46.wrapped, True)
_face_sk_Sketch59_46 = Face(_mkf_sk_Sketch59_46.Face())

# 'Sketch60': 8 segments → Line/RadiusArc profile
_inclined_plane_47 = Plane(
    origin=Vector(0.0, 433.9164, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(-0.0, 1.0, 0.0),
)
with BuildSketch(_inclined_plane_47) as sk_Sketch60_47:
    with BuildLine():
        RadiusArc((435.6652, -74.2567), (439.192, -56.0369), -239.2452)
        RadiusArc((439.192, -56.0369), (440.3547, -42.8807), -104.8292)
        Line((440.3547, -42.8807), (400.5543, -38.8299))
        Line((400.5543, -38.8299), (427.375, -87.2297))
        Line((427.375, -87.2297), (427.375, -138.2925))
        Line((427.375, -138.2925), (427.9968, -120.5426))
        RadiusArc((427.9968, -120.5426), (431.8791, -91.1834), 240.0921)
        RadiusArc((431.8791, -91.1834), (435.6652, -74.2567), 568.7541)
    _inc_edges_sk_Sketch60_47 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch60_47 = Wire.combine(_inc_edges_sk_Sketch60_47)[0]
_wire_sk_Sketch60_47 = _wire_sk_Sketch60_47.moved(_inclined_plane_47.location)
_mkf_sk_Sketch60_47 = BRepBuilderAPI_MakeFace(_inclined_plane_47.wrapped, _wire_sk_Sketch60_47.wrapped, True)
_face_sk_Sketch60_47 = Face(_mkf_sk_Sketch60_47.Face())

# 'Sketch62': 5 segments → Line/RadiusArc profile
_inclined_plane_48 = Plane(
    origin=Vector(427.375, 334.4921, 3.8014),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.523843, -0.851815),
)
with BuildSketch(_inclined_plane_48) as sk_Sketch62_48:
    with BuildLine():
        RadiusArc((-19.9071, -41.0502), (0.0, 0.0), -70.7942)
        Line((0.0, 0.0), (42.01, 31.5548))
        Line((42.01, 31.5548), (42.01, -78.0616))
        Line((42.01, -78.0616), (-62.6252, -78.0616))
        Line((-62.6252, -78.0616), (-19.9071, -41.0502))
    _inc_edges_sk_Sketch62_48 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch62_48 = Wire.combine(_inc_edges_sk_Sketch62_48)[0]
_wire_sk_Sketch62_48 = _wire_sk_Sketch62_48.moved(_inclined_plane_48.location)
_mkf_sk_Sketch62_48 = BRepBuilderAPI_MakeFace(_inclined_plane_48.wrapped, _wire_sk_Sketch62_48.wrapped, True)
_face_sk_Sketch62_48 = Face(_mkf_sk_Sketch62_48.Face())

# 'Sketch65': 5 segments → Line/RadiusArc profile
_inclined_plane_49 = Plane(
    origin=Vector(427.375, 348.672, -142.5665),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.523843, 0.851815),
)
with BuildSketch(_inclined_plane_49) as sk_Sketch65_49:
    with BuildLine():
        Line((-19.9278, -41.071), (-60.5265, -63.8133))
        Line((-60.5265, -63.8133), (12.97, -63.8133))
        Line((12.97, -63.8133), (12.97, 7.0412))
        Line((12.97, 7.0412), (0.0, 7.0412))
        RadiusArc((0.0, 7.0412), (-19.9278, -41.071), 68.0432)
    _inc_edges_sk_Sketch65_49 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch65_49 = Wire.combine(_inc_edges_sk_Sketch65_49)[0]
_wire_sk_Sketch65_49 = _wire_sk_Sketch65_49.moved(_inclined_plane_49.location)
_mkf_sk_Sketch65_49 = BRepBuilderAPI_MakeFace(_inclined_plane_49.wrapped, _wire_sk_Sketch65_49.wrapped, True)
_face_sk_Sketch65_49 = Face(_mkf_sk_Sketch65_49.Face())

# New cut profile: plane at y=626.5882 (top face), normal=-Y; cut 100 mm in -Y
_sat_cut_plane = Plane(
    origin=Vector(0.0, 626.5882, 0.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, -1.0, 0.0),
)
with BuildSketch(_sat_cut_plane) as _sk_sat_cut:
    with BuildLine():
        Polyline(
            (696.875,  556.6645),
            (523.7717, 556.6645),
            (523.7717, 334.3887),
            (696.875,  397.3931),
            close=True,
        )
    _sat_cut_edges = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_sat_cut_wire = Wire.combine(_sat_cut_edges)[0]
_sat_cut_wire = _sat_cut_wire.moved(_sat_cut_plane.location)
_sat_cut_mkf = BRepBuilderAPI_MakeFace(_sat_cut_plane.wrapped, _sat_cut_wire.wrapped, True)
_sat_cut_face = Face(_sat_cut_mkf.Face())

# New profile: plane at x=696.875, extrude in +X to x=756.87216758
_sat_new_plane = Plane(
    origin=Vector(696.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_sat_new_plane) as _sk_sat_new:
    with BuildLine():
        Line((666.5882, 385.0058), (666.5882, 472.3468))
        RadiusArc((666.5882, 472.3468), (658.5882, 479.3285), -8.1416)
        Line((658.5882, 479.3285), (596.5883, 479.3285))
        Line((596.5883, 479.3285), (596.5883, 315.0059))
        Line((596.5883, 315.0059), (666.5882, 385.0058))
    _sat_new_edges = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_sat_new_wire = Wire.combine(_sat_new_edges)[0]
_sat_new_wire = _sat_new_wire.moved(_sat_new_plane.location)
_sat_new_mkf = BRepBuilderAPI_MakeFace(_sat_new_plane.wrapped, _sat_new_wire.wrapped, True)
_sat_new_face = Face(_sat_new_mkf.Face())

# Cut profile: plane at x=696.875, cut in +X to x=756.87216758
_sat_cut2_plane = Plane(
    origin=Vector(696.875, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_sat_cut2_plane) as _sk_sat_cut2:
    with BuildLine():
        Line((666.5882, 407.2753), (653.2615, 407.2753))
        Line((653.2615, 407.2753), (640.1655, 394.5399))
        RadiusArc((640.1655, 394.5399), (626.5882, 400.2753), 8.0)
        Line((626.5882, 400.2753), (626.5882, 435.0142))
        RadiusArc((626.5882, 435.0142), (640.1655, 440.7495), 8.0)
        Line((640.1655, 440.7495), (653.2615, 428.0141))
        Line((653.2615, 428.0141), (666.5882, 428.0141))
        Line((666.5882, 428.0141), (666.5882, 407.2753))
    _sat_cut2_edges = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_sat_cut2_wire = Wire.combine(_sat_cut2_edges)[0]
_sat_cut2_wire = _sat_cut2_wire.moved(_sat_cut2_plane.location)
_sat_cut2_mkf = BRepBuilderAPI_MakeFace(_sat_cut2_plane.wrapped, _sat_cut2_wire.wrapped, True)
_sat_cut2_face = Face(_sat_cut2_mkf.Face())

# -- Build --
with BuildPart() as part:
    # --- FEATURE: Extrude1 ---
    # -- Extrude1 --
    _face = _face_sk_Sketch3
    _vec = Vector(1.0, 0.0, 0.0) * -368.5
    _solid = Solid.extrude(_face, _vec)
    add(_solid)
    # Fusion depth expression: -368.500022888 mm
    
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
        _profile_face = sk_Sketch4_1.sketch.faces()[0]
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
            _sweep_shell = Solid.sweep(sk_Sketch4_1.sketch.faces()[0], path_Sweep1)
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
        add(_solid, mode=Mode.SUBTRACT)
    except Exception as _sweep_err:
        print('WARNING: Sweep1 sweep failed:', _sweep_err)
    
    # --- FEATURE: Extrude2 ---
    # -- Extrude2 --
    _face = _face_sk_Sketch6_3
    _vec = Vector(0.0, 0.0, 1.0) * 900.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 900.000000 mm
    
    # --- FEATURE: Extrude3 ---
    # -- Extrude3 --
    _face = _face_sk_Sketch7_4
    _vec = Vector(0.0, -1.0, 0.0) * -800.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -800.000000 mm
    
    # --- FEATURE: Extrude5 ---
    # -- Extrude5_p0 --
    _face = _face_sk_Sketch9_5
    _vec = Vector(0.0, 0.0, 1.0) * -335.4297
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -335.429686012 mm
    
    # -- Extrude5_p1 --
    _face = _face_sk_Sketch9_6
    _vec = Vector(0.0, 0.0, 1.0) * -335.4297
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -335.429686012 mm
    
    # --- FEATURE: Extrude4 ---
    # -- Extrude4 --
    _face = _face_sk_Sketch8_7
    _vec = Vector(-1.0, 0.0, 0.0) * -368.5
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -368.500022888 mm
    
    # --- FEATURE: Extrude6 ---
    # -- Extrude6 --
    _face = _face_sk_Sketch10_8
    _vec = Vector(0.0, 1.0, -0.0) * -400.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -400.000019073 mm
    
    # --- FEATURE: Extrude8 ---
    # -- Extrude8 --
    _face = _face_sk_Sketch14_9
    _vec = Vector(0.0, 0.0, 1.0) * -500.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -500.000000 mm
    
    # --- FEATURE: Extrude9 ---
    # -- Extrude9 --
    _face = _face_sk_Sketch15_10
    _vec = Vector(-1.0, 0.0, 0.0) * 60.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 60.000000 mm
    
    # --- FEATURE: Revolve4 ---
    # -- Revolve4 --
    _custom_axis = Axis(
        Vector(909.6598, 386.5882, 356.6648),
        Vector(1.0, 0.0, 0.0),
    )
    revolve(sk_Sketch23_10.sketch.faces(), axis=_custom_axis, mode=Mode.ADD)
    
    # --- FEATURE: Extrude14 ---
    # -- Extrude14 --
    _face = _face_sk_Sketch25_12
    _vec = Vector(1.0, 0.0, 0.0) * -10.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -10.000000 mm
    
    # --- FEATURE: Extrude15 ---
    # -- Extrude15 --
    _face = _face_sk_Sketch26_13
    _vec = Vector(1.0, 0.0, 0.0) * -10.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -10.000000 mm
    
    # --- FEATURE: Extrude16 ---
    # -- Extrude16 --
    _face = _face_sk_Sketch28_14
    _vec = Vector(1.0, 0.0, 0.0) * -50.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -50.000000 mm
    
    # --- FEATURE: Extrude17 ---
    # -- Extrude17 --
    _face = _face_sk_Sketch27_15
    _vec = Vector(-0.0, 1.0, 0.0) * -300.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -300.000000 mm
    
    # --- FEATURE: Extrude18 ---
    # -- Extrude18 --
    _face = _face_sk_Sketch27_16
    _vec = Vector(-0.0, 1.0, 0.0) * 200.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 200.000000 mm
    
    # --- FEATURE: Extrude19 ---
    # -- Extrude19 --
    _face = _face_sk_Sketch29_17
    _vec = Vector(1.0, 0.0, 0.0) * -200.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -200.000000 mm
    
    # --- FEATURE: Extrude20 ---
    # -- Extrude20 --
    _face = _face_sk_Sketch30_18
    _vec = Vector(1.0, 0.0, 0.0) * -150.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -150.000000 mm
    
    # --- FEATURE: Extrude21 ---
    # -- Extrude21 --
    _face = _face_sk_Sketch31_19
    _vec = Vector(1.0, 0.0, 0.0) * -250.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -250.000000 mm
    
    # --- FEATURE: Extrude22 ---
    # -- Extrude22 --
    _face = _face_sk_Sketch32_20
    _vec = Vector(1.0, 0.0, 0.0) * -130.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -130.000000 mm
    
    # --- FEATURE: Extrude23 ---
    # -- Extrude23 --
    _face = _face_sk_Sketch35_21
    _vec = Vector(1.0, 0.0, 0.0) * -140.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -140.000000 mm
    
    # --- FEATURE: Extrude24 ---
    # -- Extrude24_p0 --
    _face = _face_sk_Sketch36_22
    _vec = Vector(-1.0, 0.0, 0.0) * 140.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 140.000000 mm
    
    # -- Extrude24_p1 --
    _face = _face_sk_Sketch36_23
    _vec = Vector(-1.0, 0.0, 0.0) * 140.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 140.000000 mm
    
    # -- Extrude24_p2 --
    _face = _face_sk_Sketch36_24
    _vec = Vector(-1.0, 0.0, 0.0) * 140.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 140.000000 mm
    
    # -- Extrude24_p3 --
    _face = _face_sk_Sketch36_25
    _vec = Vector(-1.0, 0.0, 0.0) * 140.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 140.000000 mm
    
    # --- FEATURE: Extrude25 ---
    # -- Extrude25 --
    extrude(sk_Sketch37_26.sketch, amount=20.0, taper=-45.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: 20.000000 mm
    # Fusion taper angle expression: 45.0 deg
    
    # --- FEATURE: Extrude26 ---
    # -- Extrude26 --
    _face = _face_sk_Sketch38_27
    _vec = Vector(0.0, -1.0, 0.0) * 50.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 50.000000 mm
    
    # --- FEATURE: Sweep3 ---
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
        _profile_face = sk_Sketch42_27.sketch.faces()[0]
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
            _sweep_shell = Solid.sweep(sk_Sketch42_27.sketch.faces()[0], path_Sweep3)
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
    
    # --- FEATURE: Sweep4 ---
    # -- Sweep4 --
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
        _profile_face = sk_Sketch46_28.sketch.faces()[0]
        _occ_wire = None
        _wire_exp = TopExp_Explorer(_profile_face.wrapped, TopAbs_WIRE)
        if _wire_exp.More():
            _occ_wire = TopoDS.Wire_s(_wire_exp.Current())
        _path_wire = path_Sweep4
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
            _sweep_shell = Solid.sweep(sk_Sketch46_28.sketch.faces()[0], path_Sweep4)
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
                print('WARNING: Sweep4 sweep — all solid attempts failed, result is Shell')
        add(_solid, mode=Mode.SUBTRACT)
    except Exception as _sweep_err:
        print('WARNING: Sweep4 sweep failed:', _sweep_err)
    
    # --- FEATURE: Extrude27 ---
    # -- Extrude27 --
    extrude(sk_Sketch48_30.sketch, amount=-275.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -275.000000 mm
    
    # --- FEATURE: Extrude28 ---
    # -- Extrude28_p0 --
    _face = _face_sk_Sketch49_31
    _vec = Vector(-0.0, -1.0, -0.0) * 125.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 125.000000 mm
    
    # -- Extrude28_p1 --
    _face = _face_sk_Sketch49_32
    _vec = Vector(-0.0, -1.0, -0.0) * 125.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 125.000000 mm
    
    # -- Extrude28_p2 --
    _face = _face_sk_Sketch49_33
    _vec = Vector(-0.0, -1.0, -0.0) * 125.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 125.000000 mm
    
    # --- FEATURE: Extrude29 ---
    # -- Extrude29_p0 --
    _face = _face_sk_Sketch50_34
    _vec = Vector(-0.0, -1.0, -0.0) * -25.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -25.000000 mm
    
    # -- Extrude29_p1 --
    _face = _face_sk_Sketch50_35
    _vec = Vector(-0.0, -1.0, -0.0) * -25.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -25.000000 mm
    
    # -- Extrude29_p2 --
    _face = _face_sk_Sketch50_36
    _vec = Vector(-0.0, -1.0, -0.0) * -25.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -25.000000 mm
    
    # --- FEATURE: Extrude30 ---
    # -- Extrude30_p0 --
    _face = _face_sk_Sketch52_37
    _vec = Vector(-0.0, 1.0, 0.0) * 200.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 200.000000 mm
    
    # -- Extrude30_p1 --
    _face = _face_sk_Sketch52_38
    _vec = Vector(-0.0, 1.0, 0.0) * 200.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 200.000000 mm
    
    # -- Extrude30_p2 --
    _face = _face_sk_Sketch52_39
    _vec = Vector(-0.0, 1.0, 0.0) * 200.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 200.000000 mm
    
    # --- FEATURE: Extrude31 ---
    # -- Extrude31_p0 --
    _face = _face_sk_Sketch53_40
    _vec = Vector(-0.0, 1.0, 0.0) * -30.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -30.000000 mm
    
    # -- Extrude31_p1 --
    _face = _face_sk_Sketch53_41
    _vec = Vector(-0.0, 1.0, 0.0) * -30.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -30.000000 mm
    
    # -- Extrude31_p2 --
    _face = _face_sk_Sketch53_42
    _vec = Vector(-0.0, 1.0, 0.0) * -30.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -30.000000 mm
    
    # --- FEATURE: Extrude32 ---
    # -- Extrude32 --
    extrude(sk_Sketch54_43.sketch, amount=310.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: 310.000000 mm
    
    # --- FEATURE: Extrude33 ---
    # -- Extrude33 --
    _face = _face_sk_Sketch56_44
    _vec = Vector(0.0, 0.0, 1.0) * -800.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -800.000000 mm
    
    # --- FEATURE: Extrude34 ---
    # -- Extrude34 --
    _face = _face_sk_Sketch57_45
    _vec = Vector(0.0, 0.0, 1.0) * -700.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -700.000000 mm
    
    # --- FEATURE: Extrude35 ---
    # -- Extrude35 --
    _face = _face_sk_Sketch59_46
    _vec = Vector(-0.0, -1.0, -0.0) * 170.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 170.000000 mm
    
    # --- FEATURE: Extrude36 ---
    # -- Extrude36 --
    _face = _face_sk_Sketch60_47
    _vec = Vector(-0.0, 1.0, 0.0) * 290.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 290.000000 mm
    
    # --- FEATURE: Extrude37 ---
    # -- Extrude37 --
    _face = _face_sk_Sketch62_48
    _vec = Vector(0.0, 0.523843, -0.851815) * -640.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -640.000000 mm
    
    # --- FEATURE: Extrude38 ---
    # -- Extrude38 --
    _face = _face_sk_Sketch65_49
    _vec = Vector(0.0, 0.523843, 0.851815) * 575.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 575.000000 mm

    # New cut: extrude 100 mm in -Y from y=626.5882
    _sat_cut_solid = Solid.extrude(_sat_cut_face, Vector(0.0, -1.0, 0.0) * 100.0)
    add(_sat_cut_solid, mode=Mode.SUBTRACT)

    # New extrude: plane at x=696.875, extrude +X to x=756.87216758
    _sat_new_solid = Solid.extrude(_sat_new_face, Vector(1.0, 0.0, 0.0) * (756.87216758 - 696.875))
    add(_sat_new_solid, mode=Mode.ADD)

    # New cut: plane at x=696.875, cut +X to x=756.87216758
    _sat_cut2_solid = Solid.extrude(_sat_cut2_face, Vector(1.0, 0.0, 0.0) * (756.87216758 - 696.875))
    add(_sat_cut2_solid, mode=Mode.SUBTRACT)

# -- Export --
export_step(part.part, 'sat.step')
# export_stl(part.part,  'fusion_features.stl')
if _has_ocp: show(part)
