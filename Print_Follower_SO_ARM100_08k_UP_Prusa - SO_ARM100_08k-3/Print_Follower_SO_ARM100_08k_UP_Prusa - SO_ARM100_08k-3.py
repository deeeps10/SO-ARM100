# Units: mm throughout.
from build123d import *
import math

_plane = Plane(
    origin=Vector(0.0, 0.0, 345.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)

with BuildSketch(_plane) as sk_profile:
    with BuildLine():
        Line((2408.7988, 1880.1741), (2004.7795, 1880.8414))
        RadiusArc((2004.7795, 1880.8414), (1924.9254, 1960.9928), 80.0)
        Line((1924.9254, 1960.9928), (1925.2969, 2156.991))
        RadiusArc((1925.2969, 2156.991), (2005.4468, 2236.8408), 79.9998)
        Line((2005.4468, 2236.8408), (2369.4464, 2236.1584))
        RadiusArc((2369.4464, 2236.1584), (2449.2961, 2156.0086), 79.9999)
        Line((2449.2961, 2156.0086), (2448.9287, 1960.009))
        RadiusArc((2448.9287, 1960.009), (2408.7988, 1890.802), 80.0001)
        Line((2408.7988, 1890.802), (2408.7988, 1880.1741))
    _inc_edges = list(BuildSketch._get_context().pending_edges)

from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3, gp_Pln
_wire = Wire.combine(_inc_edges)[0]
_wire = _wire.moved(_plane.location)
_mkf = BRepBuilderAPI_MakeFace(_plane.wrapped, _wire.wrapped, True)
_face = Face(_mkf.Face())

def _near(a, b, t=0.1):
    return abs(a - b) < t

def _is_excluded_edge(edge):
    excl_pts = [
        (2408.7988, 1890.802,  345.6977),
        (2408.7988, 1880.1741, 345.6977),
    ]
    verts = edge.vertices()
    matched = 0
    for v in verts:
        for ep in excl_pts:
            if _near(v.X, ep[0]) and _near(v.Y, ep[1]) and _near(v.Z, ep[2]):
                matched += 1
                break
    return matched >= 2

# --- Cut profile at z=355.6977 ---
_cut_plane = Plane(
    origin=Vector(0.0, 0.0, 355.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)

with BuildSketch(_cut_plane) as sk_cut:
    with BuildLine():
        Line((2350.8351, 1910.1927), (2032.8357, 1910.7889))
        Line((2032.8357, 1910.7889), (2032.9369, 1964.7888))
        Line((2032.9369, 1964.7888), (1954.937,  1964.935))
        Line((1954.937,  1964.935),  (1955.2969, 2156.9347))
        RadiusArc((1955.2969, 2156.9347), (2005.3906, 2206.8408), 49.9999)
        Line((2005.3906, 2206.8408), (2369.39,   2206.1584))
        RadiusArc((2369.39, 2206.1584), (2419.2961, 2156.0649), 49.9999)
        Line((2419.2961, 2156.0649), (2418.94,   1966.0652))
        Line((2418.94,   1966.0652), (2418.902,  1946.1743))
        Line((2418.902,  1946.1743), (2369.9025, 1946.1571))
        Line((2369.9025, 1946.1571), (2350.9026, 1946.1926))
        Line((2350.9026, 1946.1926), (2350.8351, 1910.1927))
    _cut_inc_edges = list(BuildSketch._get_context().pending_edges)

_cut_wire = Wire.combine(_cut_inc_edges)[0]
_cut_wire = _cut_wire.moved(_cut_plane.location)
_cut_mkf = BRepBuilderAPI_MakeFace(_cut_plane.wrapped, _cut_wire.wrapped, True)
_cut_face = Face(_cut_mkf.Face())

def _edge_key(e):
    c = e.center()
    return (round(c.X, 3), round(c.Y, 3), round(c.Z, 3))

# --- Add3 profile face: plane at x=2369.9002, normal=+x; local x=worldY, local y=worldZ ---
_add3_sk_plane = Plane(
    origin=Vector(2369.9002, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_add3_sk_plane) as _sk_add3:
    with BuildLine():
        # 2D coords (worldY, worldZ), reversed for CCW winding viewed from +x
        Polyline(
            (1944.9247, 65.6977),
            (1964.7104, 65.6977),
            (1966.1571, 262.1156),
            (1949.8291, 330.352),
            (1948.7849, 333.5203),
            (1947.2285, 336.4709),
            (1946.1571, 337.9869),
            close=True,
        )
    _add3_edges = list(BuildSketch._get_context().pending_edges)

_add3_wire = Wire.combine(_add3_edges)[0]
_add3_wire = _add3_wire.moved(_add3_sk_plane.location)
_add3_mkf = BRepBuilderAPI_MakeFace(_add3_sk_plane.wrapped, _add3_wire.wrapped, True)
_add3_face = Face(_add3_mkf.Face())

# --- Add4 profile face: plane at x=2369.9002, normal=+x; local x=worldY, local y=worldZ ---
_add4_sk_plane = Plane(
    origin=Vector(2369.9002, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_add4_sk_plane) as _sk_add4:
    with BuildLine():
        # 2D coords (worldY, worldZ), reversed for CCW winding viewed from +x
        Polyline(
            (1964.7104, 65.6977),
            (1964.8992, 91.3372),
            (1927.3709, 91.3372),
            (1927.3709, 65.6977),
            close=True,
        )
    _add4_edges = list(BuildSketch._get_context().pending_edges)

_add4_wire = Wire.combine(_add4_edges)[0]
_add4_wire = _add4_wire.moved(_add4_sk_plane.location)
_add4_mkf = BRepBuilderAPI_MakeFace(_add4_sk_plane.wrapped, _add4_wire.wrapped, True)
_add4_face = Face(_add4_mkf.Face())

# --- Cut6 profile: plane at x=2408.817, normal=+x; local x=worldY, local y=worldZ ---
_cut6_sk_plane = Plane(
    origin=Vector(2408.817, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_cut6_sk_plane) as _sk_cut6:
    with BuildLine():
        Polyline(
            (1900.4819, 360.2376),
            (1844.5683, 360.2376),
            (1844.5683, 304.3236),
            (1867.0847, 326.8404),
            (1875.0841, 334.8398),
            (1883.013,  342.7687),
            close=True,
        )
    _cut6_edges = list(BuildSketch._get_context().pending_edges)

_cut6_wire = Wire.combine(_cut6_edges)[0]
_cut6_wire = _cut6_wire.moved(_cut6_sk_plane.location)
_cut6_mkf = BRepBuilderAPI_MakeFace(_cut6_sk_plane.wrapped, _cut6_wire.wrapped, True)
_cut6_face = Face(_cut6_mkf.Face())

# --- Cut9 profile: plane at x=1925.2231 (min x), normal=+x; local x=worldY, local y=worldZ ---
_cut9_sk_plane = Plane(
    origin=Vector(1925.2231, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_cut9_sk_plane) as _sk_cut9:
    with BuildLine():
        Polyline(
            (2137.491,  222.2828),
            (2123.2014, 207.6909),
            (2120.9975, 205.0098),
            (2119.2902, 201.988),
            (2118.131,  198.7165),
            (2117.5548, 195.2939),
            (2117.579,  191.8232),
            (2118.2028, 188.409),
            (2119.4077, 185.154),
            (2121.1571, 182.1563),
            (2123.3983, 179.5063),
            (2126.064,  177.2835),
            (2132.337,  174.3731),
            (2135.7556, 173.7731),
            (2139.2264, 173.7731),
            (2145.9081, 175.5551),
            (2148.918,  177.2835),
            (2151.5836, 179.5063),
            (2153.8249, 182.1563),
            (2155.5742, 185.154),
            (2156.991,  189.2536),
            (2157.4028, 191.8232),
            (2157.4271, 195.2939),
            (2156.991,  198.1418),
            (2155.6917, 201.988),
            (2153.9844, 205.0098),
            (2151.7804, 207.6909),
            close=True,
        )
    _cut9_edges = list(BuildSketch._get_context().pending_edges)

_cut9_wire = Wire.combine(_cut9_edges)[0]
_cut9_wire = _cut9_wire.moved(_cut9_sk_plane.location)
_cut9_mkf = BRepBuilderAPI_MakeFace(_cut9_sk_plane.wrapped, _cut9_wire.wrapped, True)
_cut9_face = Face(_cut9_mkf.Face())

# --- Cut10 profile: plane at x=1925.3665 (min x of points), cut in +x to x=2010.91339111 ---
_cut10_sk_plane = Plane(
    origin=Vector(1925.3665, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_cut10_sk_plane) as _sk_cut10:
    with BuildLine():
        Polyline(
            (1932.4815, 222.2828),
            (1940.1242, 214.483),
            (1946.7783, 207.6909),
            (1947.0972, 207.3579),
            (1948.983,  205.0098),
            (1949.9022, 203.5368),
            (1950.6909, 201.988),
            (1951.3419, 200.3769),
            (1951.8503, 198.7165),
            (1952.2127, 197.0187),
            (1952.4266, 195.2939),
            (1952.4899, 193.5547),
            (1952.4023, 191.8232),
            (1952.1649, 190.1042),
            (1951.7784, 188.409),
            (1951.2447, 186.75),
            (1950.5733, 185.154),
            (1949.7646, 183.6189),
            (1948.8235, 182.1563),
            (1947.0972, 180.0374),
            (1946.5594, 179.5296),
            (1945.2972, 178.3375),
            (1943.9148, 177.2835),
            (1942.4356, 176.3474),
            (1940.9036, 175.5551),
            (1939.2946, 174.8924),
            (1937.6387, 174.3731),
            (1934.218,  173.7731),
            (1933.625,  173.7731),
            (1930.7448, 173.7731),
            (1927.3235, 174.3731),
            (1924.0572, 175.5551),
            (1921.0443, 177.2835),
            (1918.3755, 179.5063),
            (1916.1316, 182.1563),
            (1915.1985, 183.6036),
            (1914.38,   185.154),
            (1913.7083, 186.7488),
            (1913.1735, 188.409),
            (1912.7879, 190.0963),
            (1912.5488, 191.8232),
            (1912.4611, 193.5549),
            (1912.5246, 195.2939),
            (1912.7412, 197.0342),
            (1913.1015, 198.7165),
            (1913.6125, 200.3828),
            (1914.2622, 201.988),
            (1915.0603, 203.5518),
            (1915.9718, 205.0098),
            (1918.1786, 207.6909),
            (1921.0341, 210.6038),
            (1926.6177, 216.2998),
            close=True,
        )
    _cut10_edges = list(BuildSketch._get_context().pending_edges)

_cut10_wire = Wire.combine(_cut10_edges)[0]
_cut10_wire = _cut10_wire.moved(_cut10_sk_plane.location)
_cut10_mkf = BRepBuilderAPI_MakeFace(_cut10_sk_plane.wrapped, _cut10_wire.wrapped, True)
_cut10_face = Face(_cut10_mkf.Face())

# --- Cut11 profile: plane at x=2010.8574 (min x), cut 22mm in +x ---
_cut11_sk_plane = Plane(
    origin=Vector(2010.8574, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_cut11_sk_plane) as _sk_cut11:
    with BuildLine():
        Polyline(
            (1932.33,   207.9902),
            (1939.4748, 200.6943),
            (1940.5768, 199.3537),
            (1941.4305, 197.8428),
            (1942.01,   196.2071),
            (1942.2981, 194.4958),
            (1942.2861, 192.7604),
            (1941.974,  191.0533),
            (1941.3718, 189.4258),
            (1940.497,  187.927),
            (1939.3764, 186.6019),
            (1938.0435, 185.4906),
            (1936.5387, 184.6264),
            (1934.9071, 184.0354),
            (1933.1978, 183.7354),
            (1931.4624, 183.7354),
            (1929.7531, 184.0354),
            (1928.1215, 184.6264),
            (1926.6165, 185.4906),
            (1925.2838, 186.6019),
            (1924.1631, 187.927),
            (1923.2884, 189.4258),
            (1922.686,  191.0533),
            (1922.3741, 192.7604),
            (1922.3619, 194.4958),
            (1922.6501, 196.2071),
            (1923.2297, 197.8428),
            (1924.0834, 199.3537),
            (1925.1854, 200.6943),
            close=True,
        )
    _cut11_edges = list(BuildSketch._get_context().pending_edges)

_cut11_wire = Wire.combine(_cut11_edges)[0]
_cut11_wire = _cut11_wire.moved(_cut11_sk_plane.location)
_cut11_mkf = BRepBuilderAPI_MakeFace(_cut11_sk_plane.wrapped, _cut11_wire.wrapped, True)
_cut11_face = Face(_cut11_mkf.Face())

# --- Cut12 profile: plane at x=2350.8568 (min x), cut in +x to x=2500 ---
_cut12_sk_plane = Plane(
    origin=Vector(2350.8568, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_cut12_sk_plane) as _sk_cut12:
    with BuildLine():
        Polyline(
            (1931.6927, 245.9902),
            (1938.8374, 238.6943),
            (1939.9394, 237.3537),
            (1940.7932, 235.8428),
            (1941.3727, 234.2071),
            (1941.6608, 232.4958),
            (1941.6487, 230.7604),
            (1941.3367, 229.0533),
            (1940.7344, 227.4258),
            (1939.8596, 225.927),
            (1938.739,  224.6019),
            (1937.4062, 223.4906),
            (1935.9013, 222.6264),
            (1934.2697, 222.0354),
            (1932.5604, 221.7354),
            (1930.825,  221.7354),
            (1929.1158, 222.0354),
            (1927.4841, 222.6264),
            (1925.9792, 223.4906),
            (1924.6465, 224.6019),
            (1923.5257, 225.927),
            (1922.6511, 227.4258),
            (1922.0486, 229.0533),
            (1921.7368, 230.7604),
            (1921.7245, 232.4958),
            (1922.0128, 234.2071),
            (1922.5923, 235.8428),
            (1923.446,  237.3537),
            (1924.548,  238.6943),
            close=True,
        )
    _cut12_edges = list(BuildSketch._get_context().pending_edges)

_cut12_wire = Wire.combine(_cut12_edges)[0]
_cut12_wire = _cut12_wire.moved(_cut12_sk_plane.location)
_cut12_mkf = BRepBuilderAPI_MakeFace(_cut12_sk_plane.wrapped, _cut12_wire.wrapped, True)
_cut12_face = Face(_cut12_mkf.Face())

# --- Cut13 profile: plane at x=2372.838 (min x), cut in +x to x=2500 ---
_cut13_sk_plane = Plane(
    origin=Vector(2372.838, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_cut13_sk_plane) as _sk_cut13:
    with BuildLine():
        Polyline(
            (1931.6515, 260.2828),
            (1917.3621, 245.6909),
            (1915.1581, 243.0098),
            (1913.4506, 239.988),
            (1912.2914, 236.7165),
            (1911.7152, 233.2939),
            (1911.7395, 229.8232),
            (1912.3634, 226.409),
            (1913.5683, 223.154),
            (1915.3175, 220.1563),
            (1917.5587, 217.5062),
            (1920.2245, 215.2835),
            (1923.2343, 213.5551),
            (1926.4977, 212.3731),
            (1929.9161, 211.7731),
            (1933.3868, 211.7731),
            (1936.8054, 212.3731),
            (1940.0687, 213.5551),
            (1943.0785, 215.2835),
            (1945.7442, 217.5062),
            (1947.9854, 220.1563),
            (1949.7348, 223.154),
            (1950.9395, 226.409),
            (1951.5634, 229.8232),
            (1951.5877, 233.2939),
            (1951.0115, 236.7165),
            (1949.8523, 239.988),
            (1948.145,  243.0098),
            (1945.9409, 245.6909),
            close=True,
        )
    _cut13_edges = list(BuildSketch._get_context().pending_edges)

_cut13_wire = Wire.combine(_cut13_edges)[0]
_cut13_wire = _cut13_wire.moved(_cut13_sk_plane.location)
_cut13_mkf = BRepBuilderAPI_MakeFace(_cut13_sk_plane.wrapped, _cut13_wire.wrapped, True)
_cut13_face = Face(_cut13_mkf.Face())

# --- Cut14 profile: plane at x=2035 (offset into cavity), cut in -x to x=1900 ---
_cut14_sk_plane = Plane(
    origin=Vector(2035.0, 0.0, 0.0),
    x_dir=Vector(0.0, 1.0, 0.0),
    z_dir=Vector(1.0, 0.0, 0.0),
)
with BuildSketch(_cut14_sk_plane) as _sk_cut14:
    with BuildLine():
        Polyline(
            (1932.2888, 207.9902),
            (1925.1442, 200.6943),
            (1924.0421, 199.3537),
            (1923.1885, 197.8428),
            (1922.6088, 196.2071),
            (1922.3207, 194.4958),
            (1922.3329, 192.7604),
            (1922.6448, 191.0533),
            (1923.2472, 189.4258),
            (1924.1219, 187.927),
            (1925.2425, 186.6019),
            (1926.5753, 185.4906),
            (1928.0803, 184.6264),
            (1929.7119, 184.0354),
            (1931.4212, 183.7354),
            (1933.1566, 183.7354),
            (1934.8657, 184.0354),
            (1936.4973, 184.6264),
            (1938.0023, 185.4906),
            (1939.3352, 186.6019),
            (1940.4558, 187.927),
            (1941.3304, 189.4258),
            (1941.9328, 191.0533),
            (1942.2569, 194.4958),
            (1941.9688, 196.2071),
            (1941.3892, 197.8428),
            (1940.5356, 199.3537),
            (1939.4336, 200.6943),
            close=True,
        )
    _cut14_edges = list(BuildSketch._get_context().pending_edges)

_cut14_wire = Wire.combine(_cut14_edges)[0]
_cut14_wire = _cut14_wire.moved(_cut14_sk_plane.location)
_cut14_mkf = BRepBuilderAPI_MakeFace(_cut14_sk_plane.wrapped, _cut14_wire.wrapped, True)
_cut14_face = Face(_cut14_mkf.Face())

# --- Cut7 profile: plane at x=2449.2961 (max x), normal=+x; cut 33mm in -x ---
_cut7_max_x = 2449.2961
_cut7_gp_pln = gp_Pln(gp_Ax3(
    gp_Pnt(_cut7_max_x, 0.0, 0.0),
    gp_Dir(1.0, 0.0, 0.0),
    gp_Dir(0.0, 1.0, 0.0),
))
_cut7_pts = [
    (2136.5086, 260.2828),
    (2122.2192, 245.6909),
    (2120.0151, 243.0098),
    (2118.3078, 239.988),
    (2117.1486, 236.7165),
    (2116.5724, 233.2939),
    (2116.5967, 229.8232),
    (2117.2206, 226.409),
    (2118.4254, 223.154),
    (2120.1747, 220.1563),
    (2122.4159, 217.5062),
    (2125.0816, 215.2835),
    (2128.0914, 213.5551),
    (2131.3548, 212.3731),
    (2134.7733, 211.7731),
    (2138.244,  211.7731),
    (2141.6626, 212.3731),
    (2144.9258, 213.5551),
    (2147.9356, 215.2835),
    (2150.6013, 217.5062),
    (2152.8426, 220.1563),
    (2154.592,  223.154),
    (2155.7967, 226.409),
    (2156.4206, 229.8232),
    (2156.4449, 233.2939),
    (2156.0086, 236.1417),
    (2154.7095, 239.988),
    (2153.0022, 243.0098),
    (2150.798,  245.6909),
]
_cut7_poly = BRepBuilderAPI_MakePolygon()
for (py, pz) in _cut7_pts:
    _cut7_poly.Add(gp_Pnt(_cut7_max_x, py, pz))
_cut7_poly.Close()
_cut7_mkf = BRepBuilderAPI_MakeFace(_cut7_gp_pln, _cut7_poly.Wire())
_cut7_face = Face(_cut7_mkf.Face())

# --- 8 diamond cut profiles along Y axis (at y≈2236, cut in -y direction) ---
# Plane: normal=-y (gp_Dir(0,-1,0)), x-axis=worldX, y-axis=worldZ
# Points given as (worldX, worldZ); projected onto plane at max_y of each profile
_diamond_cut_data = [
    # (max_y, [(x1,z1),(x2,z2),(x3,z3),(x4,z4)])  -- original point order
    (2236.3046, [(2315.4463,280.2057),(2339.4463,255.6977),(2315.4463,231.1897),(2291.4464,255.6977)]),
    (2236.4584, [(2257.4464,255.6977),(2233.4465,231.1897),(2209.4464,255.6977),(2233.4465,280.2057)]),
    (2236.6121, [(2151.4465,280.2057),(2175.4465,255.6977),(2151.4465,231.1897),(2127.4466,255.6977)]),
    (2236.7657, [(2069.4467,280.2057),(2093.4467,255.6977),(2069.4467,231.1897),(2045.4468,255.6977)]),
    (2236.3046, [(2315.4463,180.2057),(2339.4463,155.6977),(2315.4463,131.1897),(2291.4464,155.6977)]),
    (2236.4584, [(2233.4465,180.2057),(2257.4464,155.6977),(2233.4465,131.1897),(2209.4464,155.6977)]),
    (2236.6121, [(2151.4465,180.2057),(2175.4465,155.6977),(2151.4465,131.1897),(2127.4466,155.6977)]),
    (2236.7657, [(2069.4467,180.2057),(2093.4467,155.6977),(2069.4467,131.1897),(2045.4468,155.6977)]),
]
# --- Add5 profile: plane at z=65.6977, normal=+z; extrude to z=334.83978271 ---
_add5_plane = Plane(
    origin=Vector(0.0, 0.0, 65.6977),
    x_dir=Vector(1.0, 0.0, 0.0),
    z_dir=Vector(0.0, 0.0, 1.0),
)
with BuildSketch(_add5_plane) as _sk_add5:
    with BuildLine():
        Polyline(
            (2408.7694, 1875.0841),
            (2408.6562, 1873.7576),
            (2408.3244, 1872.4683),
            (2407.7835, 1871.2518),
            (2407.0483, 1870.1419),
            (2406.1394, 1869.1692),
            (2405.0816, 1868.3607),
            (2403.9044, 1867.739),
            (2402.6404, 1867.321),
            (2401.3246, 1867.1184),
            (2399.9934, 1867.1368),
            (2398.6838, 1867.3758),
            (2397.4318, 1867.8285),
            (2396.2723, 1868.4827),
            (2395.2373, 1869.3202),
            (2394.3556, 1870.3175),
            (2393.6514, 1871.4474),
            (2393.5623, 1871.5901),
            (2393.4505, 1871.7159),
            (2393.3192, 1871.8211),
            (2393.1721, 1871.9029),
            (2393.0135, 1871.9588),
            (2392.8477, 1871.9873),
            (2392.6794, 1871.9876),
            (2392.5136, 1871.9597),
            (2392.3546, 1871.9044),
            (2392.2072, 1871.8231),
            (2392.0755, 1871.7184),
            (2391.9633, 1871.5932),
            (2391.8736, 1871.4508),
            (2391.1565, 1870.3117),
            (2390.2583, 1869.3092),
            (2389.205,  1868.4714),
            (2388.026,  1867.822),
            (2386.7549, 1867.3793),
            (2385.4276, 1867.1562),
            (2384.0814, 1867.1587),
            (2382.755,  1867.3869),
            (2381.4854, 1867.8342),
            (2380.309,  1868.488),
            (2379.2587, 1869.3298),
            (2378.3644, 1870.3358),
            (2377.6515, 1871.4774),
            (2377.5624, 1871.6202),
            (2377.4506, 1871.7459),
            (2377.3193, 1871.851),
            (2377.1722, 1871.9328),
            (2377.0135, 1871.9888),
            (2376.8477, 1872.0172),
            (2376.5135, 1871.9897),
            (2376.3547, 1871.9344),
            (2376.2073, 1871.8532),
            (2376.0756, 1871.7485),
            (2375.9633, 1871.6231),
            (2375.8737, 1871.4807),
            (2375.1653, 1870.3535),
            (2374.2798, 1869.3594),
            (2373.2417, 1868.5258),
            (2372.0798, 1867.8761),
            (2370.8261, 1867.428),
            (2369.5155, 1867.1939),
            (2368.1844, 1867.1805),
            (2366.8692, 1867.388),
            (2365.6068, 1867.8107),
            (2364.4321, 1868.4369),
            (2363.3774, 1869.2494),
            (2362.4719, 1870.2254),
            (2361.7409, 1871.338),
            (2361.2045, 1872.5566),
            (2360.8777, 1873.8472),
            (2360.7695, 1875.1741),
            (2360.8211, 1902.7283),
            (2408.8211, 1902.6384),
            close=True,
        )
    _add5_edges = list(BuildSketch._get_context().pending_edges)

_add5_wire = Wire.combine(_add5_edges)[0]
_add5_wire = _add5_wire.moved(_add5_plane.location)
_add5_mkf = BRepBuilderAPI_MakeFace(_add5_plane.wrapped, _add5_wire.wrapped, True)
_add5_face = Face(_add5_mkf.Face())

_diamond_cut_faces = []
for _d_max_y, _d_pts in _diamond_cut_data:
    _d_gp_pln = gp_Pln(gp_Ax3(
        gp_Pnt(0.0, _d_max_y, 0.0),
        gp_Dir(0.0, -1.0, 0.0),   # normal = -y
        gp_Dir(1.0, 0.0, 0.0),    # local x = world X
    ))
    _d_poly = BRepBuilderAPI_MakePolygon()
    for (px, pz) in _d_pts:
        _d_poly.Add(gp_Pnt(px, _d_max_y, pz))
    _d_poly.Close()
    _d_mkf = BRepBuilderAPI_MakeFace(_d_gp_pln, _d_poly.Wire())
    _diamond_cut_faces.append(Face(_d_mkf.Face()))

with BuildPart() as part:
    # Extrude till z = 205.69766998
    # vector Z magnitude = 205.69766998 - 345.6977 = -140.00003002
    _vec = Vector(0.0, 0.0, 1.0) * (-140.00003002)
    _solid = Solid.extrude(_face, _vec)
    add(_solid)

    # Fillet all edges at z=345.69766998 except the excluded edge
    _target_z = 345.69766998
    _edges_to_fillet = [
        e for e in part.part.edges()
        if all(_near(v.Z, _target_z) for v in e.vertices())
        and not _is_excluded_edge(e)
    ]
    fillet(_edges_to_fillet, radius=10)

    # Record existing edge keys at target_z before cut
    _pre_cut_keys = {
        _edge_key(e) for e in part.part.edges()
        if all(_near(v.Z, _target_z) for v in e.vertices())
    }

    # Extrude cut profile downward through entire body (355.6977 -> below 205.6977)
    _cut_vec = Vector(0.0, 0.0, 1.0) * (-160.0)
    _cut_solid = Solid.extrude(_cut_face, _cut_vec)
    add(_cut_solid, mode=Mode.SUBTRACT)

    # Fillet only the NEW edges at z=345.69766998 formed by the cut
    _post_cut_edges = [
        e for e in part.part.edges()
        if all(_near(v.Z, _target_z) for v in e.vertices())
        and _edge_key(e) not in _pre_cut_keys
    ]
    fillet(_post_cut_edges, radius=10)

    # Mirror about z=205.69766998
    _mirror_plane = Plane(
        origin=Vector(0.0, 0.0, 205.69766998),
        x_dir=Vector(1.0, 0.0, 0.0),
        z_dir=Vector(0.0, 0.0, 1.0),
    )
    mirror(about=_mirror_plane)

    # Extrude add3 profile in +x from x=2369.9002 to x=2418.93997192
    _add3_dist = 2418.93997192 - 2369.9002  # ~49.04mm
    _add3_solid = Solid.extrude(_add3_face, Vector(1.0, 0.0, 0.0) * _add3_dist)
    add(_add3_solid)

    # Extrude add4 profile in +x from x=2369.9002 to x=2428.88292073
    # Record edges at z=65.6977 before adding
    _target_z4 = 65.6977
    _pre_add4_keys = {
        _edge_key(e) for e in part.part.edges()
        if all(_near(v.Z, _target_z4) for v in e.vertices())
    }
    _add4_dist = 2428.88292073 - 2369.9002  # ~58.98mm
    _add4_solid = Solid.extrude(_add4_face, Vector(1.0, 0.0, 0.0) * _add4_dist)
    add(_add4_solid)

    # Fillet new edges at z=65.6977 formed by add4 (one at a time to handle short edges)
    _post_add4_edges = [
        e for e in part.part.edges()
        if all(_near(v.Z, _target_z4) for v in e.vertices())
        and _edge_key(e) not in _pre_add4_keys
    ]
    for _e4 in _post_add4_edges:
        try:
            fillet([_e4], radius=10)
        except Exception:
            pass

    # Fillet edges defined by specific endpoint pairs
    def _find_edge_by_pts(solid, pt_a, pt_b, tol=0.1):
        for e in solid.edges():
            verts = e.vertices()
            if len(verts) < 2:
                continue
            coords = [(v.X, v.Y, v.Z) for v in verts]
            def _pt_near(c, p):
                return _near(c[0], p[0]) and _near(c[1], p[1]) and _near(c[2], p[2])
            if ((_pt_near(coords[0], pt_a) and _pt_near(coords[1], pt_b)) or
                (_pt_near(coords[0], pt_b) and _pt_near(coords[1], pt_a))):
                return e
        return None

    _spec_edge1 = _find_edge_by_pts(part.part,
        (2428.8829, 1964.7104, 65.6977),
        (2369.9002, 1964.7104, 65.6977))
    _spec_edge2 = _find_edge_by_pts(part.part,
        (2369.9002, 1964.7104, 65.6977),
        (2369.9002, 1936.1744, 65.6977))

    for _se in [_spec_edge1, _spec_edge2]:
        if _se is not None:
            try:
                fillet([_se], radius=10)
            except Exception:
                pass

    # Cut 8 diamond profiles through body along -y direction
    for _d_face in _diamond_cut_faces:
        _d_solid = Solid.extrude(_d_face, Vector(0.0, -1.0, 0.0) * 400.0)
        add(_d_solid, mode=Mode.SUBTRACT)

    # Cut7: extrude profile 33mm in -x direction
    _cut7_solid = Solid.extrude(_cut7_face, Vector(-1.0, 0.0, 0.0) * 33.0)
    add(_cut7_solid, mode=Mode.SUBTRACT)

    # Extrude add5 profile from z=65.6977 to z=342.76870728
    _add5_dist = 342.76870728 - 65.6977  # = 277.07100728mm
    _add5_solid = Solid.extrude(_add5_face, Vector(0.0, 0.0, 1.0) * _add5_dist)
    add(_add5_solid)

    # Cut6: extrude profile through body in -x direction (after add5 so it cuts add5 material)
    _cut6_solid = Solid.extrude(_cut6_face, Vector(-1.0, 0.0, 0.0) * 500.0)
    add(_cut6_solid, mode=Mode.SUBTRACT)

    # Cut9: extrude profile 30mm in +x direction (inward from left wall)
    _cut9_solid = Solid.extrude(_cut9_face, Vector(1.0, 0.0, 0.0) * 32.0)
    add(_cut9_solid, mode=Mode.SUBTRACT)

    # Cut14: extrude in -x from x=2035 to x=1900
    _cut14_dist = 2035.0 - 1900.0  # 135mm
    _cut14_solid = Solid.extrude(_cut14_face, Vector(-1.0, 0.0, 0.0) * _cut14_dist)
    add(_cut14_solid, mode=Mode.SUBTRACT)

    # Cut13: extrude in +x from x=2372.838 to x=2500
    _cut13_dist = 2500.0 - 2372.838  # ~127.16mm
    _cut13_solid = Solid.extrude(_cut13_face, Vector(1.0, 0.0, 0.0) * _cut13_dist)
    add(_cut13_solid, mode=Mode.SUBTRACT)

    # Cut12: extrude in +x from x=2350.8568 to x=2500
    _cut12_dist = 2500.0 - 2350.8568  # ~149.14mm
    _cut12_solid = Solid.extrude(_cut12_face, Vector(1.0, 0.0, 0.0) * _cut12_dist)
    add(_cut12_solid, mode=Mode.SUBTRACT)

    # Cut11: extrude 22mm in +x
    _cut11_solid = Solid.extrude(_cut11_face, Vector(1.0, 0.0, 0.0) * 22.0)
    add(_cut11_solid, mode=Mode.SUBTRACT)

    # Cut10: extrude profile in +x from x=1925.3665 to x=2010.91339111
    _cut10_dist = 2010.91339111 - 1925.3665  # ~85.55mm
    _cut10_solid = Solid.extrude(_cut10_face, Vector(1.0, 0.0, 0.0) * _cut10_dist)
    add(_cut10_solid, mode=Mode.SUBTRACT)

export_step(part.part, "/Users/softage/Documents/5may/Print_Follower_SO_ARM100_08k_UP_Prusa - SO_ARM100_08k-3.step")
export_stl(part.part, "/Users/softage/Documents/5may/Print_Follower_SO_ARM100_08k_UP_Prusa - SO_ARM100_08k-3.stl")
