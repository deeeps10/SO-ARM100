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

# 'Sketch1': circle on inclined plane
_inclined_plane_1 = Plane(
    origin=Vector(0.0, 0.0, 0.284),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch1:
    with Locations((-0.0, -0.452)):
        Circle(radius=0.1)

# 'Sketch3': circle on inclined plane
_inclined_plane_2 = Plane(
    origin=Vector(0.0, 0.0, 0.284),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_2) as sk_Sketch3_2:
    with Locations((0.0495, -0.5015)):
        Circle(radius=0.0125)

# 'Sketch3': circle on inclined plane
_inclined_plane_3 = Plane(
    origin=Vector(0.0, 0.0, 0.284),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_3) as sk_Sketch3_3:
    with Locations((-0.0495, -0.5015)):
        Circle(radius=0.0125)

# 'Sketch3': circle on inclined plane
_inclined_plane_4 = Plane(
    origin=Vector(0.0, 0.0, 0.284),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch3_4:
    with Locations((-0.0495, -0.4025)):
        Circle(radius=0.0125)

# 'Sketch3': circle on inclined plane
_inclined_plane_5 = Plane(
    origin=Vector(0.0, 0.0, 0.284),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch3_5:
    with Locations((0.0495, -0.4025)):
        Circle(radius=0.0125)

# 'Sketch4': circle on inclined plane
_inclined_plane_6 = Plane(
    origin=Vector(0.0, 0.0, 0.284),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_6) as sk_Sketch4_6:
    with Locations((0.0, -0.452)):
        Circle(radius=0.03)

# 'Sketch5': circle on inclined plane
_inclined_plane_7 = Plane(
    origin=Vector(0.0, 0.0, 0.317),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_7) as sk_Sketch5_7:
    with Locations((0.0, 0.452)):
        Circle(radius=0.03)

# 'Sketch6': circle on inclined plane
_inclined_plane_8 = Plane(
    origin=Vector(0.0, 0.0, 0.278),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_8) as sk_Sketch6_8:
    with Locations((-0.0, 0.452)):
        Circle(radius=0.0125)

# 'Sketch8': 8 segments → Line/RadiusArc profile
_inclined_plane_9 = Plane(
    origin=Vector(0.0, 0.0, 0.317),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_9) as sk_Sketch8_9:
    with BuildLine():
        Line((0.124, 0.1), (-0.124, 0.1))
        Line((-0.124, 0.1), (0.124, 0.1))
        Line((0.124, 0.1), (-0.124, 0.1))
        Line((-0.124, 0.1), (-0.124, 0.524))
        Line((-0.124, 0.524), (-0.094, 0.554))
        Line((-0.094, 0.554), (0.094, 0.554))
        Line((0.094, 0.554), (0.124, 0.524))
        Line((0.124, 0.524), (0.124, 0.1))
    _inc_edges_sk_Sketch8_9 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch8_9 = Wire.combine(_inc_edges_sk_Sketch8_9)[0]
_wire_sk_Sketch8_9 = _wire_sk_Sketch8_9.moved(_inclined_plane_9.location)
_mkf_sk_Sketch8_9 = BRepBuilderAPI_MakeFace(_inclined_plane_9.wrapped, _wire_sk_Sketch8_9.wrapped, True)
_face_sk_Sketch8_9 = Face(_mkf_sk_Sketch8_9.Face())

# 'Sketch10': circle on inclined plane
_inclined_plane_10 = Plane(
    origin=Vector(0.0, 0.0, 0.648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_10) as sk_Sketch10_10:
    with Locations((-0.0, 0.452)):
        Circle(radius=0.1)

# 'Sketch11': circle on inclined plane
_inclined_plane_11 = Plane(
    origin=Vector(0.0, 0.0, 0.623),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_11) as sk_Sketch11_11:
    with Locations((0.0, 0.452)):
        Circle(radius=0.045)

# 'Sketch12': circle on inclined plane
_inclined_plane_12 = Plane(
    origin=Vector(0.0, 0.0, 0.608),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_12) as sk_Sketch12_12:
    with Locations((0.0, 0.452)):
        Circle(radius=0.024)

# 'Sketch17': 10 segments → Line/RadiusArc profile
_inclined_plane_13 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_13) as sk_Sketch17_13:
    with BuildLine():
        Line((-0.12, 0.399), (-0.12, 0.1211))
        Line((-0.12, 0.1211), (-0.12, 0.104))
        Line((-0.12, 0.104), (-0.1029, 0.104))
        Line((-0.1029, 0.104), (0.1029, 0.104))
        Line((0.1029, 0.104), (0.12, 0.104))
        Line((0.12, 0.104), (0.12, 0.1211))
        Line((0.12, 0.1211), (0.12, 0.399))
        Line((0.12, 0.399), (0.0964, 0.399))
        RadiusArc((0.0964, 0.399), (-0.0964, 0.399), 0.1101)
        Line((-0.0964, 0.399), (-0.12, 0.399))
    _inc_edges_sk_Sketch17_13 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch17_13 = Wire.combine(_inc_edges_sk_Sketch17_13)[0]
_wire_sk_Sketch17_13 = _wire_sk_Sketch17_13.moved(_inclined_plane_13.location)
_mkf_sk_Sketch17_13 = BRepBuilderAPI_MakeFace(_inclined_plane_13.wrapped, _wire_sk_Sketch17_13.wrapped, True)
_face_sk_Sketch17_13 = Face(_mkf_sk_Sketch17_13.Face())

_solid_sk_Sketch17_13 = extrude(_face_sk_Sketch17_13, amount=-0.015, dir=Vector(0.0, 0.0, -1.0), taper=-15.0).solid()

# 'Sketch18': 8 segments → Line/RadiusArc profile
_inclined_plane_14 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_14) as sk_Sketch18_14:
    with BuildLine():
        Line((-0.065, 0.3365), (-0.101, 0.3365))
        Line((-0.101, 0.3365), (-0.101, 0.2865))
        Line((-0.101, 0.2865), (0.101, 0.2865))
        Line((0.101, 0.2865), (0.101, 0.3365))
        Line((0.101, 0.3365), (0.065, 0.3365))
        Line((0.065, 0.3365), (0.065, 0.3715))
        RadiusArc((0.065, 0.3715), (-0.065, 0.3715), 0.1101)
        Line((-0.065, 0.3715), (-0.065, 0.3365))
    _inc_edges_sk_Sketch18_14 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch18_14 = Wire.combine(_inc_edges_sk_Sketch18_14)[0]
_wire_sk_Sketch18_14 = _wire_sk_Sketch18_14.moved(_inclined_plane_14.location)
_mkf_sk_Sketch18_14 = BRepBuilderAPI_MakeFace(_inclined_plane_14.wrapped, _wire_sk_Sketch18_14.wrapped, True)
_face_sk_Sketch18_14 = Face(_mkf_sk_Sketch18_14.Face())

# 'Sketch9': circle on inclined plane
_inclined_plane_15 = Plane(
    origin=Vector(0.0, 0.0, 0.267),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_15) as sk_Sketch9_15:
    with Locations((-0.076, 0.3115)):
        Circle(radius=0.01)

# 'Sketch9': circle on inclined plane
_inclined_plane_16 = Plane(
    origin=Vector(0.0, 0.0, 0.267),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_16) as sk_Sketch9_16:
    with Locations((-0.052, 0.3115)):
        Circle(radius=0.01)

# 'Sketch9': circle on inclined plane
_inclined_plane_17 = Plane(
    origin=Vector(0.0, 0.0, 0.267),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_17) as sk_Sketch9_17:
    with Locations((-0.028, 0.3115)):
        Circle(radius=0.01)

# 'Sketch9': circle on inclined plane
_inclined_plane_18 = Plane(
    origin=Vector(0.0, 0.0, 0.267),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_18) as sk_Sketch9_18:
    with Locations((0.028, 0.3115)):
        Circle(radius=0.01)

# 'Sketch9': circle on inclined plane
_inclined_plane_19 = Plane(
    origin=Vector(0.0, 0.0, 0.267),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_19) as sk_Sketch9_19:
    with Locations((0.052, 0.3115)):
        Circle(radius=0.01)

# 'Sketch9': circle on inclined plane
_inclined_plane_20 = Plane(
    origin=Vector(0.0, 0.0, 0.267),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_20) as sk_Sketch9_20:
    with Locations((0.076, 0.3115)):
        Circle(radius=0.01)

# 'Sketch19': 4 segments → Line/RadiusArc profile
_inclined_plane_21 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_21) as sk_Sketch19_21:
    with BuildLine():
        Line((0.1408, 0.4222), (0.1578, 0.3998))
        Line((0.1578, 0.3998), (0.0917, 0.399))
        Line((0.0917, 0.399), (0.1057, 0.4222))
        Line((0.1057, 0.4222), (0.1408, 0.4222))
    _inc_edges_sk_Sketch19_21 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch19_21 = Wire.combine(_inc_edges_sk_Sketch19_21)[0]
_wire_sk_Sketch19_21 = _wire_sk_Sketch19_21.moved(_inclined_plane_21.location)
_mkf_sk_Sketch19_21 = BRepBuilderAPI_MakeFace(_inclined_plane_21.wrapped, _wire_sk_Sketch19_21.wrapped, True)
_face_sk_Sketch19_21 = Face(_mkf_sk_Sketch19_21.Face())

# 'Sketch19': 4 segments → Line/RadiusArc profile
_inclined_plane_22 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_22) as sk_Sketch19_22:
    with BuildLine():
        Line((-0.1356, 0.4152), (-0.1427, 0.399))
        Line((-0.1427, 0.399), (-0.0892, 0.399))
        Line((-0.0892, 0.399), (-0.098, 0.4152))
        Line((-0.098, 0.4152), (-0.1356, 0.4152))
    _inc_edges_sk_Sketch19_22 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch19_22 = Wire.combine(_inc_edges_sk_Sketch19_22)[0]
