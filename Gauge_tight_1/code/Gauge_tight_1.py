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
    from OCP.TopAbs import TopAbs_SOLID
    try:
        fuse_op = BFuse(solid1.wrapped, solid2.wrapped)
        fuse_op.SetFuzzyValue(0.01)
        fuse_op.Build()
        result_shape = fuse_op.Shape()
        if not result_shape.IsNull() and result_shape.ShapeType() == TopAbs_SOLID:
            return Solid(result_shape)
    except:
        pass
    # Non-touching bodies: OCC returns a Compound — accumulate explicitly.
    existing = list(solid1.solids()) if isinstance(solid1, Compound) else [solid1]
    new_s = list(solid2.solids()) if isinstance(solid2, Compound) else [solid2]
    return Compound(existing + new_s)

def cut_solids(shape, tool):
    """Cut tool from shape with fuzzy tolerance. Handles Compound (multi-body) shapes with bbox pre-check."""
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
                        cut_result = Solid(cut_op.Shape())
                        if not cut_result.wrapped.IsNull() and len(list(cut_result.faces())) > 0:
                            result_solids.append(cut_result)
                        else:
                            result_solids.append(solid)
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
                cut_result = Solid(cut_op.Shape())
                if not cut_result.wrapped.IsNull() and len(list(cut_result.faces())) > 0:
                    return cut_result
            return shape
    except:
        return shape

# -- Edge selection helpers --
# Use these to select edges for fillet/chamfer operations.
# Find edge coordinates using the diagnostic pattern at the bottom of this file.

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

# 'Sketch1': 8 segments → Line/RadiusArc profile
_inclined_plane_1 = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_1) as sk_Sketch1:
    with BuildLine():
        Line((417.0, 247.1429), (417.0, 346.0))
        Line((417.0, 346.0), (0.0, 346.0))
        Line((0.0, 346.0), (0.0, 0.0))
        Line((0.0, 0.0), (417.0, 0.0))
        Line((417.0, 0.0), (417.0, 98.8571))
        Line((417.0, 98.8571), (437.0, 98.8571))
        # Spline from NurbsCurve3D, 144 adaptive samples
        Spline((437.0, 98.8571), (439.4837, 98.9925), (440.7001, 99.0758), (441.8994, 99.1697), (443.0819, 99.274), (444.2474, 99.3889), (446.5281, 99.6504), (448.7424, 99.9544), (450.892, 100.3016), (452.9793, 100.693), (455.0077, 101.1295), (456.9818, 101.613), (458.9074, 102.1453), (460.7919, 102.729), (462.6437, 103.3668), (464.4717, 104.0618), (466.2846, 104.8168), (468.0904, 105.6345), (469.8956, 106.5171), (471.7048, 107.4661), (473.5196, 108.4821), (475.3386, 109.5645), (477.1567, 110.7118), (478.9666, 111.9213), (480.7587, 113.1893), (482.5225, 114.5118), (484.2473, 115.8837), (485.9231, 117.2999), (487.541, 118.7549), (489.0946, 120.2431), (490.5805, 121.7589), (491.9984, 123.2973), (493.3508, 124.8536), (494.6423, 126.4244), (495.8786, 128.0077), (497.0661, 129.6033), (498.2107, 131.2131), (499.3178, 132.842), (500.3906, 134.4976), (501.4305, 136.1908), (502.4365, 137.9348), (502.9259, 138.8302), (503.4058, 139.7436), (503.8755, 140.6766), (504.3345, 141.6309), (504.782, 142.6077), (505.2176, 143.6082), (505.6404, 144.6333), (506.0499, 145.6836), (506.4454, 146.7594), (506.8263, 147.8603), (507.1921, 148.986), (507.5422, 150.1351), (507.8763, 151.306), (508.194, 152.4965), (508.4951, 153.7039), (508.7795, 154.9249), (509.2978, 157.3929), (509.7492, 159.8682), (510.1349, 162.3165), (510.3036, 163.5199), (510.4566, 164.7039), (510.5941, 165.8649), (510.7165, 166.9995), (510.824, 168.1048), (510.9168, 169.1783), (510.9953, 170.2182), (511.0598, 171.2235), (511.1104, 172.1937), (511.1472, 173.1294), (511.1705, 174.0321), (511.1804, 174.9042), (511.1767, 175.749), (511.1597, 176.5703), (511.0849, 178.1614), (510.9553, 179.718), (510.7695, 181.2829), (510.6549, 182.0813), (510.5257, 182.8966), (510.3815, 183.7328), (510.2221, 184.5931), (510.0472, 185.4798), (509.8565, 186.3945), (509.6497, 187.3378), (509.4267, 188.3098), (509.187, 189.3095), (508.9306, 190.3356), (508.6571, 191.386), (508.3665, 192.4583), (508.0584, 193.5497), (507.7328, 194.6571), (507.0288, 196.9061), (506.2543, 199.1767), (505.4098, 201.4402), (504.9619, 202.561), (504.4972, 203.6703), (504.0162, 204.7658), (503.5192, 205.8453), (503.0069, 206.9071), (502.4798, 207.9499), (501.9386, 208.9727), (501.3839, 209.9752), (500.8165, 210.9568), (500.2371, 211.9178), (499.6464, 212.8583), (499.045, 213.7787), (498.4337, 214.6797), (497.813, 215.5622), (496.5459, 217.275), (495.2475, 218.9251), (493.9202, 220.5209), (492.5644, 222.0703), (491.1786, 223.5793), (489.7594, 225.0524), (488.3023, 226.4924), (486.8021, 227.9004), (485.2537, 229.2765), (483.6529, 230.6193), (481.9969, 231.9268), (480.285, 233.1961), (478.5191, 234.4236), (476.7044, 235.6053), (474.8485, 236.7373), (472.961, 237.8152), (471.0528, 238.8352), (469.1349, 239.7937), (467.2182, 240.6877), (465.3124, 241.5152), (463.4255, 242.275), (461.5629, 242.9671), (459.7271, 243.5931), (457.918, 244.1552), (456.1334, 244.6568), (454.3697, 245.1018), (452.6223, 245.494), (450.8864, 245.8376), (449.157, 246.1361), (447.4302, 246.3926), (445.7027, 246.6096), (443.9723, 246.7886), (442.2376, 246.9309), (440.4976, 247.0372), (438.7518, 247.1078), (437.0, 247.1429))
        Line((437.0, 247.1429), (417.0, 247.1429))
    _inc_edges_sk_Sketch1 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch1 = Wire.combine(_inc_edges_sk_Sketch1)[0]
