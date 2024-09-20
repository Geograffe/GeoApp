from shapely.geometry import Polygon, MultiPolygon, Point

def load_polygons_from_geojson_within_extents(gdf, extents_polygon):
    polygons = []
    for _, row in gdf.iterrows():
        geometry = row['geometry']
        name = row.get('Name', 'Unnamed Park')  # Assuming the name field is 'Name'
        if isinstance(geometry, (Polygon, MultiPolygon)):
            if geometry.intersects(extents_polygon):
                centroid = geometry.centroid if isinstance(geometry, Polygon) else geometry.representative_point()
                polygons.append({
                    'coordinates': list(geometry.exterior.coords) if isinstance(geometry, Polygon) else 
                                   [list(poly.exterior.coords) for poly in geometry.geoms],
                    'description': row.get('Description', 'No description available'),
                    'name': name,
                    'centroid': (centroid.y, centroid.x)  # (lat, lon)
                })
    return polygons