_wire_sk_Sketch19_22 = _wire_sk_Sketch19_22.moved(_inclined_plane_22.location)
_mkf_sk_Sketch19_22 = BRepBuilderAPI_MakeFace(_inclined_plane_22.wrapped, _wire_sk_Sketch19_22.wrapped, True)
_face_sk_Sketch19_22 = Face(_mkf_sk_Sketch19_22.Face())

# 'Sketch26': circle on inclined plane
_inclined_plane_23 = Plane(
    origin=Vector(0.0, 0.0, 0.648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_23) as sk_Sketch26_23:
    with Locations((-0.0495, 0.5015)):
        Circle(radius=0.0125)

# 'Sketch26': circle on inclined plane
_inclined_plane_24 = Plane(
    origin=Vector(0.0, 0.0, 0.648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_24) as sk_Sketch26_24:
    with Locations((0.0495, 0.5015)):
        Circle(radius=0.0125)

# 'Sketch26': circle on inclined plane
_inclined_plane_25 = Plane(
    origin=Vector(0.0, 0.0, 0.648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_25) as sk_Sketch26_25:
    with Locations((0.0495, 0.4025)):
        Circle(radius=0.0125)

# 'Sketch26': circle on inclined plane
_inclined_plane_26 = Plane(
    origin=Vector(0.0, 0.0, 0.648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_26) as sk_Sketch26_26:
    with Locations((-0.0495, 0.4025)):
        Circle(radius=0.0125)

# 'Sketch34': 6 segments → Line/RadiusArc profile
_inclined_plane_27 = Plane(
    origin=Vector(0.0, 0.0, 0.605),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_27) as sk_Sketch34_27:
    with BuildLine():
        Line((-0.124, 0.399), (-0.124, 0.1))
        Line((-0.124, 0.1), (0.124, 0.1))
        Line((0.124, 0.1), (0.124, 0.399))
        Line((0.124, 0.399), (0.0918, 0.399))
        RadiusArc((0.0918, 0.399), (-0.0918, 0.399), 0.106)
        Line((-0.0918, 0.399), (-0.124, 0.399))
    _inc_edges_sk_Sketch34_27 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch34_27 = Wire.combine(_inc_edges_sk_Sketch34_27)[0]
_wire_sk_Sketch34_27 = _wire_sk_Sketch34_27.moved(_inclined_plane_27.location)
_mkf_sk_Sketch34_27 = BRepBuilderAPI_MakeFace(_inclined_plane_27.wrapped, _wire_sk_Sketch34_27.wrapped, True)
_face_sk_Sketch34_27 = Face(_mkf_sk_Sketch34_27.Face())

_solid_sk_Sketch34_27 = extrude(_face_sk_Sketch34_27, amount=0.026, dir=Vector(0.0, 0.0, 1.0), taper=15.0).solid()

# 'Sketch35': 5 segments → Line/RadiusArc profile
_inclined_plane_28 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_28) as sk_Sketch35_28:
    with BuildLine():
        Line((0.1032, 0.4245), (0.07, 0.3751))
        Line((0.07, 0.3751), (0.07, 0.0825))
        Line((0.07, 0.0825), (0.152, 0.0825))
        Line((0.152, 0.0825), (0.152, 0.4245))
        Line((0.152, 0.4245), (0.1032, 0.4245))
    _inc_edges_sk_Sketch35_28 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch35_28 = Wire.combine(_inc_edges_sk_Sketch35_28)[0]
_wire_sk_Sketch35_28 = _wire_sk_Sketch35_28.moved(_inclined_plane_28.location)
_mkf_sk_Sketch35_28 = BRepBuilderAPI_MakeFace(_inclined_plane_28.wrapped, _wire_sk_Sketch35_28.wrapped, True)
_face_sk_Sketch35_28 = Face(_mkf_sk_Sketch35_28.Face())

# 'Sketch35': 5 segments → Line/RadiusArc profile
_inclined_plane_29 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_29) as sk_Sketch35_29:
    with BuildLine():
        Line((-0.1032, 0.4245), (-0.07, 0.3751))
        Line((-0.07, 0.3751), (-0.07, 0.0825))
        Line((-0.07, 0.0825), (-0.152, 0.0825))
        Line((-0.152, 0.0825), (-0.152, 0.4245))
        Line((-0.152, 0.4245), (-0.1032, 0.4245))
    _inc_edges_sk_Sketch35_29 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch35_29 = Wire.combine(_inc_edges_sk_Sketch35_29)[0]
_wire_sk_Sketch35_29 = _wire_sk_Sketch35_29.moved(_inclined_plane_29.location)
_mkf_sk_Sketch35_29 = BRepBuilderAPI_MakeFace(_inclined_plane_29.wrapped, _wire_sk_Sketch35_29.wrapped, True)
_face_sk_Sketch35_29 = Face(_mkf_sk_Sketch35_29.Face())

# 'Sketch36': 6 segments → Line/RadiusArc profile
_inclined_plane_30 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_30) as sk_Sketch36_30:
    with BuildLine():
        Line((-0.1318, 0.14), (-0.1318, 0.0872))
        Line((-0.1318, 0.0872), (-0.084, 0.0872))
        Line((-0.084, 0.0872), (-0.084, 0.1))
        Line((-0.084, 0.1), (-0.084, 0.12))
        Line((-0.084, 0.12), (-0.104, 0.14))
        Line((-0.104, 0.14), (-0.1318, 0.14))
    _inc_edges_sk_Sketch36_30 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch36_30 = Wire.combine(_inc_edges_sk_Sketch36_30)[0]
_wire_sk_Sketch36_30 = _wire_sk_Sketch36_30.moved(_inclined_plane_30.location)
_mkf_sk_Sketch36_30 = BRepBuilderAPI_MakeFace(_inclined_plane_30.wrapped, _wire_sk_Sketch36_30.wrapped, True)
_face_sk_Sketch36_30 = Face(_mkf_sk_Sketch36_30.Face())

# 'Sketch36': 6 segments → Line/RadiusArc profile
_inclined_plane_31 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_31) as sk_Sketch36_31:
    with BuildLine():
        Line((0.1318, 0.14), (0.104, 0.14))
        Line((0.104, 0.14), (0.084, 0.12))
        Line((0.084, 0.12), (0.084, 0.1))
        Line((0.084, 0.1), (0.084, 0.0872))
        Line((0.084, 0.0872), (0.1318, 0.0872))
        Line((0.1318, 0.0872), (0.1318, 0.14))
    _inc_edges_sk_Sketch36_31 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch36_31 = Wire.combine(_inc_edges_sk_Sketch36_31)[0]
