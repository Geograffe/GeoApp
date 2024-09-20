from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import nearest_points

def load_polygons_from_geojson_within_extents(gdf, extents_polygon, user_location):
    polygons = []
    user_point = Point(user_location["longitude"], user_location["latitude"])
    
    for _, row in gdf.iterrows():
        geometry = row['geometry']
        if isinstance(geometry, (Polygon, MultiPolygon)):
            if geometry.intersects(extents_polygon):
                # Find the nearest point on the polygon to the user's current location
                nearest_point = nearest_points(geometry, user_point)[0]
                
                # Handle both Polygon and MultiPolygon types
                if isinstance(geometry, Polygon):
                    polygons.append({
                        'coordinates': list(geometry.exterior.coords),
                        'description': row.get('Description', 'No description available')
                    })
                elif isinstance(geometry, MultiPolygon):
                    polygons.append({
                        'coordinates': [list(poly.exterior.coords) for poly in geometry.geoms],
                        'description': row.get('Description', 'No description available')
                    })
    return polygons
