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
from django.utils.translation import ugettext_lazy as _

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
        Render the bbox selection widget.
        """
        # Initially the widget shows no bounding box and shows an area that
        # contains the France
        if value:
            upper_left_lat, upper_left_lon, \
                lower_right_lat, lower_right_lon = value[0]
            area_upper_left_lat, area_upper_left_lon, \
                area_lower_right_lat, area_lower_right_lon = value[1]
        else:
            upper_left_lat, upper_left_lon, \
                lower_right_lat, lower_right_lon = '', '', '', ''
            area_upper_left_lat, area_upper_left_lon, \
                area_lower_right_lat, area_lower_right_lon = settings.BASE_BOUNDING_BOX

        tpl = u"""<div id="map"></div>
        <div id="map_bb">
            <input type="text" name="lat_upper_left" id="lat_upper_left"
                   onchange="updateMap();" value="%(tl_lat)s"
                   title="%(tl_lat_help)s" />,
            <input type="text" name="lon_upper_left" id="lon_upper_left"
                   onchange="updateMap();" value="%(tl_lon)s"
                   title="%(tl_lon_help)s" />
            &rarr;
            <input type="text" name="lat_bottom_right" id="lat_bottom_right"
                   onchange="updateMap();" value="%(br_lat)s"
                   title="%(br_lat_help)s" />,
            <input type="text" name="lon_bottom_right" id="lon_bottom_right"
                   onchange="updateMap();" value="%(br_lon)s"
                   title="%(br_lon_help)s" />
            <input type="hidden" name="area_lat_upper_left"
                   id="area_lat_upper_left" value="%(area_tl_lat)s">
            <input type="hidden" name="area_lon_upper_left"
                   id="area_lon_upper_left" value="%(area_tl_lon)s">
            <input type="hidden" name="area_lat_bottom_right"
                   id="area_lat_bottom_right" value="%(area_br_lat)s">
            <input type="hidden" name="area_lon_bottom_right"
                   id="area_lon_bottom_right" value="%(area_br_lon)s">
        </div>""" % {'tl_lat': upper_left_lat, 'tl_lon': upper_left_lon,
                     'br_lat': lower_right_lat, 'br_lon': lower_right_lon,
                     'area_tl_lat': area_upper_left_lat,
                     'area_tl_lon': area_upper_left_lon,
                     'area_br_lat': area_lower_right_lat,
                     'area_br_lon': area_lower_right_lon,
                     'tl_lat_help': _("Latitude of the top left corner"),
                     'tl_lon_help': _("Longitude of the top left corner"),
                     'br_lat_help': _("Latitude of the bottom right corner"),
                     'br_lon_help': _("Longitude of the bottom right corner")}

        return mark_safe(tpl)

    def value_from_datadict(self, data, files, name):
        """
        Return the appropriate values
        """
        return ((data['lat_upper_left'], data['lon_upper_left'],
                 data['lat_bottom_right'], data['lon_bottom_right']),
                (data['area_lat_upper_left'], data['area_lon_upper_left'],
                 data['area_lat_bottom_right'], data['area_lon_bottom_right']))

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

