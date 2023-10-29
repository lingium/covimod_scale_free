import os
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

from pathlib import Path
args = {}
args['cwd'] = Path(__file__).resolve().parent.parent.parent
args['data'] = args['cwd'] / "data"
args['csv_dir'] = args['data'] / 'covimod'
args['derived_dir'] = args['data'] / 'derived'
args['fig_dir'] = args['cwd'] / "figures"

# load csv files
df_part = pd.read_csv(os.path.join(args['csv_dir'], "part_data.csv"))


# get the the mapping between region name and coordinates
# this takes time to run, so we save the result to pickle

# from geopy.geocoders import Nominatim
# # Create a geocoder instance
# geolocator = Nominatim(user_agent="my_app")
# # List of region names
# regions = df_part['kreis_0'].unique()
# # Create a dictionary to store the region coordinates
# region_coordinates = {}

# # Iterate over the region names and geocode each region
# for region in regions:
#     # Geocode the region
#     location = geolocator.geocode(region + ", Germany")
#     print(location)
#     # Extract latitude and longitude from the location
#     if location:
#         lat, lon = location.latitude, location.longitude
#         region_coordinates[region] = (lat, lon)

# # save to pickle
# import pickle
# with open(args['derived_dir'] / 'region_coordinates.pkl', 'wb') as f:
#     pickle.dump(region_coordinates, f)



# directly load geo mapping from pickle
import pickle
with open(args['derived_dir'] / 'region_coordinates.pkl', 'rb') as f:
    region_coordinates = pickle.load(f)

df_region_coordinates = pd.DataFrame.from_dict(region_coordinates, orient='index', columns=['lat', 'lon'])
df_region_coordinates.reset_index(inplace=True)
df_region_coordinates.rename(columns={'index': 'pt_region'}, inplace=True)

dpart = pd.read_csv(os.path.join(args['derived_dir'], 'dpart.csv'))
dpart = pd.merge(dpart, df_region_coordinates, how='left', on='pt_region')
dpart = dpart.dropna(subset=['lat', 'lon'])

# count number of participants in each region
df_part_count = dpart.groupby(['pt_region', 'lat', 'lon']).size().reset_index(name='count')



# -------------------------- Geographic distribution of participants --------------------------
import networkx as nx
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Create a dictionary of node locations with latitude and longitude
nodes_locations = {}
for i in range(len(df_part_count)):
    ID = df_part_count['pt_region'][i]
    lon = df_part_count['lon'][i]
    lat = df_part_count['lat'][i]
    nodes_locations[ID] = (lon,lat)

# Initialize a Graph object and add edges to it
G = nx.Graph()
for i in range(len(df_part_count)):
    G.add_node(df_part_count['pt_region'][i])

palette = sns.color_palette("deep", 10)

# Create a Europe map using Cartopy
fig = plt.figure(figsize=(7, 7))
ax = plt.axes(projection=ccrs.PlateCarree())
# Set the desired map extent
ax.set_extent([5, 16, 47, 56])
# Add map features (coastlines, land, oceans, etc.)
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.LAND)
ax.add_feature(cfeature.OCEAN)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAKES, alpha=0.5)

nx.draw_networkx_nodes(
    G,
    pos=nodes_locations,
    # nodelist=list(layouts.keys()),
    node_size=df_part_count['count'] * 0.2,
    node_color=[palette[2]]*len(G),
    edgecolors=palette[0],
    linewidths=0.6,
    ax=ax,
)
# plt.title("Geographic distribution of participants")
plt.savefig(args['fig_dir'] / 'data' / "fig_3.pdf")




