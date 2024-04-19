'''
Search ASF for bursts and create N+2 pairs

export POLYGON='POLYGON ((38.6401149641734 -69.9149589283716,38.0950151069544 -70.0278414394631,39.3056438596154 -70.5135264611673,40.1296320158775 -70.3031189013304,38.6401149641734 -69.9149589283716))'
GITHUB_OUTPUT=github_outputs.txt POLARIZATION=hh python getBurstPairs.py
'''
import asf_search as asf
import geopandas as gpd
import json
import os

# Parse Workflow inputs from environment variables
POL = os.environ['POLARIZATION']
POLYGON = os.environ['POLYGON']

# Search for Bursts
results = asf.geo_search(
    platform=[asf.PLATFORM.SENTINEL1],
    processingLevel=asf.PRODUCT_TYPE.BURST,
    intersectsWith=POLYGON,
    polarization=POL,
    flightDirection=asf.FLIGHT_DIRECTION.ASCENDING,
)
gf = gpd.GeoDataFrame.from_features(results.geojson(), crs=4326)
print('Number of bursts:', len(gf))

# Just use first burst for selecting orbits
gf['burstID'] = gf.burst.str['fullBurstID']
gf = gf[gf.burstID == gf.burstID.iloc[0]]

# Sort chronological ascending
gf['datetime'] = gpd.pd.to_datetime(gf.startTime)
gf = gf.sort_values(by='datetime', ignore_index=True)

print('Number of Acquisitions: ', len(gf))
burstIDs = gf.sceneName.to_list()
print('\n'.join(burstIDs))

pairs = []
# fairly consistent 12 day repeat cycle, so pick every other for reference and secondary
for i in range(len(gf)-2):
    ref = gf.orbit.iloc[i]
    sec = gf.orbit.iloc[i+2]
    pairs.append({'reference': str(ref), 'secondary': str(sec)})


# Save JSON for GitHub Actions Matrix Job
matrixJSON = f'{{"include":{json.dumps(pairs)}}}'
print(f'Number of Interferograms: {len(pairs)}')
print(matrixJSON)

with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    print(f'BURST_IDS={burstIDs}', file=f)
    print(f'MATRIX_PARAMS_COMBINATIONS={matrixJSON}', file=f)
