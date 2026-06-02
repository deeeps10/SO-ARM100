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

# 'Sketch1': 8 segments → Line/RadiusArc profile
_inclined_plane_1 = Plane(
    origin=Vector(0.0, 0.0, 40.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch1:
    with BuildLine():
        RadiusArc((-185.0, 210.0), (-255.0, 140.0), -70.0)
        Line((-255.0, 140.0), (-255.0, -140.0))
        RadiusArc((-255.0, -140.0), (-185.0, -210.0), -70.0)
        Line((-185.0, -210.0), (185.0, -210.0))
        RadiusArc((185.0, -210.0), (255.0, -140.0), -70.0)
        Line((255.0, -140.0), (255.0, 140.0))
        RadiusArc((255.0, 140.0), (185.0, 210.0), -70.0)
        Line((185.0, 210.0), (-185.0, 210.0))
    _inc_edges_sk_Sketch1 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch1 = Wire.combine(_inc_edges_sk_Sketch1)[0]
_wire_sk_Sketch1 = _wire_sk_Sketch1.moved(_inclined_plane_1.location)
_mkf_sk_Sketch1 = BRepBuilderAPI_MakeFace(_inclined_plane_1.wrapped, _wire_sk_Sketch1.wrapped, True)
_face_sk_Sketch1 = Face(_mkf_sk_Sketch1.Face())

# 'Sketch2': 4 segments → Line/RadiusArc profile
_inclined_plane_2 = Plane(
    origin=Vector(0.0, 0.0, 40.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_2) as sk_Sketch2_2:
    with BuildLine():
        Line((-79.5, 79.0), (79.5, 79.0))
        Line((79.5, 79.0), (79.5, -79.0))
        Line((79.5, -79.0), (-79.5, -79.0))
        Line((-79.5, -79.0), (-79.5, 79.0))
    _inc_edges_sk_Sketch2_2 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch2_2 = Wire.combine(_inc_edges_sk_Sketch2_2)[0]
_wire_sk_Sketch2_2 = _wire_sk_Sketch2_2.moved(_inclined_plane_2.location)
_mkf_sk_Sketch2_2 = BRepBuilderAPI_MakeFace(_inclined_plane_2.wrapped, _wire_sk_Sketch2_2.wrapped, True)
_face_sk_Sketch2_2 = Face(_mkf_sk_Sketch2_2.Face())

# 'Sketch3': 4 segments → Line/RadiusArc profile
_inclined_plane_3 = Plane(
    origin=Vector(0.0, 0.0, 53.404),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_3) as sk_Sketch3_3:
    with BuildLine():
        Line((-79.5, 79.0), (79.5, 79.0))
        Line((79.5, 79.0), (79.5, -79.0))
        Line((79.5, -79.0), (-79.5, -79.0))
        Line((-79.5, -79.0), (-79.5, 79.0))
    _inc_edges_sk_Sketch3_3 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch3_3 = Wire.combine(_inc_edges_sk_Sketch3_3)[0]
_wire_sk_Sketch3_3 = _wire_sk_Sketch3_3.moved(_inclined_plane_3.location)
_mkf_sk_Sketch3_3 = BRepBuilderAPI_MakeFace(_inclined_plane_3.wrapped, _wire_sk_Sketch3_3.wrapped, True)
_face_sk_Sketch3_3 = Face(_mkf_sk_Sketch3_3.Face())

_solid_sk_Sketch3_3 = extrude(_face_sk_Sketch3_3, amount=12.0, dir=Vector(0.0, 0.0, 1.0), taper=-44.0).solid()

# 'Sketch4': 4 segments → Line/RadiusArc profile
_inclined_plane_4 = Plane(
    origin=Vector(0.0, 0.0, 65.404),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch4_4:
    with BuildLine():
        Line((-91.0883, 90.5883), (91.0883, 90.5883))
        Line((91.0883, 90.5883), (91.0883, -90.5883))
        Line((91.0883, -90.5883), (-91.0883, -90.5883))
        Line((-91.0883, -90.5883), (-91.0883, 90.5883))
    _inc_edges_sk_Sketch4_4 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch4_4 = Wire.combine(_inc_edges_sk_Sketch4_4)[0]
_wire_sk_Sketch4_4 = _wire_sk_Sketch4_4.moved(_inclined_plane_4.location)
_mkf_sk_Sketch4_4 = BRepBuilderAPI_MakeFace(_inclined_plane_4.wrapped, _wire_sk_Sketch4_4.wrapped, True)
_face_sk_Sketch4_4 = Face(_mkf_sk_Sketch4_4.Face())

# 'Sketch5': circle on inclined plane
_inclined_plane_5 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch5_5:
    with Locations((228.6712, -105.0)):
        Circle(radius=10.5)

# 'Sketch5': circle on inclined plane
_inclined_plane_6 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_6) as sk_Sketch5_6:
    with Locations((63.6712, -105.0)):
        Circle(radius=10.5)

# 'Sketch5': circle on inclined plane
_inclined_plane_7 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_7) as sk_Sketch5_7:
    with Locations((228.6712, 105.0)):
        Circle(radius=10.5)

# 'Sketch5': circle on inclined plane
_inclined_plane_8 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_8) as sk_Sketch5_8:
    with Locations((63.6712, 105.0)):
        Circle(radius=10.5)

# 'Sketch6': circle on inclined plane
_inclined_plane_9 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_9) as sk_Sketch6_9:
    with Locations((63.6712, 105.0)):
        Circle(radius=18.0)

