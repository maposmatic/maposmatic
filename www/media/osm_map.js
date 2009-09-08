/* Copyright (C) 2009  Étienne Loks  <etienne.loks_AT_peacefrogsDOTnet>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

See the file COPYING for details.
*/

var map;
var update_lock = 0;
var epsg_display_projection = new OpenLayers.Projection('EPSG:4326');
var epsg_projection = new OpenLayers.Projection('EPSG:900913');


/* update form fields on zoom action */
function updateForm(){
    if (update_lock) return;
    var bounds = map.getExtent();
    var topleft = new OpenLayers.LonLat(bounds.left, bounds.top);
    topleft = topleft.transform(epsg_projection, epsg_display_projection);
    var bottomright = new OpenLayers.LonLat(bounds.right, bounds.bottom);
    bottomright = bottomright.transform(epsg_projection, epsg_display_projection);
    document.getElementById('lat_upper_left').value = topleft.lat;
    document.getElementById('lon_upper_left').value = topleft.lon;
    document.getElementById('lat_bottom_right').value = bottomright.lat;
    document.getElementById('lon_bottom_right').value = bottomright.lon;
}

/* update map on form field modification */
function updateMap(){
    var bounds = new OpenLayers.Bounds();
    var topleft = new OpenLayers.LonLat(document.getElementById('lon_upper_left').value,
                                        document.getElementById('lat_upper_left').value);
    topleft = topleft.transform(epsg_display_projection, epsg_projection);
    var bottomright = new OpenLayers.LonLat(document.getElementById('lon_bottom_right').value,
                                            document.getElementById('lat_bottom_right').value);
    bottomright = bottomright.transform(epsg_display_projection, epsg_projection);
    bounds.extend(topleft);
    bounds.extend(bottomright);
    update_lock = 1;
    map.zoomToExtent(bounds);
    // force the zoom is necessary when initializing the page (OL bug ?)
    map.zoomTo(map.getZoomForExtent(bounds));
    update_lock = 0;
}

/* main initialisation function */
function init(){
    map = new OpenLayers.Map ('map', {
        controls:[new OpenLayers.Control.Navigation(),
                    new OpenLayers.Control.PanZoomBar(),
                    new OpenLayers.Control.Attribution()],
        maxExtent: new OpenLayers.Bounds(-20037508,-20037508,20037508,20037508),
        numZoomLevels: 18,
        maxResolution: 156543,
        units: 'm',
        projection: epsg_projection,
        displayProjection: epsg_display_projection
    } );
    layerTilesMapnik = new OpenLayers.Layer.OSM.Mapnik("Mapnik");
    map.addLayer(layerTilesMapnik);
    map.events.register('zoomend', map, updateForm);
    map.events.register('moveend', map, updateForm);
}


