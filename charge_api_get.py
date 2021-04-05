import requests
import json
import geopandas as gpd
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import passwords

ago_url = "https://semcog.maps.arcgis.com"
gis = GIS(ago_url, passwords.user_name, passwords.password)

r = requests.get(
    'https://developer.nrel.gov/api/alt-fuel-stations/v1.geojson?fuel_type=ELEC&state=MI&api_key=dfi1k14gwsgv5PkXuzpdD62zHoTv2ZUQm4N4tJ5j')
data = r.json()

for feature in data['features']:
    if feature['properties']['ev_connector_types']:
        feature['properties']['ev_connector_types'] = ', '.join(feature['properties']['ev_connector_types'])

with open('charge_points.geojson', 'w') as charge_points:
    json.dump(data, charge_points)

charge_points_file = gpd.read_file('charge_points.geojson')
mcds = gpd.read_file('mcds.geojson')
join = gpd.sjoin(charge_points_file, mcds, how="inner", op="intersects")

used_columns = ['access_code', 'access_days_time', 'access_detail_code',
                'cards_accepted', 'date_last_confirmed', 'expected_date',
                'fuel_type_code', 'groups_with_access_code', 'id', 'open_date',
                'owner_type_code', 'status_code', 'station_name', 'station_phone',
                'updated_at', 'facility_type', 'geocode_status', 'city',
                'intersection_directions', 'plus4', 'state', 'street_address', 'zip',
                'country', 'ev_dc_fast_num', 'ev_level1_evse_num',
                'ev_level2_evse_num', 'ev_network', 'ev_network_web', 'ev_other_evse',
                'ev_pricing', 'ev_renewable_source', 'ev_network_ids', 'ev_connector_types',
                'federal_agency', 'geometry',
                'SEMMCD', 'NAME', 'COUNTY', 'county_name']
join_cleaned = join[used_columns]
join_cleaned.to_file('charge_points_region.geojson', driver='GeoJSON', RFC7946='YES')

charge_layer = gis.content.search('title:charge_points_semcog owner:makari_SEMCOG type:Feature Service')

# to init a feature layer
if not charge_layer:
    print('publishing new charge layer')
    item_prop = {'title': 'charge_points_semcog', 'type': 'GeoJson', 'overwrite': 'true'}
    geojson_item = gis.content.add(item_properties=item_prop, data='charge_points_region.geojson')
    charge_points_item = geojson_item.publish()
    charge_points_item.share(org=True, everyone=False)
    charge_points_item.reassign_to(target_owner='makari_SEMCOG')
else:
    print('overwriting charge layer')
    charge_points_flayer_collection = FeatureLayerCollection.fromitem(charge_layer[0])
    charge_points_flayer_collection.manager.overwrite('charge_points_region.geojson')
