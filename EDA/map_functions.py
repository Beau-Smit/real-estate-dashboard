import folium
import geopy.distance
import pandas as pd


def add_map_marker(m, lat, lon, name="NA", color="blue", icon="map-marker"):
    marker = folium.Marker(
        location=[lat, lon],
        popup=name,
        icon=folium.Icon(color=color, icon=icon, prefix="fa"),
    )
    # icon list: https://getbootstrap.com/docs/3.3/components/
    return marker


def add_map_circle(m, lat, lon, radius=800):
    # radius parameter in meters
    folium.Circle(
        location=[lat, lon],
        radius=radius,  # 800 meters = 0.5 miles
        color="red",
        fill=True,
        fill_color="red",
    ).add_to(m)


def get_closest(coords_1_lat, coords_1_lon, coords_2_lat, coords_2_lon):
    shortest_distance_lst = []
    for coord_1 in zip(coords_1_lat, coords_1_lon):
        shortest_distance = 10  # arbitrarily chosen
        for coord_2 in zip(coords_2_lat, coords_2_lon):
            dist = geopy.distance.geodesic(coord_1, coord_2).miles
            if dist < shortest_distance:
                shortest_distance = dist
        shortest_distance_lst.append(shortest_distance)
    return pd.Series(shortest_distance_lst)


def count_points_within_range(
    coords_1_lat, coords_1_lon, coords_2_lat, coords_2_lon, within_dist=0.5
):
    # walking distance in miles
    count_lst = []
    for coord_1 in zip(coords_1_lat, coords_1_lon):
        count = 0
        for coord_2 in zip(coords_2_lat, coords_2_lon):
            dist = geopy.distance.geodesic(coord_1, coord_2).miles
            if dist < within_dist:
                count += 1
        count_lst.append(count)
    return pd.Series(count_lst)
