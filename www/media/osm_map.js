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

var map = null;
var update_lock = 0;
var epsg_display_projection = new OpenLayers.Projection('EPSG:4326');
var epsg_projection = new OpenLayers.Projection('EPSG:900913');

function getUpperLeftLat() { return document.getElementById('lat_upper_left'); }
function getUpperLeftLon() { return document.getElementById('lon_upper_left'); }
function getBottomRightLat() { return document.getElementById('lat_bottom_right'); }
function getBottomRightLon() { return document.getElementById('lon_bottom_right'); }

/** Map Zoom/Move events callback: update form fields on zoom action. */
function updateForm()
{
    if (update_lock)
      return;

    var bounds = map.getExtent();

    var topleft = new OpenLayers.LonLat(bounds.left, bounds.top);
    topleft = topleft.transform(epsg_projection, epsg_display_projection);

    var bottomright = new OpenLayers.LonLat(bounds.right, bounds.bottom);
    bottomright = bottomright.transform(epsg_projection, epsg_display_projection);

    getUpperLeftLat().value = topleft.lat.toFixed(4);
    getUpperLeftLon().value = topleft.lon.toFixed(4);
    getBottomRightLat().value = bottomright.lat.toFixed(4);
    getBottomRightLon().value = bottomright.lon.toFixed(4);
}

/* Update the map on form field modification. */
function updateMap()
{
    var bounds = new OpenLayers.Bounds(getUpperLeftLon().value,
                                       getUpperLeftLat().value,
                                       getBottomRightLon().value,
                                       getBottomRightLat().value);
    bounds.transform(epsg_display_projection, epsg_projection);

    update_lock = 1;
    map.zoomToExtent(bounds);
    update_lock = 0;
}

/* Main initialisation function. Must be called before the map is manipulated. */
function mapInit()
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

    map.events.register('zoomend', map, updateForm);
    map.events.register('moveend', map, updateForm);
    updateMap();
}

function switchToAdminMode() {
  $('#mapform tbody').children('tr.bybbox').hide();
  $('#mapform tbody').children('tr.byadmin').show();
  $('#map_language_label').hide();
  $('#map_language_entry').hide();
}

function switchToBBoxMode() {
  $('#mapform tbody').children('tr.byadmin').hide();
  $('#mapform tbody').children('tr.bybbox').show();
  $('#map_language_label').show();
  $('#map_language_entry').show();
  if (map == null)
    mapInit();
}

$(document).ready(function() {
  $('#id_mode_0').bind('click', function(e) { switchToAdminMode(); });
  $('#id_mode_1').bind('click', function(e) { switchToBBoxMode(); });

  if ($('#id_mode_1').is(':checked'))
    switchToBBoxMode();
  else
    switchToAdminMode();

  suggest('#id_administrative_city', '#suggest',
          '#id_administrative_osmid', '#id_go_next_btn',
          { selectedClass: 'selected',
            timeout: 150
          });
});

function suggest(input, results, osm_id, button, options) {
  var $input = $(input).attr('autocomplete', 'off');
  var $results = $(results);
  var $osm_id = $(osm_id);
  var $button = $(button);
  var timeout = false;

  // Setup the keyup event.
  $input.keyup(processKey);

  // Disable form validation via the Enter key
  $input.keypress(function(e) { if (e.keyCode == 13) return false; });

  function appendValidResult(id, name) {
    $results.append('<li class="suggestok" id="rad' + id + '">'
       + name + '</span></li>');
    return $('#rad' + id);
  }

  function handleNominatimResults(data, textResult) {
    closeSuggest();

    if (data.length)
      $results.show();

    $.each(data, function(i, item) {
      if (typeof item.ocitysmap_params != 'undefined' &&
          item.ocitysmap_params['admin_level'] == 8) {
        var e = appendValidResult(item.ocitysmap_params['id'], item.display_name);

        e.bind('click', function(e) { setResult($(this)); });
        e.bind('onmouseover', function(e) { setSelectedResultTo($(this)); });
      } else {
        $results.append('<li class="suggestoff">'
          + item.display_name + '</li>');
      }
    });
  }

  function processKey(e) {
    clearResult();

    switch (e.keyCode) {
      case 27:  // ESC
        closeSuggest();
        break;
      case 9:   // TAB
      case 13:  // OK
        selectCurrentResult();
        return false;
        break;
      case 38:  // UP
        prevResult();
        break;
      case 40:  // DOWN
        nextResult();
        break;
      default:
        if (timeout) {
          clearTimeout(timeout);
        }
        timeout = setTimeout(function() {
          $.getJSON("/nominatim/", {q: $input.val()},
            handleNominatimResults);
          }, options.timeout);
      }
  }

  function clearResult() {
    $osm_id.val('');
    $button.attr('disabled', 'disabled');
    $button.hide();
  }

  /* Returns the currently selected result. */
  function getCurrentResult() {
    var children = $results.children('li.' + options.selectedClass);
    if (children.length)
      return children;
    return false;
  }

  /* Set the form to the currently selected result. */
  function selectCurrentResult() {
    var elt = getCurrentResult();
    if (elt)
      setResult(elt);
  }

  /* Set the form to the given result. */
  function setResult(elt) {
    $osm_id.val(elt.attr('id').substring(3));
    $input.val(elt.html());
    closeSuggest();
    $button.removeAttr('disabled');
    $button.show();
  }

  function setSelectedResultTo(elt) {
    $results.children('li').removeClass(options.selectedClass);
    if (elt)
      elt.addClass(options.selectedClass);
  }

  function prevResult() {
    var current = getCurrentResult();
    var new_result;

    if (current) {
      var prev_valid = current.siblings('li.suggestok');
      if (prev_valid.length)
        new_result = prev_valid;
    } else {
      new_result = $results.children('li.suggestok:last');
    }

    setSelectedResultTo(new_result);
  }

  function nextResult() {
    var current = getCurrentResult();
    var new_result;

    if (current) {
      var next_valid = current.siblings('li.suggestok');
      if (next_valid.length)
        new_result = next_valid;
    } else {
      new_result = $results.children('li.suggestok:first');
    }

    setSelectedResultTo(new_result);
  }

  /* Empty and close the suggestion box. */
  function closeSuggest() {
    $results.empty();
    $results.hide();
  }
}