_wire_sk_Sketch36_31 = _wire_sk_Sketch36_31.moved(_inclined_plane_31.location)
_mkf_sk_Sketch36_31 = BRepBuilderAPI_MakeFace(_inclined_plane_31.wrapped, _wire_sk_Sketch36_31.wrapped, True)
_face_sk_Sketch36_31 = Face(_mkf_sk_Sketch36_31.Face())

# 'Sketch39': circle on inclined plane
_inclined_plane_32 = Plane(
    origin=Vector(0.0, 0.0, 0.631),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_32) as sk_Sketch39_32:
    with Locations((-0.104, 0.12)):
        Circle(radius=0.02)

# 'Sketch39': circle on inclined plane
_inclined_plane_33 = Plane(
    origin=Vector(0.0, 0.0, 0.631),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_33) as sk_Sketch39_33:
    with Locations((0.104, 0.12)):
        Circle(radius=0.02)

# 'Sketch40': circle on inclined plane
_inclined_plane_34 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_34) as sk_Sketch40_34:
    with Locations((0.1025, 0.162)):
        Circle(radius=0.021)

# 'Sketch40': circle on inclined plane
_inclined_plane_35 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_35) as sk_Sketch40_35:
    with Locations((-0.1025, 0.162)):
        Circle(radius=0.021)

# 'Sketch40': circle on inclined plane
_inclined_plane_36 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_36) as sk_Sketch40_36:
    with Locations((-0.1025, 0.369)):
        Circle(radius=0.021)

# 'Sketch40': circle on inclined plane
_inclined_plane_37 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_37) as sk_Sketch40_37:
    with Locations((0.1025, 0.369)):
        Circle(radius=0.021)

