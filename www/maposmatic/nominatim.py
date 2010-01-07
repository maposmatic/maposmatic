# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Nominatim parsing + json export
# Note: we query nominatim in XML format because otherwise we cannot
# access the osm_id tag. Then we format it as json back to the
# javascript routines


"""
Simple API to query http://nominatim.openstreetmap.org

Most of the credits should go to gthe Nominatim team.
"""

import www.settings
import psycopg2
from urllib import urlencode
import urllib2
from xml.etree.ElementTree import parse as XMLTree


NOMINATIM_BASE_URL = "http://nominatim.openstreetmap.org/search/"


def query(query_text, with_polygons = False):
    """
    Query the nominatim service for the given city query and return a
    (python) list of entries for the given squery (eg. "Paris"). Each
    entry is a dictionary key -> value (value is always a
    string). When possible, we also try to uncover the OSM database
    IDs associated with the entries; in that case, an
    "ocitysmap_params" key is provided, which maps to a dictionary
    containing:
      - key "table": when "line" -> refers to table "planet_osm_line";
        when "polygon" -> "planet_osm_polygon"
      - key "id": ID of the OSM database entry
      - key "admin_level": The value stored in the OSM table for admin_level
    """
    entries = _fetch_entries(query_text, with_polygons)
    return _canonicalize_data(_retrieve_missing_data_from_GIS(entries))


def _fetch_entries(query_text, with_polygons):
    """
    Query the nominatim service for the given city query and return a
    (python) list of entries for the given squery (eg. "Paris"). Each
    entry is a dictionary key -> value (value is always a
    string).
    """
    # For some reason, the "xml" nominatim output is ALWAYS used, even
    # though we will later (in views.py) transform this into
    # json. This is because we know that this xml output is correct
    # and complete (at least the "osm_id" field is missing from the
    # json output)
    query_tags = dict(q=query_text.encode("UTF-8"),
                      format='xml', addressdetails=1)
    if with_polygons:
        query_tags['polygon']=1

    qdata = urlencode(query_tags)
    f = urllib2.urlopen(url="%s?%s" % (NOMINATIM_BASE_URL, qdata))

    result = []
    for place in XMLTree(f).getroot().getchildren():
        attribs = dict(place.attrib)
        for elt in place.getchildren():
            attribs[elt.tag] = elt.text
        result.append(attribs)

    return result


def _canonicalize_data(data):
    """
    Take a structure containing strings (dict, list, scalars, ...)
    and convert it into the same structure with the proper conversions
    to float or integers, etc.
    """
    if type(data) is tuple:
        return tuple(_canonicalize_data(x) for x in data)
    elif type(data) is list:
        return [_canonicalize_data(x) for x in data]
    elif type(data) is dict:
        return dict([(_canonicalize_data(k),
                      _canonicalize_data(v)) for k,v in data.iteritems()])
    try:
        return int(data)
    except ValueError:
        try:
            return float(data)
        except ValueError:
            pass
    return data


def _retrieve_missing_data_from_GIS(entries):
    """
    Try to retrieve additional OSM information for the given nominatim
    entries. Among the information, we try to determine the real ID in
    an OSM table for each of these entries. All these additional data
    are stored in the "ocitysmap_params" key of the entry, which maps
    to a dictionary containing:
      - key "table": when "line" -> refers to table "planet_osm_line";
        when "polygon" -> "planet_osm_polygon"
      - key "id": ID of the OSM database entry
      - key "admin_level": The value stored in the OSM table for admin_level
    """
    if not www.settings.has_gis_database():
        return entries

    try:
        conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %
                                (www.settings.GIS_DATABASE_NAME,
                                 www.settings.DATABASE_USER,
                                 www.settings.DATABASE_HOST,
                                 www.settings.DATABASE_PASSWORD))
    except psycopg2.OperationalError, e:
        www.settings.LOG.warning("Could not connect to the PostGIS database: %s" %
                                 str(e)[:-1])
        return entries

    # Nominatim returns a field "osm_id" for each result
    # entry. Depending on the type of the entry, it can point to
    # various database entries. For admin boundaries, osm_id is
    # supposed to point to either the 'polygon' or the 'line'
    # table. Usually, the database entry ID in the table is derived by
    # the "relation" items by osm2pgsql, which assigns to that ID the
    # opposite of osm_id... But we still consider that it could be the
    # real osm_id (not its opposite). Let's have fun...

    # Will sort the entries so that the admin boundaries appear first,
    # then cities, towns, etc. Second order: larger cities
    # (ie. greater way_area) are listed first
    unsorted_entries = []
    admin_boundary_names = set()
    PLACE_RANKS = { 'city': 20, 'town': 30, 'municipality': 40,
                    'village': 50, 'hamlet': 60, 'suburb': 70,
                    'island': 80, 'islet': 90, 'locality': 100 }
    ADMIN_LEVEL_RANKS = { '8': 0, '7': 1, '6': 2, '5':3 } # level 8 is best !
    try:
        cursor = conn.cursor()
        for entry in entries:
            # Should we try to lookup the id in the OSM DB ?
            lookup_OSM = False

            # Highest rank = last in the output
            entry_rank = (1000,0) # tuple (sort rank, -area)

            # Try to determine the order in which this entry should appear
            if entry.get("class") == "boundary":
                if entry.get("type") == "administrative":
                    entry_rank = (10,0)
                    admin_boundary_names.add(entry.get("display_name", 42))
                    lookup_OSM = True
                else:
                    # Just don't try to lookup any additional
                    # information from OSM when the nominatim entry is
                    # not an administrative boundary
                    continue
            elif entry.get("class") == "place":
                try:
                    entry_rank = (PLACE_RANKS[entry.get("type")],0)
                except KeyError:
                    # Will ignore all the other place tags
                    continue
            else:
                # We ignore all the other classes
                continue

            # Try to lookup in the OSM DB, when needed and when it
            # makes sense (ie. the data is coming from a relation)
            if lookup_OSM and (entry.get('osm_type') == "relation"):
                for table_name in ("polygon", "line"):
                    # Lookup the polygon/line table for both osm_id and
                    # the opposite of osm_id
                    cursor.execute("""select osm_id, admin_level, way_area
                                      from planet_osm_%s
                                      where osm_id = -%s""" \
                                       % (table_name,entry["osm_id"]))
                    result = tuple(set(cursor.fetchall()))
                    if len(result) == 1:
                        osm_id, admin_level, way_area = result[0]
                        entry["ocitysmap_params"] \
                            = dict(table=table_name, id=osm_id,
                                   admin_level=admin_level,
                                   way_area=way_area)
                        # Make these first in list, priviledging level 8
                        entry_rank = (ADMIN_LEVEL_RANKS.get(admin_level,9),
                                      -way_area)
                        break

            # Register this entry for the results
            unsorted_entries.append((entry_rank, entry))

        # Some cleanup
        cursor.close()
    finally:
        conn.close()

    # Sort the entries according to their rank
    sorted_entries = [entry for rank,entry in sorted(unsorted_entries,
                                                     key=lambda kv: kv[0])]

    # Remove those non-admin-boundaries having the same name as an
    # admin boundary
    retval = []
    for e in sorted_entries:
        if e.get("class") != "boundary" or e.get("type") != "administrative":
            if e.get("display_name") in admin_boundary_names:
                continue
        retval.append(e)

    return retval



if __name__ == "__main__":
    import pprint, sys
    pp = pprint.PrettyPrinter(indent=4)

    for city in sys.argv[1:]:
        print "###### %s:" % city
        pp.pprint(query(city))
