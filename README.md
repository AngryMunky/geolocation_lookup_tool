# Geolocation Lookup Tool
[![Latest Release](https://img.shields.io/github/v/release/AngryMunky/geolocation_lookup_tool?label=release)](https://github.com/AngryMunky/geolocation_lookup_tool/releases/latest)  [![Build Windows EXE](https://github.com/AngryMunky/geolocation_lookup_tool/actions/workflows/build.yml/badge.svg)](https://github.com/AngryMunky/geolocation_lookup_tool/actions/workflows/build.yml)

Version 1.2.2  
Author: [Angry Munky](https://github.com/AngryMunky)  
Project: [https://github.com/AngryMunky/geolocation_lookup_tool](https://github.com/AngryMunky/geolocation_lookup_tool)

This app geocodes a list of street intersections from a CSV file.  
You must supply an OpenCage API key (get a free one at [OpenCage Data](https://opencagedata.com/api)).  
API usage is tracked and limited to 2,500 lookups per UTC day.

## How To Use

1. Download your OpenCage API key.
2. Launch `geolocator.py` (Python 3.8+ and dependencies required, see below).
3. Click “API Key” at the bottom and paste in your key.
4. Click “Browse” to select your CSV file of intersections.
5. Click “RUN” to enrich your CSV with latitude and longitude.
6. Help/About is always available at the bottom.

## Requirements

- Python 3.8 or higher
- [pandas](https://pypi.org/project/pandas/)
- [geopy](https://pypi.org/project/geopy/)

Install dependencies with:
```
pip install pandas geopy
```

## Author

[Angry Munky](https://github.com/AngryMunky)

