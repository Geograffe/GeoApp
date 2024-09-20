from shapely.geometry import Polygon, MultiPolygon

def load_polygons_from_geojson_within_extents(gdf, extents_polygon):
    polygons = []
    for _, row in gdf.iterrows():
        geometry = row['geometry']
        if isinstance(geometry, (Polygon, MultiPolygon)):
            if geometry.intersects(extents_polygon):
                polygons.append({
                    'coordinates': list(geometry.exterior.coords) if isinstance(geometry, Polygon) else 
                                   [list(poly.exterior.coords) for poly in geometry.geoms],
                    'description': row.get('Description', 'No description available')
                })
    return polygons
