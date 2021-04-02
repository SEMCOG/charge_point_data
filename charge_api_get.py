import requests
import json
import pandas as pd
import numpy as np
import geopandas as gpd
import shapely
import fiona
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import passwords

ago_url = "https://semcog.maps.arcgis.com"
gis = GIS(ago_url, passwords.my_user_name, passwords.my_password)

r = requests.get(
    'https://developer.nrel.gov/api/alt-fuel-stations/v1.geojson?fuel_type=ELEC&state=MI&api_key=dfi1k14gwsgv5PkXuzpdD62zHoTv2ZUQm4N4tJ5j')
data = r.json()

with open('charge_points.geojson', 'w') as charge_points:
    json.dump(data, charge_points)

charge_points_file = gpd.read_file('charge_points.geojson')
mcds = gpd.read_file('mcds.geojson')
join = gpd.sjoin(charge_points_file, mcds, how="inner", op="intersects")

used_columns = ['station_name', 'updated_at', 'facility_type', 'geocode_status', 'city',
                'intersection_directions', 'plus4', 'street_address', 'zip',
                'cng_total_storage', 'cng_vehicle_class',
                'ev_pricing', 'geometry',
                'SEMMCD', 'NAME', 'COUNTY']
join_cleaned = join[used_columns]
join_cleaned.to_file('charge_points_region.geojson', driver='GeoJSON', RFC7946='YES')

charge_layer = gis.content.search('title:charge_points_semcog owner:misiuk_SEMCOG type:Feature Service')

# to init a feature layer
if not charge_layer:
    print('publishing new charge layer')
    item_prop = {'title': 'charge_points_semcog', 'type': 'GeoJson', 'overwrite': 'true'}
    geojson_item = gis.content.add(item_properties=item_prop, data='charge_points_region.geojson')
    charge_points_item = geojson_item.publish()
    charge_points_item.share(org=True, everyone=False)
else:
    print('overwriting charge layer')
    charge_points_flayer_collection = FeatureLayerCollection.fromitem(charge_layer[0])
    charge_points_flayer_collection.manager.overwrite('charge_points_region.geojson')
