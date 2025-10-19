import folium
import pandas as pd

from folium.plugins import TimestampedGeoJson

def draw_multiship_routes(csv_path, output_html_path):
    df = pd.read_csv(csv_path, parse_dates=['postime'])
    required_cols = ['lat', 'lon', 'postime', 'mmsi']
    map_center = [df['lat'].mean(), df['lon'].mean()]
    m = folium.Map(location=map_center, zoom_start=6)

    folium.TileLayer('CartoDB positron', name='简洁地图', attr='default').add_to(m)
    folium.TileLayer('Stamen Terrain', name='地形图', attr='default').add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='卫星影像'
    ).add_to(m)

    colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred', 'cadetblue', 'darkpurple']
    all_features = []
    grouped = df.groupby('mmsi')

    for i, (ship_id, group_df) in enumerate(grouped):
        color = colors[i % len(colors)]

        ship_layer = folium.FeatureGroup(name=f"静态路线: {ship_id}")

        group_df = group_df.sort_values(by='postime').reset_index(drop=True)

        points = list(zip(group_df['lat'], group_df['lon']))

        folium.PolyLine(
            locations=points,
            color=color,
            weight=3,
            opacity=0.7
        ).add_to(ship_layer)

        ship_layer.add_to(m)


        point_features = []
        for _, row in group_df.iterrows():
            point_features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [row['lon'], row['lat']]},
                'properties': {
                    'time': row['postime'].isoformat(),
                    'icon': 'circle',
                    'iconstyle': {'fillColor': color, 'fillOpacity': 0.8, 'stroke': 'true', 'radius': 7},
                    'popup': f"<b>{row.get('mmsi', ship_id)}</b><br>{row['postime'].strftime('%Y-%m-%d %H:%M')}<br>Lat: {row['lat']} <br>Lon: {row['lon']}"
                }
            })


        line_coordinates = list(zip(group_df['lon'], group_df['lat']))
        line_times = [dt.isoformat() for dt in group_df['postime']]
        line_feature = {
            'type': 'Feature',
            'geometry': {'type': 'LineString', 'coordinates': line_coordinates},
            'properties': {'times': line_times, 'style': {'color': color, 'weight': 5}}
        }

        all_features.extend(point_features)
        all_features.append(line_feature)

    if all_features:
        TimestampedGeoJson(
            {'type': 'FeatureCollection', 'features': all_features},
            period='PT5M',
            add_last_point=True,
            auto_play=False,
            loop=False,
            max_speed=5,
            loop_button=True,
            time_slider_drag_update=True,
        ).add_to(m)

    folium.LayerControl().add_to(m)

    m.save(output_html_path)

if __name__ == "__main__":
    csv_file = 'ships_routes.csv'
    output_html_file = 'multiship_route_map.html'

    draw_multiship_routes(csv_file, output_html_file)