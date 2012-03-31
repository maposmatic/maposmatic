# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2012  David Decotigny
# Copyright (C) 2012  Frédéric Lehobey
# Copyright (C) 2012  David Mentré
# Copyright (C) 2012  Maxime Petazzoni
# Copyright (C) 2012  Thomas Petazzoni
# Copyright (C) 2012  Gaël Utard

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

import logging
import psycopg2
import www.settings

l = logging.getLogger('maposmatic')
_DB = None

def get():
    global _DB

    if _DB:
        return _DB

    try:
        _DB = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s' port='%s'" %
                                (www.settings.GIS_DATABASE_NAME,
                                 www.settings.GIS_DATABASE_USER,
                                 www.settings.GIS_DATABASE_HOST,
                                 www.settings.GIS_DATABASE_PASSWORD,
                                 www.settings.GIS_DATABASE_PORT))
    except psycopg2.OperationalError, e:
        l.warning("Could not connect to the PostGIS database: %s" %
                  str(e)[:-1])
        _DB = None

    return _DB
