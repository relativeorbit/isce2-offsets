#!/usr/bin/env python
"""
Construct SAFEs from ASF bursts for ISCE2
(Downloads Precise Orbits, DEMs, and prepare ISCE2 topsApp XMLs)

Usage: (to be run from repository rootdir)
export WKT='POLYGON ((40.2120662291117 -70.4784035560571, 40.2120662291117 -69.8946747468079, 38.4742377626362 -69.8946747468079, 38.4742377626362 -70.4784035560571, 40.2120662291117 -70.4784035560571))'
./scripts/burst2topsapp.py --reference 052893 --secondary 053418 --wkt $WKT --pol hh

NOTES: 
if you have geojson, get a WKT: `ogrinfo shirase.geojson -al | grep POLYGON`
"""

import asf_search as asf
import glob
from argparse import ArgumentParser
import subprocess
import shapely
from burst2safe.burst2safe import burst2safe
import eof

def search_asf(wkt, absoluteOrbit, polarization):
    print(f'Searching ASF for {absoluteOrbit} bursts...')
    results = asf.geo_search(
        platform=[asf.PLATFORM.SENTINEL1],
        processingLevel=asf.PRODUCT_TYPE.BURST,
        intersectsWith=wkt,
        polarization=polarization,
        absoluteOrbit=absoluteOrbit,
    )
    # All subswaths
    granules = [r.properties["fileID"] for r in results]
    
    return granules

def fetch_orbits():
    print('Downloading orbits...')
    orbit_files = eof.download.main()
    return orbit_files

def download_dem(wkt, buffer=0.4):
    print('Downloading DEM...')
    poly = shapely.from_wkt(wkt)
    minlon, minlat, maxlon, maxlat =  shapely.box(*poly.bounds).buffer(buffer).bounds
    cmd = f"sardem -isce --data-source COP --bbox {minlon} {minlat} {maxlon} {maxlat}"
    sts = subprocess.Popen(cmd, shell=True).wait()

def prepare_topsApp(reference_safe, secondary_safe, subswaths, polarization):
    # Better to use jinja2 for templating
    # https://github.com/ASFHyP3/hyp3-isce2/blob/040addfb8291c5b2041bcf3ca5b90d8faf493097/src/hyp3_isce2/topsapp.py#L98
    print('Creating topsApp XML config files...')
    with open('templates/topsApp.xml') as f:
        template = f.read()
        filled = template.replace('{{SWATH_LIST}}', str(subswaths))
        with open('topsApp.xml', 'w') as f:
            f.write(filled)   
    
    with open('templates/reference.xml') as f:
        template = f.read()
        filled = template.replace('{{REFERENCE_SAFE}}', reference_safe).replace('{{POL}}', polarization)
        with open('reference.xml', 'w') as f:
            f.write(filled)   

    with open('templates/secondary.xml') as f:
        template = f.read()
        filled = template.replace('{{SECONDARY_SAFE}}', secondary_safe).replace('{{POL}}', polarization)
        with open('secondary.xml', 'w') as f:
            f.write(filled)   

def main():
    parser = ArgumentParser()
    parser.add_argument('--reference', type=int, required=True, help='absolute orbit number of reference scene')
    parser.add_argument('--secondary', type=int, required=True, help='absolute orbit number of secondary scene')
    parser.add_argument('--wkt', type=str, required=True, help='polygon WKT')
    parser.add_argument('--pol', type=str, required=True, help='polarization to process (i.e., vv vh hh)')

    args = parser.parse_args()

    reference_bursts = search_asf(args.wkt, args.reference, args.pol)
    secondary_bursts = search_asf(args.wkt, args.secondary, args.pol)

    print('Constructing SAFE files...')
    burst2safe(granules=reference_bursts)
    burst2safe(granules=secondary_bursts)

    #burst2safe(granules=secondary_bursts)
    # Find SAFEs in current directory and sort ascending by datetime string
    safes = glob.glob('*SAFE')
    safes.sort(key = lambda x: x.split('_')[5])
    reference_safe, secondary_safe = safes

    orbit_paths = fetch_orbits()

    download_dem(args.wkt)
    
    subswaths = list(set([int(g[12]) for g in reference_bursts]))
    prepare_topsApp(reference_safe, secondary_safe, subswaths, args.pol)

    print('Done! ready to run topsApp.py')


if __name__ == '__main__':
    main()