_wire_sk_Sketch1 = _wire_sk_Sketch1.moved(_inclined_plane_1.location)
_mkf_sk_Sketch1 = BRepBuilderAPI_MakeFace(_inclined_plane_1.wrapped, _wire_sk_Sketch1.wrapped, True)
_face_sk_Sketch1 = Face(_mkf_sk_Sketch1.Face())

# 'Sketch3': 12 segments → Line/RadiusArc profile
_inclined_plane_2 = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_2) as sk_Sketch3_2:
    with BuildLine():
        Line((379.0, 103.0), (367.0, 103.0))
        Line((367.0, 103.0), (367.0, 50.0))
        Line((367.0, 50.0), (50.0, 50.0))
        Line((50.0, 50.0), (50.0, 80.5))
        Line((50.0, 80.5), (31.0, 80.5))
        Line((31.0, 80.5), (31.0, 265.5))
        Line((31.0, 265.5), (50.0, 265.5))
        Line((50.0, 265.5), (50.0, 296.0))
        Line((50.0, 296.0), (367.0, 296.0))
        Line((367.0, 296.0), (367.0, 243.0))
        Line((367.0, 243.0), (379.0, 243.0))
        Line((379.0, 243.0), (379.0, 103.0))
    _inc_edges_sk_Sketch3_2 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch3_2 = Wire.combine(_inc_edges_sk_Sketch3_2)[0]
_wire_sk_Sketch3_2 = _wire_sk_Sketch3_2.moved(_inclined_plane_2.location)
_mkf_sk_Sketch3_2 = BRepBuilderAPI_MakeFace(_inclined_plane_2.wrapped, _wire_sk_Sketch3_2.wrapped, True)
_face_sk_Sketch3_2 = Face(_mkf_sk_Sketch3_2.Face())

# 'Sketch4': 6 segments → Line/RadiusArc profile
_inclined_plane_3 = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_3) as sk_Sketch4_3:
    with BuildLine():
        Line((483.0, 146.8271), (483.0, 169.0226))
        Line((483.0, 169.0226), (469.6667, 177.5963))
        Line((469.6667, 177.5963), (469.6667, 161.186))
        Line((469.6667, 161.186), (403.0, 161.186))
        Line((403.0, 161.186), (403.0, 146.8271))
        Line((403.0, 146.8271), (483.0, 146.8271))
    _inc_edges_sk_Sketch4_3 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch4_3 = Wire.combine(_inc_edges_sk_Sketch4_3)[0]
