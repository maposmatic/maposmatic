/* coding: utf-8
 *
 * maposmatic, the web front-end of the MapOSMatic city map generation system
 * Copyright (C) 2009 David Decotigny
 * Copyright (C) 2009 Frédéric Lehobey
 * Copyright (C) 2009 David Mentré
 * Copyright (C) 2009 Maxime Petazzoni
 * Copyright (C) 2009 Thomas Petazzoni
 * Copyright (C) 2009 Gaël Utard
 * Copyright (C) 2009 Étienne Loks
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * See the file COPYING for details.
 */

/* OSM slippy map management. */

/* Maximum length of the bounding box to be rendered. This length is
 * checked in both directions (longitude and latitude).
 * Note: if you change this you should probably change
 * BBOX_MAXIMUM_LENGTH_IN_METERS in settings_local.py too.
 *
 * Note: this should be a const, but apparently IE still chokes on the const
 * keyword.
 * */
var BBOX_MAXIMUM_LENGTH_IN_KM = 20;

var map = null;
var update_lock = 0;
var epsg_display_projection = new OpenLayers.Projection('EPSG:4326');
var epsg_projection = new OpenLayers.Projection('EPSG:900913');
var bbox_style = {fill: true, fillColor: "#FFFFFF", fillOpacity: 0.5,
    stroke: true, strokeOpacity: 0.8, strokeColor: "#FF0000", strokeWidth: 2};

function getUpperLeftLat() { return document.getElementById('lat_upper_left'); }
function getUpperLeftLon() { return document.getElementById('lon_upper_left'); }
function getBottomRightLat() { return document.getElementById('lat_bottom_right'); }
function getBottomRightLon() { return document.getElementById('lon_bottom_right'); }
function getAreaUpperLeftLat() { return document.getElementById('area_lat_upper_left'); }
function getAreaUpperLeftLon() { return document.getElementById('area_lon_upper_left'); }
function getAreaBottomRightLat() { return document.getElementById('area_lat_bottom_right'); }
function getAreaBottomRightLon() { return document.getElementById('area_lon_bottom_right'); }

/* Update form fields on bbox drawing. */
function updateFormBbox(bounds, areaSelectionNotifier)
{
    bounds = bounds.transform(epsg_projection, epsg_display_projection);

    getUpperLeftLat().value = bounds.top.toFixed(4);
    getUpperLeftLon().value = bounds.left.toFixed(4);
    getBottomRightLat().value = bounds.bottom.toFixed(4);
    getBottomRightLon().value = bounds.right.toFixed(4);

    upper_left   = new OpenLayers.LonLat(bounds.left, bounds.top);
    upper_right  = new OpenLayers.LonLat(bounds.right, bounds.top);
    bottom_right = new OpenLayers.LonLat(bounds.right, bounds.bottom);

    bbox_width  = OpenLayers.Util.distVincenty(upper_left, upper_right)
    bbox_height = OpenLayers.Util.distVincenty(upper_right, bottom_right)

    if (bbox_width > BBOX_MAXIMUM_LENGTH_IN_KM ||
        bbox_height > BBOX_MAXIMUM_LENGTH_IN_KM)
	areaSelectionNotifier(false, bounds);
    else
	areaSelectionNotifier(true, bounds);
}

/* Update the map on form field modification. */
function updateMap(vectorLayer)
{
    if (getUpperLeftLon().value!="" && getUpperLeftLat().value!="" &&
        getBottomRightLon().value!="" && getBottomRightLat().value!="")
    {
        var bbox_bounds = new OpenLayers.Bounds(
            getUpperLeftLon().value, getUpperLeftLat().value,
            getBottomRightLon().value, getBottomRightLat().value);
        bbox_bounds.transform(epsg_display_projection, epsg_projection);
        var feature = new OpenLayers.Feature.Vector(
            bbox_bounds.toGeometry(), {}, bbox_style);
        vectorLayer.addFeatures(feature);
        closest = true
    }
    else
    {
        closest = false
    }

    var bounds = new OpenLayers.Bounds(getAreaUpperLeftLon().value,
                                       getAreaUpperLeftLat().value,
                                       getAreaBottomRightLon().value,
                                       getAreaBottomRightLat().value);
    bounds.transform(epsg_display_projection, epsg_projection);

    update_lock = 1;
    map.zoomToExtent(bounds, closest);
    update_lock = 0;
}

/** Map Zoom/Move events callback: update form fields on zoom action. */
function updateFormArea()
{
    if (update_lock)
      return;

    var bounds = map.getExtent();
    bounds = bounds.transform(epsg_projection, epsg_display_projection);
    getAreaUpperLeftLat().value = bounds.top.toFixed(4);
    getAreaUpperLeftLon().value = bounds.left.toFixed(4);
    getAreaBottomRightLat().value = bounds.bottom.toFixed(4);
    getAreaBottomRightLon().value = bounds.right.toFixed(4);
}

/* Main initialisation function. Must be called before the map is
   manipulated. areaSelectionNotifier is a function that gets called
   when an area is selected. */
function mapInit(areaSelectionNotifier)
{
    map = new OpenLayers.Map ('map', {
        controls:[new OpenLayers.Control.Navigation(),
                  new OpenLayers.Control.PanZoomBar(),
                  new OpenLayers.Control.Attribution()],
        maxExtent: new OpenLayers.Bounds(-20037508.34,-20037508.34,20037508.34,20037508.34),
        numZoomLevels: 18,
        maxResolution: 156543.0399,
        projection: epsg_projection,
        displayProjection: epsg_display_projection
    } );

    layerTilesMapnik = new OpenLayers.Layer.OSM.Mapnik("Mapnik");
    map.addLayer(layerTilesMapnik);

    var vectorLayer = new OpenLayers.Layer.Vector("Overlay");
    map.addLayer(vectorLayer);

    var selectControl = new OpenLayers.Control();
    OpenLayers.Util.extend(selectControl, {
        draw: function() {
            this.box = new OpenLayers.Handler.Box(selectControl,
                {'done': this.notice},
                {keyMask: navigator.platform.match(/Mac/) ?
                     OpenLayers.Handler.MOD_ALT :OpenLayers.Handler.MOD_CTRL});
            this.box.activate();
        },

        notice: function(pxbounds) {
            ltpixel = map.getLonLatFromPixel(
                new OpenLayers.Pixel(pxbounds.left, pxbounds.top));
            rbpixel = map.getLonLatFromPixel(
                new OpenLayers.Pixel(pxbounds.right, pxbounds.bottom));
            if (ltpixel.equals(rbpixel))
                return;
            bounds = new OpenLayers.Bounds();
            bounds.extend(ltpixel);
            bounds.extend(rbpixel);
            var feature = new OpenLayers.Feature.Vector(
                bounds.toGeometry(), {}, bbox_style);
            vectorLayer.destroyFeatures()
            vectorLayer.addFeatures(feature);
            updateFormBbox(bounds, areaSelectionNotifier);
        }
    });
    map.addControl(selectControl);

    map.events.register('zoomend', map, updateFormArea);
    map.events.register('moveend', map, updateFormArea);
    updateMap(vectorLayer);
}
