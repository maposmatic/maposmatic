#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009  Étienne Loks  <etienne.loks_AT_peacefrogsDOTnet>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# See the file COPYING for details.

"""
Extra widgets and fields
"""

from django import forms
from django.utils.safestring import mark_safe

from www import settings

URL_OSM_CSS = ["http://www.openlayers.org/api/theme/default/style.css"]
URL_OSM_JS = ["http://www.openlayers.org/api/OpenLayers.js",
          "http://www.openstreetmap.org/openlayers/OpenStreetMap.js"]

class AreaWidget(forms.TextInput):
    """
    Manage the edition of an area on the map
    """
    class Media:
        css = {"all": URL_OSM_CSS}
        js = URL_OSM_JS + ["/smedia/osm_map.js"]

    def render(self, name, value, attrs=None):
        """
        Render a map
        """
        upper_left_lat, upper_left_lon = 0, 0
        lower_right_lat, lower_right_lon = 0, 0

        if value:
            if len(value) == 2:
                upper_left = value[0]
                lower_right = value[1]
                if hasattr(upper_left, 'x') and hasattr(upper_left, 'y'):
                    upper_left_lon = str(upper_left.x)
                    upper_left_lat = str(upper_left.y)
                elif len(upper_left) == 2:
                    upper_left_lon = upper_left[1]
                    upper_left_lat = upper_left[0]
                if hasattr(lower_right, 'x') and hasattr(lower_right, 'y'):
                    lower_right_lon = str(lower_right.x)
                    lower_right_lat = str(lower_right.y)
                elif len(lower_right) == 2:
                    lower_right_lon = lower_right[1]
                    lower_right_lat = lower_right[0]
        else:
            upper_left_lat, upper_left_lon, \
                lower_right_lat, lower_right_lon = settings.BASE_BOUNDING_BOX

        tpl = u"""<div id="map"></div>
<div id="map_bb">
    <input type="text" name="lat_upper_left" id="lat_upper_left"
           onchange="updateMap();" value="%s" /><br />
    <input type="text" name="lon_upper_left" id="lon_upper_left"
           onchange="updateMap();" value="%s" />
    <input type="text" name="lon_bottom_right" id="lon_bottom_right"
           onchange="updateMap();" value="%s" /><br />
    <input type="text" name="lat_bottom_right" id="lat_bottom_right"
           onchange="updateMap();" value="%s" />
</div>
""" % (upper_left_lat, upper_left_lon, lower_right_lon, lower_right_lat)
        tpl += u"""<script type='text/javascript'><!--
init();
// -->
</script>
"""
        return mark_safe(tpl)

    def value_from_datadict(self, data, files, name):
        """
        Return the appropriate values
        """
        values = []
        for keys in (('lat_upper_left', 'lon_upper_left',),
                     ('lat_bottom_right', 'lon_bottom_right')):
            value = []
            for key in keys:
                val = data.get(key, None)
                if not val:
                    return []
                value.append(val)
            values.append(value)
        return values

class AreaField(forms.MultiValueField):
    '''
    Set the widget for the form field
    '''
    widget = AreaWidget

    def clean(self, value):
        pass

    def compress(self, data_list):
        if not data_list:
            return None
        return data_list