_wire_sk_Sketch4_3 = _wire_sk_Sketch4_3.moved(_inclined_plane_3.location)
_mkf_sk_Sketch4_3 = BRepBuilderAPI_MakeFace(_inclined_plane_3.wrapped, _wire_sk_Sketch4_3.wrapped, True)
_face_sk_Sketch4_3 = Face(_mkf_sk_Sketch4_3.Face())

# 'Sketch5': 6 segments → Line/RadiusArc profile
_inclined_plane_4 = Plane(
    origin=Vector(0.0, 0.0, 83.219),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_4) as sk_Sketch5_4:
    with BuildLine():
        Line((403.0, 146.8271), (483.0, 146.8271))
        Line((483.0, 146.8271), (483.0, 169.0226))
        Line((483.0, 169.0226), (469.6667, 177.5963))
        Line((469.6667, 177.5963), (469.6667, 161.186))
        Line((469.6667, 161.186), (403.0, 161.186))
        Line((403.0, 161.186), (403.0, 146.8271))
    _inc_edges_sk_Sketch5_4 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch5_4 = Wire.combine(_inc_edges_sk_Sketch5_4)[0]
_wire_sk_Sketch5_4 = _wire_sk_Sketch5_4.moved(_inclined_plane_4.location)
_mkf_sk_Sketch5_4 = BRepBuilderAPI_MakeFace(_inclined_plane_4.wrapped, _wire_sk_Sketch5_4.wrapped, True)
_face_sk_Sketch5_4 = Face(_mkf_sk_Sketch5_4.Face())

# 'Sketch6': 4 segments → Line/RadiusArc profile
_inclined_plane_5 = Plane(
    origin=Vector(0.0, 0.0, 100.0),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_5) as sk_Sketch6_5:
    with BuildLine():
        Line((425.5641, 196.0578), (425.5641, 223.7501))
        Line((425.5641, 223.7501), (438.8974, 223.7501))
        Line((438.8974, 223.7501), (438.8974, 196.0578))
        Line((438.8974, 196.0578), (425.5641, 196.0578))
    _inc_edges_sk_Sketch6_5 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch6_5 = Wire.combine(_inc_edges_sk_Sketch6_5)[0]
_wire_sk_Sketch6_5 = _wire_sk_Sketch6_5.moved(_inclined_plane_5.location)
_mkf_sk_Sketch6_5 = BRepBuilderAPI_MakeFace(_inclined_plane_5.wrapped, _wire_sk_Sketch6_5.wrapped, True)
_face_sk_Sketch6_5 = Face(_mkf_sk_Sketch6_5.Face())

# 'Sketch7': 4 segments → Line/RadiusArc profile
_inclined_plane_6 = Plane(
    origin=Vector(0.0, 0.0, 83.219),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_inclined_plane_6) as sk_Sketch7_6:
    with BuildLine():
        Line((425.5641, 196.0578), (425.5641, 223.7501))
        Line((425.5641, 223.7501), (438.8974, 223.7501))
        Line((438.8974, 223.7501), (438.8974, 196.0578))
        Line((438.8974, 196.0578), (425.5641, 196.0578))
    _inc_edges_sk_Sketch7_6 = list(BuildSketch._get_context().pending_edges)
# Build inclined-plane face outside BuildSketch (bypasses BRepFill_Filling)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
_wire_sk_Sketch7_6 = Wire.combine(_inc_edges_sk_Sketch7_6)[0]
_wire_sk_Sketch7_6 = _wire_sk_Sketch7_6.moved(_inclined_plane_6.location)
_mkf_sk_Sketch7_6 = BRepBuilderAPI_MakeFace(_inclined_plane_6.wrapped, _wire_sk_Sketch7_6.wrapped, True)
_face_sk_Sketch7_6 = Face(_mkf_sk_Sketch7_6.Face())