# 'Sketch38': circle on inclined plane
_inclined_plane_38 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_38) as sk_Sketch38_38:
    with Locations((-0.1025, 0.369)):
        Circle(radius=0.0075)

# 'Sketch38': circle on inclined plane
_inclined_plane_39 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_39) as sk_Sketch38_39:
    with Locations((0.1025, 0.369)):
        Circle(radius=0.0075)

# 'Sketch38': circle on inclined plane
_inclined_plane_40 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_40) as sk_Sketch38_40:
    with Locations((-0.1025, 0.162)):
        Circle(radius=0.0075)

# 'Sketch38': circle on inclined plane
_inclined_plane_41 = Plane(
    origin=Vector(0.0, 0.0, 0.62),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_41) as sk_Sketch38_41:
    with Locations((0.1025, 0.162)):
        Circle(radius=0.0075)

# 'Sketch45': 5 segments → Line/RadiusArc profile
_inclined_plane_42 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_42) as sk_Sketch45_42:
    with BuildLine():
        Line((-0.12, 0.1356), (-0.2188, 0.1356))
        Line((-0.2188, 0.1356), (-0.2188, 0.0403))
        Line((-0.2188, 0.0403), (-0.096, 0.0403))
        Line((-0.096, 0.0403), (-0.096, 0.104))
        RadiusArc((-0.096, 0.104), (-0.12, 0.1356), 0.021)
    _inc_edges_sk_Sketch45_42 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch45_42 = Wire.combine(_inc_edges_sk_Sketch45_42)[0]
_wire_sk_Sketch45_42 = _wire_sk_Sketch45_42.moved(_inclined_plane_42.location)
_mkf_sk_Sketch45_42 = BRepBuilderAPI_MakeFace(_inclined_plane_42.wrapped, _wire_sk_Sketch45_42.wrapped, True)
_face_sk_Sketch45_42 = Face(_mkf_sk_Sketch45_42.Face())

_solid_sk_Sketch45_42 = extrude(_face_sk_Sketch45_42, amount=-0.015, dir=Vector(0.0, 0.0, -1.0), taper=15.0).solid()

# 'Sketch45': 5 segments → Line/RadiusArc profile
_inclined_plane_43 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_43) as sk_Sketch45_43:
    with BuildLine():
        Line((0.096, 0.0403), (0.2188, 0.0403))
        Line((0.2188, 0.0403), (0.2188, 0.1356))
        Line((0.2188, 0.1356), (0.12, 0.1356))
        RadiusArc((0.12, 0.1356), (0.096, 0.104), 0.021)
        Line((0.096, 0.104), (0.096, 0.0403))
    _inc_edges_sk_Sketch45_43 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch45_43 = Wire.combine(_inc_edges_sk_Sketch45_43)[0]
_wire_sk_Sketch45_43 = _wire_sk_Sketch45_43.moved(_inclined_plane_43.location)
_mkf_sk_Sketch45_43 = BRepBuilderAPI_MakeFace(_inclined_plane_43.wrapped, _wire_sk_Sketch45_43.wrapped, True)
_face_sk_Sketch45_43 = Face(_mkf_sk_Sketch45_43.Face())

_solid_sk_Sketch45_43 = extrude(_face_sk_Sketch45_43, amount=-0.015, dir=Vector(0.0, 0.0, -1.0), taper=15.0).solid()

# 'Sketch42': circle on inclined plane
_inclined_plane_44 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_44) as sk_Sketch42_44:
    with Locations((-0.1025, 0.369)):
        Circle(radius=0.021)

# 'Sketch42': circle on inclined plane
_inclined_plane_45 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_45) as sk_Sketch42_45:
    with Locations((0.1025, 0.369)):
        Circle(radius=0.021)

# 'Sketch42': circle on inclined plane
_inclined_plane_46 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_46) as sk_Sketch42_46:
    with Locations((-0.1025, 0.124)):
        Circle(radius=0.021)

# 'Sketch42': circle on inclined plane
_inclined_plane_47 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_47) as sk_Sketch42_47:
    with Locations((0.1025, 0.124)):
        Circle(radius=0.021)

# 'Sketch41': circle on inclined plane
_inclined_plane_48 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_48) as sk_Sketch41_48:
    with Locations((0.1025, 0.124)):
        Circle(radius=0.0075)

# 'Sketch41': circle on inclined plane
_inclined_plane_49 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_49) as sk_Sketch41_49:
    with Locations((-0.1025, 0.124)):
        Circle(radius=0.0075)

# 'Sketch41': circle on inclined plane
_inclined_plane_50 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_50) as sk_Sketch41_50:
    with Locations((-0.1025, 0.369)):
        Circle(radius=0.0075)

# 'Sketch41': circle on inclined plane
_inclined_plane_51 = Plane(
    origin=Vector(0.0, 0.0, 0.302),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, -1.0),
)
with BuildSketch(_inclined_plane_51) as sk_Sketch41_51:
    with Locations((0.1025, 0.369)):
        Circle(radius=0.0075)

