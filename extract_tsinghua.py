#!/usr/bin/env python3
"""Extract Tsinghua University campus data from Beijing OSM PBF file."""

import osmium
import json
import sys

# Tsinghua campus bounding box (slightly expanded to catch everything)
TSINGHUA_BBOX = {
    'min_lat': 39.990,
    'max_lat': 40.020,
    'min_lon': 116.305,
    'max_lon': 116.345,
}

class TsinghuaHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}        # id -> (lat, lon)
        self.buildings = []    # ways with building tag
        self.amenities = []    # POIs
        self.highways = []     # roads/paths
        self.leisures = []     # parks, gardens, sports
        self.waterways = []    # rivers, lakes
        self.landuse = []      # land use areas
        self.relations = []    # multipolygon relations etc.
        self.all_pois = []     # All named features
        self.seen_ids = set()

    def in_bbox(self, lat, lon):
        return (TSINGHUA_BBOX['min_lat'] <= lat <= TSINGHUA_BBOX['max_lat'] and
                TSINGHUA_BBOX['min_lon'] <= lon <= TSINGHUA_BBOX['max_lon'])

    def way_in_bbox(self, nodes_list):
        """Check if any node in the way falls within bbox."""
        for nref in nodes_list:
            if nref in self.nodes:
                lat, lon = self.nodes[nref]
                if self.in_bbox(lat, lon):
                    return True
        return False

    def get_centroid(self, nodes_list):
        """Calculate centroid of a way."""
        lats, lons = [], []
        for nref in nodes_list:
            if nref in self.nodes:
                lat, lon = self.nodes[nref]
                lats.append(lat)
                lons.append(lon)
        if lats:
            return sum(lats) / len(lats), sum(lons) / len(lons)
        return None, None

    def node(self, n):
        if self.in_bbox(n.location.lat, n.location.lon):
            self.nodes[n.id] = (n.location.lat, n.location.lon)

    def way(self, w):
        if not self.way_in_bbox(w.nodes):
            return

        tags = dict(w.tags)
        if not tags:
            return

        centroid = self.get_centroid(w.nodes)
        if centroid[0] is None:
            return

        name = tags.get('name', '')
        name_zh = tags.get('name:zh', tags.get('name:zh-CN', name))

        base_info = {
            'id': w.id,
            'lat': round(centroid[0], 6),
            'lon': round(centroid[1], 6),
            'name': name_zh or name,
            'name_en': tags.get('name:en', ''),
            'tags': tags,
        }

        # Buildings
        if 'building' in tags and tags['building'] != 'no':
            base_info['building_type'] = tags['building']
            self.buildings.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)

        # Amenities and POIs
        if 'amenity' in tags:
            base_info['category'] = 'amenity'
            base_info['type'] = tags['amenity']
            self.amenities.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)

        # Highways (roads, paths)
        if 'highway' in tags:
            base_info['type'] = tags['highway']
            self.highways.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)

        # Leisure (parks, gardens, sports)
        if 'leisure' in tags:
            base_info['category'] = 'leisure'
            base_info['type'] = tags['leisure']
            self.leisures.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)

        # Natural water
        if 'natural' in tags and tags['natural'] in ('water', 'wetland'):
            base_info['category'] = 'water'
            self.waterways.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)

        # Waterway
        if 'waterway' in tags:
            base_info['category'] = 'waterway'
            self.waterways.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)

        # Land use
        if 'landuse' in tags:
            base_info['category'] = 'landuse'
            base_info['type'] = tags['landuse']
            self.landuse.append(base_info)

        # Tourism
        if 'tourism' in tags:
            base_info['category'] = 'tourism'
            base_info['type'] = tags['tourism']
            self.amenities.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)

        # Historic
        if 'historic' in tags:
            base_info['category'] = 'historic'
            base_info['type'] = tags['historic']
            self.amenities.append(base_info)
            if name_zh or name:
                self.all_pois.append(base_info)


def main():
    pbf_path = 'myagents_files/beijing-260710.osm.pbf'

    handler = TsinghuaHandler()
    handler.apply_file(pbf_path, locations=True)

    print(f"Nodes loaded: {len(handler.nodes)}")
    print(f"Buildings found: {len(handler.buildings)}")
    print(f"Amenities/POIs: {len(handler.amenities)}")
    print(f"Named POIs: {len(handler.all_pois)}")
    print(f"Highways/roads: {len(handler.highways)}")
    print(f"Leisure areas: {len(handler.leisures)}")
    print(f"Water features: {len(handler.waterways)}")
    print(f"Land use areas: {len(handler.landuse)}")
    print()

    # Save all data
    output = {
        'bbox': TSINGHUA_BBOX,
        'stats': {
            'nodes': len(handler.nodes),
            'buildings': len(handler.buildings),
            'amenities': len(handler.amenities),
            'named_pois': len(handler.all_pois),
            'highways': len(handler.highways),
            'leisures': len(handler.leisures),
            'waterways': len(handler.waterways),
            'landuse': len(handler.landuse),
        },
        'buildings': handler.buildings,
        'amenities': handler.amenities,
        'highways': handler.highways,
        'leisures': handler.leisures,
        'waterways': handler.waterways,
        'landuse': handler.landuse,
    }

    with open('tsinghua_osm_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Data saved to tsinghua_osm_data.json")

    # Print all named buildings
    print("\n=== NAMED BUILDINGS ===")
    named = [b for b in handler.buildings if b['name']]
    named.sort(key=lambda x: x['name'])
    for b in named:
        print(f"  {b['name']:<20s} ({b['name_en']:<40s}) [{b['lat']}, {b['lon']}]  type={b.get('building_type','?')}")

    # Print all amenities
    print("\n=== AMENITIES / POIs ===")
    for a in handler.amenities:
        cat = a.get('category', a.get('type', '?'))
        print(f"  {a['name']:<25s} [{a['lat']}, {a['lon']}]  {cat}")

    # Print roads
    print("\n=== ROADS ===")
    named_roads = [h for h in handler.highways if h['name']]
    named_roads.sort(key=lambda x: x['name'])
    for r in named_roads:
        print(f"  {r['name']:<25s} type={r.get('type','?')}")

    # Print water/natural features
    print("\n=== WATER & NATURAL ===")
    for w in handler.waterways:
        print(f"  {w['name']:<25s} [{w['lat']}, {w['lon']}]  {w.get('category','?')}")

    # Print leisure
    print("\n=== LEISURE / SPORTS ===")
    for l in handler.leisures:
        print(f"  {l['name']:<25s} [{l['lat']}, {l['lon']}]  type={l.get('type','?')}")


if __name__ == '__main__':
    main()