# -- Separate body: body_Extrude1 (mirrored) --
with BuildPart() as body_Extrude1:
    # -- Extrude1 --
    _face = _face_sk_Sketch1
    _vec = Vector(0.0, 0.0, 1.0) * -50.0
    _solid = Solid.extrude(_face, _vec)
    add(_solid)
    # Fusion depth expression: -50.000000 mm
    
    # -- Extrude2 --
    _face = _face_sk_Sketch3_2
    _vec = Vector(0.0, 0.0, 1.0) * -120.0
    _solid = Solid.extrude(_face, _vec)
    _result = body_Extrude1.part.cut(_solid)
    body_Extrude1.part = _result[0] if isinstance(_result, ShapeList) else _result
    # Fusion depth expression: -120.000000 mm
    
    # -- Extrude3 --
    _face = _face_sk_Sketch4_3
    _vec = Vector(0.0, 0.0, 1.0) * -16.781
    _solid = Solid.extrude(_face, _vec)
    _result = body_Extrude1.part.cut(_solid)
    body_Extrude1.part = _result[0] if isinstance(_result, ShapeList) else _result
    # Fusion depth expression: -16.7810154 mm
    
    # -- Extrude4 --
    _face = _face_sk_Sketch5_4
    _vec = Vector(0.0, 0.0, 1.0) * -7.219
    _solid = Solid.extrude_taper(_face, _vec, taper=42)
    _result = body_Extrude1.part.cut(_solid)
    body_Extrude1.part = _result[0] if isinstance(_result, ShapeList) else _result
    # Fusion depth expression: -7.21898555 mm
    # Fusion taper angle expression: -42 deg
    
    # -- Extrude5 --
    _face = _face_sk_Sketch6_5
    _vec = Vector(0.0, 0.0, 1.0) * -16.781
    _solid = Solid.extrude(_face, _vec)
    _result = body_Extrude1.part.cut(_solid)
    body_Extrude1.part = _result[0] if isinstance(_result, ShapeList) else _result
    # Fusion depth expression: -16.7810154 mm
    
    # -- Extrude6 --
    _face = _face_sk_Sketch7_6
    _vec = Vector(0.0, 0.0, 1.0) * -7.219
    _solid = Solid.extrude_taper(_face, _vec, taper=42)
    _result = body_Extrude1.part.cut(_solid)
    body_Extrude1.part = _result[0] if isinstance(_result, ShapeList) else _result
    # Fusion depth expression: -7.21898556 mm
    # Fusion taper angle expression: -42 deg
    

# -- Build --
with BuildPart() as part:
    # -- C-Pattern1 (bodies: Body3) --
    _custom_axis = Axis(
        Vector(0.0, 173.0, 50.0),
        Vector(1.0, 0.0, 0.0),
    )
    # Axis: _custom_axis  count=2  step=180.0deg
    for _pat_i in range(2):
        add(body_Extrude1.part.rotate(_custom_axis, _pat_i * 180.0))

    # -- Chamfer --
    # Chamfer distance=10.0mm on edges: 33,28,30,26,22,25,27,29,32,24,23,31,81,85,74,77,78,82,86,90,96,89,93,94
    try:
        chamfer([part.edges()[33], part.edges()[28], part.edges()[30], part.edges()[26], part.edges()[22], part.edges()[25], part.edges()[27], part.edges()[29], part.edges()[32], part.edges()[24], part.edges()[23], part.edges()[31], part.edges()[81], part.edges()[85], part.edges()[74], part.edges()[77], part.edges()[78], part.edges()[82], part.edges()[86], part.edges()[90], part.edges()[96], part.edges()[89], part.edges()[93], part.edges()[94]], length=13.32735062, length2=12.00000763 )
    except Exception as _ce:
        print('WARNING: Chamfer failed:', _ce)

    # -- Chamfer2 --
    # Chamfer distance=10.0mm on edges: 141,59,55,84,80,82,77,60,12,15,13,17,19,18,16,14
    try:
        chamfer([part.edges()[141], part.edges()[59], part.edges()[55], part.edges()[84], part.edges()[80], part.edges()[82], part.edges()[77], part.edges()[60], part.edges()[12], part.edges()[15], part.edges()[13], part.edges()[17], part.edges()[19], part.edges()[18], part.edges()[16], part.edges()[14]], length=12.0, length2=10.80486298)
    except Exception as _ce:
        print('WARNING: Chamfer2 failed:', _ce)


# -- Export --
export_step(part.part, 'Gauge_tight_1.step')
export_stl(part.part,  'Gauge_tight_1.stl')
if _has_ocp: show(part)

# -- Edge coordinate diagnostic --
# Uncomment the block below to find edge coordinates for fillet/chamfer.
# Set tx, ty, tz to a point near the edge you're looking for.
# Run the script — matching edges will print their vertex coordinates.
#
# tx, ty, tz = 0, 0, 0  # <-- set target coordinates here
# for e in part.part.edges():
#     verts = e.vertices()
#     for v in verts:
#         if abs(v.X - tx) < 1 and abs(v.Y - ty) < 1 and abs(v.Z - tz) < 1:
#             print([(round(v2.X,3), round(v2.Y,3), round(v2.Z,3)) for v2 in verts])
#             break
