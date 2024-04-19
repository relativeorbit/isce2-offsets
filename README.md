# isce2-offsets
SAR ISCE2 offset workflow for [CryoCloud](https://book.cryointhecloud.com/intro.html)

This repository runs ISCE2 denseOffsets via GitHub Actions and stages results for *90 days*. These results can be accessed on CyroCloud JupyterHub (or other computers) for analysis and interpretation.

## Usage

By default the workflow AOI uses a polygon covering shirase glacier in antarctica and you only need to specify the pair of absolute orbits to process:

### Single pair

```
gh -R relativeorbit/isce2-offsets workflow run pair.yml \
  -f reference=052893 \
  -f secondary=053418 \
```

### Timeseries

Instead of explicitly identifying a pair of orbits, search ASF and chose one pair per month from all available acquisitions and process them in parallel

```
gh -R relativeorbit/isce2-offsets workflow run timeseries.yml 
```

## Download

ISCE2 does not produce cloud-optimized geotiffs, so it's most efficient to download and work with them locally. NOTE: GitHub workflow artifacts are publically accessible to anyone with a GitHub account.

```
# Pick a workflow ID (e.g. 8072975855)
gh -R relativeorbit/isce2-offsets run list -w offset_pair.yml

# Download to temporary scratch space
gh -R relativeorbit/isce2-offsets run download 8072975855 --dir /tmp/052893_053418
```