# 'Sketch6': circle on inclined plane
_inclined_plane_10 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_10) as sk_Sketch6_10:
    with Locations((228.6712, 105.0)):
        Circle(radius=18.0)

# 'Sketch6': circle on inclined plane
_inclined_plane_11 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_11) as sk_Sketch6_11:
    with Locations((63.6712, -105.0)):
        Circle(radius=18.0)

# 'Sketch6': circle on inclined plane
_inclined_plane_12 = Plane(
    origin=Vector(0.0, 0.0, 20.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_12) as sk_Sketch6_12:
    with Locations((228.6712, -105.0)):
        Circle(radius=18.0)

# -- Build --
with BuildPart() as part:
    # --- FEATURE: Extrude1 ---
    # -- Extrude1 --
    _face = _face_sk_Sketch1
    _vec = Vector(0.0, 0.0, 1.0) * -40.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid)
    # Fusion depth expression: -40.000000 mm
    
    # --- FEATURE: Extrude2 ---
    # -- Extrude2 --
    _face = _face_sk_Sketch2_2
    _vec = Vector(0.0, 0.0, 1.0) * 13.404
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 13.404026031 mm
    
    # --- FEATURE: Extrude3 ---
    # -- Extrude3 --
    _face = _face_sk_Sketch3_3
    _solid = _solid_sk_Sketch3_3
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 11.999998093 mm
    # Fusion taper angle expression: 44.0 deg
    
    # --- FEATURE: Extrude4 ---
    # -- Extrude4 --
    _face = _face_sk_Sketch4_4
    _vec = Vector(0.0, 0.0, 1.0) * 10.596
    _solid = Solid.extrude(_face, _vec)
    add(_solid, mode=Mode.ADD)
    # Fusion depth expression: 10.595974922 mm
    
    # --- FEATURE: Extrude5 ---
    # -- Extrude5_p0 --
    extrude(sk_Sketch5_5.sketch, amount=-40.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -40.000000 mm
    
    # -- Extrude5_p1 --
    extrude(sk_Sketch5_6.sketch, amount=-40.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -40.000000 mm
    
    # -- Extrude5_p2 --
    extrude(sk_Sketch5_7.sketch, amount=-40.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -40.000000 mm
    
    # -- Extrude5_p3 --
    extrude(sk_Sketch5_8.sketch, amount=-40.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: -40.000000 mm
    
    # --- FEATURE: Extrude6 ---
    # -- Extrude6_p0 --
    extrude(sk_Sketch6_9.sketch, amount=25.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: 25.000000 mm
    
    # -- Extrude6_p1 --
    extrude(sk_Sketch6_10.sketch, amount=25.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: 25.000000 mm
    
    # -- Extrude6_p2 --
    extrude(sk_Sketch6_11.sketch, amount=25.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: 25.000000 mm
    
    # -- Extrude6_p3 --
    extrude(sk_Sketch6_12.sketch, amount=25.0, mode=Mode.SUBTRACT)
    # Fusion depth expression: 25.000000 mm
    

# -- Export --
export_step(part.part, '/Users/softage/Downloads/Seeedstudio_Mounting_Plate_SO101.step')
export_stl(part.part,  '/Users/softage/Downloads/Seeedstudio_Mounting_Plate_SO101.stl')
if _has_ocp: show(part)