# 'Sketch43': 4 segments → Line/RadiusArc profile
_inclined_plane_52 = Plane(
    origin=Vector(0.092, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_inclined_plane_52) as sk_Sketch43_52:
    with BuildLine():
        Line((-0.253, 0.284), (-0.2865, 0.302))
        Line((-0.2865, 0.302), (-0.153, 0.302))
        Line((-0.153, 0.302), (-0.153, 0.284))
        Line((-0.153, 0.284), (-0.253, 0.284))
    _inc_edges_sk_Sketch43_52 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch43_52 = Wire.combine(_inc_edges_sk_Sketch43_52)[0]
_wire_sk_Sketch43_52 = _wire_sk_Sketch43_52.moved(_inclined_plane_52.location)
_mkf_sk_Sketch43_52 = BRepBuilderAPI_MakeFace(_inclined_plane_52.wrapped, _wire_sk_Sketch43_52.wrapped, True)
_face_sk_Sketch43_52 = Face(_mkf_sk_Sketch43_52.Face())

# 'Sketch48': circle on inclined plane
_inclined_plane_53 = Plane(
    origin=Vector(0.0, 0.0, 0.605),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_53) as sk_Sketch48_53:
    with Locations((-0.1025, 0.12)):
        Circle(radius=0.0175)

# 'Sketch48': circle on inclined plane
_inclined_plane_54 = Plane(
    origin=Vector(0.0, 0.0, 0.605),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_54) as sk_Sketch48_54:
    with Locations((0.1025, 0.12)):
        Circle(radius=0.0175)

# 'Sketch49': circle on inclined plane
_inclined_plane_55 = Plane(
    origin=Vector(0.0, 0.0, 0.613),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_55) as sk_Sketch49_55:
    with Locations((-0.1025, 0.12)):
        Circle(radius=0.0175)

# 'Sketch49': circle on inclined plane
_inclined_plane_56 = Plane(
    origin=Vector(0.0, 0.0, 0.613),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_56) as sk_Sketch49_56:
    with Locations((0.1025, 0.12)):
        Circle(radius=0.0175)

# 'Sketch50': circle on inclined plane
_inclined_plane_57 = Plane(
    origin=Vector(0.0, 0.0, 0.616),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_57) as sk_Sketch50_57:
    with Locations((-0.1025, 0.12)):
        Circle(radius=0.0167)

# 'Sketch50': circle on inclined plane
_inclined_plane_58 = Plane(
    origin=Vector(0.0, 0.0, 0.616),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_58) as sk_Sketch50_58:
    with Locations((0.1025, 0.12)):
        Circle(radius=0.0167)

# 'Sketch51': circle on inclined plane
_inclined_plane_59 = Plane(
    origin=Vector(0.0, 0.0, 0.6182),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_59) as sk_Sketch51_59:
    with Locations((-0.1025, 0.12)):
        Circle(radius=0.0147)

# 'Sketch51': circle on inclined plane
_inclined_plane_60 = Plane(
    origin=Vector(0.0, 0.0, 0.6182),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_60) as sk_Sketch51_60:
    with Locations((0.1025, 0.12)):
        Circle(radius=0.0147)

# 'Sketch54': circle on inclined plane
_inclined_plane_61 = Plane(
    origin=Vector(0.0, 0.0, 0.648),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_61) as sk_Sketch54_61:
    with Locations((-0.0, 0.452)):
        Circle(radius=0.0269)

# 'Sketch55': circle on inclined plane
_inclined_plane_62 = Plane(
    origin=Vector(0.0, 0.0, 0.6524),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_62) as sk_Sketch55_62:
    with Locations((-0.0, 0.452)):
        Circle(radius=0.0269)

# 'Sketch56': circle on inclined plane
_inclined_plane_63 = Plane(
    origin=Vector(0.0, 0.0, 0.6582),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_63) as sk_Sketch56_63:
    with Locations((-0.0, 0.452)):
        Circle(radius=0.0259)

# 'Sketch57': circle on inclined plane
_inclined_plane_64 = Plane(
    origin=Vector(0.0, 0.0, 0.6593),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_64) as sk_Sketch57_64:
    with Locations((-0.0, 0.452)):
        Circle(radius=0.0255)

# 'Sketch59': circle on inclined plane
_inclined_plane_65 = Plane(
    origin=Vector(0.0, 0.0, 0.6616),
    x_dir=Vector(-1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_65) as sk_Sketch59_65:
    with Locations((-0.0, 0.452)):
        Circle(radius=0.0233)

# 'CustomCut1': 12-point polygon profile, cut from z=0.613 to z=1.0
_inclined_plane_custom1 = Plane(
    origin=Vector(0.0, 0.0, 0.613),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_custom1) as sk_CustomCut1:
    with BuildLine():
        Line((0.105, -0.1225), (0.105, -0.132))
        Line((0.105, -0.132), (0.1, -0.132))
        Line((0.1, -0.132), (0.1, -0.1225))
        Line((0.1, -0.1225), (0.0905, -0.1225))
        Line((0.0905, -0.1225), (0.0905, -0.1175))
        Line((0.0905, -0.1175), (0.1, -0.1175))
        Line((0.1, -0.1175), (0.1, -0.108))
        Line((0.1, -0.108), (0.105, -0.108))
        Line((0.105, -0.108), (0.105, -0.1175))
        Line((0.105, -0.1175), (0.1145, -0.1175))
        Line((0.1145, -0.1175), (0.1145, -0.1225))
        Line((0.1145, -0.1225), (0.105, -0.1225))
    _inc_edges_custom1 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_custom1 = Wire.combine(_inc_edges_custom1)[0]
_wire_custom1 = _wire_custom1.moved(_inclined_plane_custom1.location)
_mkf_custom1 = BRepBuilderAPI_MakeFace(_inclined_plane_custom1.wrapped, _wire_custom1.wrapped, True)
_face_custom1 = Face(_mkf_custom1.Face())

# 'CustomCut2': same profile shifted so first point is at (-0.1, -0.1225, 0.613)
_inclined_plane_custom2 = Plane(
    origin=Vector(0.0, 0.0, 0.613),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_custom2) as sk_CustomCut2:
    with BuildLine():
        Line((-0.1, -0.1225), (-0.1, -0.132))
        Line((-0.1, -0.132), (-0.105, -0.132))
        Line((-0.105, -0.132), (-0.105, -0.1225))
        Line((-0.105, -0.1225), (-0.1145, -0.1225))
        Line((-0.1145, -0.1225), (-0.1145, -0.1175))
        Line((-0.1145, -0.1175), (-0.105, -0.1175))
        Line((-0.105, -0.1175), (-0.105, -0.108))
        Line((-0.105, -0.108), (-0.1, -0.108))
        Line((-0.1, -0.108), (-0.1, -0.1175))
        Line((-0.1, -0.1175), (-0.0905, -0.1175))
        Line((-0.0905, -0.1175), (-0.0905, -0.1225))
        Line((-0.0905, -0.1225), (-0.1, -0.1225))
    _inc_edges_custom2 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_custom2 = Wire.combine(_inc_edges_custom2)[0]
_wire_custom2 = _wire_custom2.moved(_inclined_plane_custom2.location)
_mkf_custom2 = BRepBuilderAPI_MakeFace(_inclined_plane_custom2.wrapped, _wire_custom2.wrapped, True)
_face_custom2 = Face(_mkf_custom2.Face())

# 'CustomCut3': 12-point polygon at z=0.663, cut down to z=0.65899998
_inclined_plane_custom3 = Plane(
    origin=Vector(0.0, 0.0, 0.663),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_custom3) as sk_CustomCut3:
    with BuildLine():
        Line((-0.0045, -0.4356), (0.0045, -0.4356))
        Line((0.0045, -0.4356), (0.0045, -0.4475))
        Line((0.0045, -0.4475), (0.0164, -0.4475))
        Line((0.0164, -0.4475), (0.0164, -0.4565))
        Line((0.0164, -0.4565), (0.0045, -0.4565))
        Line((0.0045, -0.4565), (0.0045, -0.4684))
        Line((0.0045, -0.4684), (-0.0045, -0.4684))
        Line((-0.0045, -0.4684), (-0.0045, -0.4565))
        Line((-0.0045, -0.4565), (-0.0164, -0.4565))
        Line((-0.0164, -0.4565), (-0.0164, -0.4475))
        Line((-0.0164, -0.4475), (-0.0045, -0.4475))
        Line((-0.0045, -0.4475), (-0.0045, -0.4356))
    _inc_edges_custom3 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_custom3 = Wire.combine(_inc_edges_custom3)[0]
_wire_custom3 = _wire_custom3.moved(_inclined_plane_custom3.location)
_mkf_custom3 = BRepBuilderAPI_MakeFace(_inclined_plane_custom3.wrapped, _wire_custom3.wrapped, True)
_face_custom3 = Face(_mkf_custom3.Face())

# 'CustomCut4': 4-line + 1-arc profile at z=0.605, cut throughout body
_inclined_plane_custom4 = Plane(
    origin=Vector(0.0, 0.0, 0.605),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_custom4) as sk_CustomCut4:
    with BuildLine():
        Line((-0.1294, -0.12), (-0.1294, -0.0894))
        Line((-0.1294, -0.0894), (-0.104, -0.0894))
        Line((-0.104, -0.0894), (-0.104, -0.1))
        RadiusArc((-0.104, -0.1), (-0.124, -0.12), -0.02)
        Line((-0.124, -0.12), (-0.1294, -0.12))
    _inc_edges_custom4 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_custom4 = Wire.combine(_inc_edges_custom4)[0]
_wire_custom4 = _wire_custom4.moved(_inclined_plane_custom4.location)
_mkf_custom4 = BRepBuilderAPI_MakeFace(_inclined_plane_custom4.wrapped, _wire_custom4.wrapped, True)
_face_custom4 = Face(_mkf_custom4.Face())

# 'CustomCut5': CustomCut4 mirrored across x=0 (YZ plane)
_inclined_plane_custom5 = Plane(
    origin=Vector(0.0, 0.0, 0.605),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_custom5) as sk_CustomCut5:
    with BuildLine():
        Line((0.1294, -0.12), (0.1294, -0.0894))
        Line((0.1294, -0.0894), (0.104, -0.0894))
        Line((0.104, -0.0894), (0.104, -0.1))
        RadiusArc((0.104, -0.1), (0.124, -0.12), 0.02)
        Line((0.124, -0.12), (0.1294, -0.12))
    _inc_edges_custom5 = list(BuildSketch._get_context().pending_edges)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_custom5 = Wire.combine(_inc_edges_custom5)[0]
_wire_custom5 = _wire_custom5.moved(_inclined_plane_custom5.location)
_mkf_custom5 = BRepBuilderAPI_MakeFace(_inclined_plane_custom5.wrapped, _wire_custom5.wrapped, True)
_face_custom5 = Face(_mkf_custom5.Face())

# -- Build --
with BuildPart() as part:
    # --- FEATURE: Extrude1 ---
    # -- Extrude1 --
    extrude(sk_Sketch1.sketch, amount=-0.021)
    # Fusion depth expression: -0.021000002 mm
    
    # --- FEATURE: Extrude3 ---
    # -- Extrude3_p0 --
    extrude(sk_Sketch3_2.sketch, amount=-0.021, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.021000002 mm
    
    # -- Extrude3_p1 --
    extrude(sk_Sketch3_3.sketch, amount=-0.021, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.021000002 mm
    
    # -- Extrude3_p2 --
    extrude(sk_Sketch3_4.sketch, amount=-0.021, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.021000002 mm
    
    # -- Extrude3_p3 --
    extrude(sk_Sketch3_5.sketch, amount=-0.021, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.021000002 mm
    
    # --- FEATURE: Extrude4 ---
    # -- Extrude4 --
    extrude(sk_Sketch4_6.sketch, amount=0.006, mode=Mode.ADD)
    # Fusion depth expression: 0.006000008 mm
    
    # --- FEATURE: Extrude5 ---
    # -- Extrude5 --
    extrude(sk_Sketch5_7.sketch, amount=0.012, mode=Mode.ADD)
    # Fusion depth expression: 0.011999998 mm
    
    # --- FEATURE: Extrude6 ---
    # -- Extrude6 --
    extrude(sk_Sketch6_8.sketch, amount=-0.039, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.039000008 mm
    
    # --- FEATURE: Extrude8 ---
    # -- Extrude8 --
    _face = _face_sk_Sketch8_9
    _vec = Vector(0.0, 0.0, -1.0) * -0.288
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -0.287999995 mm
    
    # --- FEATURE: Extrude10 ---
    # -- Extrude10 --
    extrude(sk_Sketch10_10.sketch, amount=-0.025, mode=Mode.ADD)
    # Fusion depth expression: -0.025000013 mm
    
    # --- FEATURE: Extrude11 ---
    # -- Extrude11 --
    extrude(sk_Sketch11_11.sketch, amount=0.015, mode=Mode.ADD)
    # Fusion depth expression: 0.014999993 mm
    
    # --- FEATURE: Extrude12 ---
    # -- Extrude12 --
    extrude(sk_Sketch12_12.sketch, amount=0.003, mode=Mode.ADD)
    # Fusion depth expression: 0.003000014 mm
    
    # --- FEATURE: Extrude16 ---
    # -- Extrude16 --
    _face = _face_sk_Sketch17_13
    _solid = _solid_sk_Sketch17_13
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -0.014999993 mm
    # Fusion taper angle expression: 15 deg
    
    # --- FEATURE: Extrude17 ---
    # -- Extrude17 --
    _face = _face_sk_Sketch18_14
    _vec = Vector(0.0, 0.0, -1.0) * -0.015
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # --- FEATURE: Extrude9 ---
    # -- Extrude9_p0 --
    extrude(sk_Sketch9_15.sketch, amount=-0.05, mode=Mode.ADD)
    # Fusion depth expression: -0.050000008 mm
    
    # -- Extrude9_p1 --
    extrude(sk_Sketch9_16.sketch, amount=-0.05, mode=Mode.ADD)
    # Fusion depth expression: -0.050000008 mm
    
    # -- Extrude9_p2 --
    extrude(sk_Sketch9_17.sketch, amount=-0.05, mode=Mode.ADD)
    # Fusion depth expression: -0.050000008 mm
    
    # -- Extrude9_p3 --
    extrude(sk_Sketch9_18.sketch, amount=-0.05, mode=Mode.ADD)
    # Fusion depth expression: -0.050000008 mm
    
    # -- Extrude9_p4 --
    extrude(sk_Sketch9_19.sketch, amount=-0.05, mode=Mode.ADD)
    # Fusion depth expression: -0.050000008 mm
    
    # -- Extrude9_p5 --
    extrude(sk_Sketch9_20.sketch, amount=-0.05, mode=Mode.ADD)
    # Fusion depth expression: -0.050000008 mm
    
    # --- FEATURE: Extrude18 ---
    # -- Extrude18_p0 --
    _face = _face_sk_Sketch19_21
    _vec = Vector(0.0, 0.0, -1.0) * -0.015
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude18_p1 --
    _face = _face_sk_Sketch19_22
    _vec = Vector(0.0, 0.0, -1.0) * -0.015
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # --- FEATURE: Extrude20 ---
    # -- Extrude20_p0 --
    extrude(sk_Sketch26_23.sketch, amount=-0.025, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.025000013 mm
    
    # -- Extrude20_p1 --
    extrude(sk_Sketch26_24.sketch, amount=-0.025, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.025000013 mm
    
    # -- Extrude20_p2 --
    extrude(sk_Sketch26_25.sketch, amount=-0.025, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.025000013 mm
    
    # -- Extrude20_p3 --
    extrude(sk_Sketch26_26.sketch, amount=-0.025, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.025000013 mm
    
    # --- FEATURE: Extrude26 ---
    # -- Extrude26 --
    _face = _face_sk_Sketch34_27
    _solid = _solid_sk_Sketch34_27
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 0.02600003 mm
    # Fusion taper angle expression: -15 deg
    
    # --- FEATURE: Extrude27 ---
    # -- Extrude27_p0 --
    _face = _face_sk_Sketch35_28
    _vec = Vector(0.0, 0.0, 1.0) * 0.08
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 0.080000 mm
    
    # -- Extrude27_p1 --
    _face = _face_sk_Sketch35_29
    _vec = Vector(0.0, 0.0, 1.0) * 0.08
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: 0.080000 mm
    
    # --- FEATURE: Extrude28 ---
    # -- Extrude28_p0 --
    _face = _face_sk_Sketch36_30
    _vec = Vector(0.0, 0.0, 1.0) * -0.015
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude28_p1 --
    _face = _face_sk_Sketch36_31
    _vec = Vector(0.0, 0.0, 1.0) * -0.015
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # --- FEATURE: Extrude30 ---
    # -- Extrude30_p0 --
    extrude(sk_Sketch39_32.sketch, amount=-0.026, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.02600003 mm
    
    # -- Extrude30_p1 --
    extrude(sk_Sketch39_33.sketch, amount=-0.026, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.02600003 mm
    
    # --- FEATURE: Extrude31 ---
    # -- Extrude31_p0 --
    extrude(sk_Sketch40_34.sketch, amount=-0.0131, mode=Mode.ADD)
    # Fusion depth expression: -0.013133958 mm
    
    # -- Extrude31_p1 --
    extrude(sk_Sketch40_35.sketch, amount=-0.0131, mode=Mode.ADD)
    # Fusion depth expression: -0.013133958 mm
    
    # -- Extrude31_p2 --
    extrude(sk_Sketch40_36.sketch, amount=-0.0131, mode=Mode.ADD)
    # Fusion depth expression: -0.013133958 mm
    
    # -- Extrude31_p3 --
    extrude(sk_Sketch40_37.sketch, amount=-0.0131, mode=Mode.ADD)
    # Fusion depth expression: -0.013133958 mm
    
    # --- FEATURE: Extrude29 ---
    # -- Extrude29_p0 --
    extrude(sk_Sketch38_38.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude29_p1 --
    extrude(sk_Sketch38_39.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude29_p2 --
    extrude(sk_Sketch38_40.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude29_p3 --
    extrude(sk_Sketch38_41.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # --- FEATURE: Extrude36 ---
    # -- Extrude36_p0 --
    _face = _face_sk_Sketch45_42
    _solid = _solid_sk_Sketch45_42
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    # Fusion taper angle expression: -15 deg
    
    # -- Extrude36_p1 --
    _face = _face_sk_Sketch45_43
    _solid = _solid_sk_Sketch45_43
    add(_solid, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    # Fusion taper angle expression: -15 deg
    
    # --- FEATURE: Extrude33 ---
    # -- Extrude33_p0 --
    extrude(sk_Sketch42_44.sketch, amount=-0.0127, mode=Mode.ADD)
    # Fusion depth expression: -0.012749694 mm
    
    # -- Extrude33_p1 --
    extrude(sk_Sketch42_45.sketch, amount=-0.0127, mode=Mode.ADD)
    # Fusion depth expression: -0.012749694 mm
    
    # -- Extrude33_p2 --
    extrude(sk_Sketch42_46.sketch, amount=-0.0127, mode=Mode.ADD)
    # Fusion depth expression: -0.012749694 mm
    
    # -- Extrude33_p3 --
    extrude(sk_Sketch42_47.sketch, amount=-0.0127, mode=Mode.ADD)
    # Fusion depth expression: -0.012749694 mm
    
    # --- FEATURE: Extrude32 ---
    # -- Extrude32_p0 --
    extrude(sk_Sketch41_48.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude32_p1 --
    extrude(sk_Sketch41_49.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude32_p2 --
    extrude(sk_Sketch41_50.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # -- Extrude32_p3 --
    extrude(sk_Sketch41_51.sketch, amount=-0.015, mode=Mode.SUBTRACT)
    # Fusion depth expression: -0.014999993 mm
    
    # --- FEATURE: Extrude34 ---
    # -- Extrude34 --
    _face = _face_sk_Sketch43_52
    _vec = Vector(1.0, 0.0, 0.0) * -0.184
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: -0.184000004 mm
    
    # --- FEATURE: Extrude37 ---
    # -- Extrude37_p0 --
    extrude(sk_Sketch48_53.sketch, amount=0.008, mode=Mode.ADD)
    # Fusion depth expression: 0.007999986 mm
    
    # -- Extrude37_p1 --
    extrude(sk_Sketch48_54.sketch, amount=0.008, mode=Mode.ADD)
    # Fusion depth expression: 0.007999986 mm
    
    # --- FEATURE: Extrude38 ---
    # -- Extrude38_p0 --
    extrude(sk_Sketch49_55.sketch, amount=0.003, taper=15.0, mode=Mode.ADD)
    # Fusion depth expression: 0.003000014 mm
    # Fusion taper angle expression: -14.99999 deg
    
    # -- Extrude38_p1 --
    extrude(sk_Sketch49_56.sketch, amount=0.003, taper=15.0, mode=Mode.ADD)
    # Fusion depth expression: 0.003000014 mm
    # Fusion taper angle expression: -14.99999 deg
    
    # --- FEATURE: Extrude39 ---
    # -- Extrude39_p0 --
    extrude(sk_Sketch50_57.sketch, amount=0.0022, taper=42.0, mode=Mode.ADD)
    # Fusion depth expression: 0.00219617 mm
    # Fusion taper angle expression: -42 deg
    
    # -- Extrude39_p1 --
    extrude(sk_Sketch50_58.sketch, amount=0.0022, taper=42.0, mode=Mode.ADD)
    # Fusion depth expression: 0.00219617 mm
    # Fusion taper angle expression: -42 deg
    
    # --- FEATURE: Extrude40 ---
    # -- Extrude40_p0 --
    extrude(sk_Sketch51_59.sketch, amount=0.0008, taper=73.0, mode=Mode.ADD)
    # Fusion depth expression: 0.000803843 mm
    # Fusion taper angle expression: -73 deg
    
    # -- Extrude40_p1 --
    extrude(sk_Sketch51_60.sketch, amount=0.0008, taper=73.0, mode=Mode.ADD)
    # Fusion depth expression: 0.000803843 mm
    # Fusion taper angle expression: -73 deg
    
    # --- FEATURE: Extrude43 ---
    # -- Extrude43 --
    extrude(sk_Sketch54_61.sketch, amount=0.0044, mode=Mode.ADD)
    # Fusion depth expression: 0.004412308 mm
    
    # --- FEATURE: Extrude44 ---
    # -- Extrude44 --
    extrude(sk_Sketch55_62.sketch, amount=0.0058, taper=10.0, mode=Mode.ADD)
    # Fusion depth expression: 0.005772561 mm
    # Fusion taper angle expression: -10 deg
    
    # --- FEATURE: Extrude45 ---
    # -- Extrude45 --
    extrude(sk_Sketch56_63.sketch, amount=0.0011, taper=19.0, mode=Mode.ADD)
    # Fusion depth expression: 0.001102686 mm
    # Fusion taper angle expression: -19 deg
    
    # --- FEATURE: Extrude46 ---
    # -- Extrude46 --
    extrude(sk_Sketch57_64.sketch, amount=0.0023, taper=44.0, mode=Mode.ADD)
    # Fusion depth expression: 0.002282113 mm
    # Fusion taper angle expression: -44 deg
    
    # --- FEATURE: Extrude48 ---
    # -- Extrude48 --
    extrude(sk_Sketch59_65.sketch, amount=0.0014, taper=76.0, mode=Mode.ADD)
    # Fusion depth expression: 0.001430288 mm
    # Fusion taper angle expression: -76 deg

    # --- FEATURE: CustomCut1 ---
    # -- CustomCut1 --
    _vec = Vector(0.0, 0.0, 1.0) * 0.387
    _solid = Solid.extrude(_face_custom1, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Cut profile from z=0.613 to z=1.0 (depth 0.387)

    # --- FEATURE: CustomCut2 ---
    # -- CustomCut2 --
    _vec = Vector(0.0, 0.0, 1.0) * 0.387
    _solid = Solid.extrude(_face_custom2, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Cut profile from z=0.613 to z=1.0 (depth 0.387)

    # --- FEATURE: CustomCut3 ---
    # -- CustomCut3 --
    _vec = Vector(0.0, 0.0, -1.0) * 0.00400002
    _solid = Solid.extrude(_face_custom3, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Cut profile from z=0.663 down to z=0.65899998 (depth 0.00400002)

    # --- FEATURE: CustomCut4 ---
    # -- CustomCut4 --
    _vec = Vector(0.0, 0.0, -1.0) * 0.4
    _solid = Solid.extrude(_face_custom4, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Cut throughout body from z=0.605 downward (depth 0.4)

    # --- FEATURE: CustomCut5 ---
    # -- CustomCut5: mirror of CustomCut4 across x=0 --
    _vec = Vector(0.0, 0.0, -1.0) * 0.4
    _solid = Solid.extrude(_face_custom5, _vec)
    add(_solid, mode=Mode.SUBTRACT)
    # Cut throughout body from z=0.605 downward (depth 0.4)


# -- Export --
export_step(part.part, 'Base_Motor.step')
export_stl(part.part,  'Base_Motor.stl')
if _has_ocp: show(part)
