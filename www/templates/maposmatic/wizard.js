{% comment %}
 coding: utf-8

 maposmatic, the web front-end of the MapOSMatic city map generation system
 Copyright (C) 2012  David Decotigny
 Copyright (C) 2012  Frédéric Lehobey
 Copyright (C) 2012  Pierre Mauduit
 Copyright (C) 2012  David Mentré
 Copyright (C) 2012  Maxime Petazzoni
 Copyright (C) 2012  Thomas Petazzoni
 Copyright (C) 2012  Gaël Utard

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
{% endcomment %}
{% load i18n %}
{% load extratags %}

/**
 * Map creation wizard.
 */

var BBOX_MAXIMUM_LENGTH_IN_KM = {{ BBOX_MAXIMUM_LENGTH_IN_METERS }} / 1000;

var map = null;
var country = null;
var languages = $('#id_map_language').html();

jQuery.fn.reverse = [].reverse;

$('#wizard').carousel({'interval': false});

/**
 * When the carousel initiates its slide, trigger the 'prepare' event on the
 * slide that is about to be activated.
 */
$('#wizard').bind('slide', function(e) {
  $(e.relatedTarget).trigger('prepare');
});

/**
 * The 'slid' event is triggered when the carousel finishes a slide in either
 * direction. This function is called by the 'slid' event handler to make sure
 * the prev/next links are in the * correct state based on the position in the
 * carousel.
 */
$('#wizard').bind('slid', setPrevNextLinks);

$('#wizard-step-location label').click(function(e) {
  $('#id_administrative_city').val('');
  $('#id_administrative_osmid').val('');
  country = null;
  $(this).tab('show');
  setPrevNextLinks();

  // If we're switching to the administrative boundary / city search tab, reset
  // the focus inside the input field.
  if ($(this).attr('for') == 'id_mode_0') {
    $('#id_administrative_city').focus();
  }

  // If it's the first time we switch to the bounding box tab, initialize the
  // minimap.
  if ($(this).attr('for') == 'id_mode_1' && !map) {
    map = wizardmap($('#step-location-map'));
  }
});

/**
 * Bind the keyup event on the map title field to control the disabled state of
 * the final submit button. The button can only be pressed if a map title is
 * present. The rest of the validation is assumed to have been taken care of at
 * each step boundary.
 */
$('#id_maptitle').bind('keyup', function(e) {
  if ($(this).val()) {
    $('#id_go_next_btn').removeAttr('disabled');
  } else {
    $('#id_go_next_btn').attr('disabled', 'disabled');
  }
});

function setPrevNextLinks() {
  var current = $('#wizard .carousel-inner div.item.active');
  var first   = $('#wizard .carousel-inner div.item:first-child');
  var last    = $('#wizard .carousel-inner div.item:last-child');

  $('#prevlink').hide();
  $('#nextlink').hide();
  if (current.attr('id') == first.attr('id')) {
    if ($('#id_administrative_osmid').val()) {
      $('#nextlink').show();
    }
  } else if (current.attr('id') == last.attr('id')) {
    $('#prevlink').show();
  } else {
    $('#prevlink').show();
    $('#nextlink').show();
  }
}

$('#wizard-step-paper-size').bind('prepare', function(e) {
  $('#paper-selection').hide();
  $('#paper-size-loading-error').hide();
  $('#paper-size-loading').show();
  $('#nextlink').hide();

  var args = null;
  if ($('#id_administrative_osmid').val()) {
    args = {
      osmid: $('#id_administrative_osmid').val(),
    };
  } else {
    args = {
      lat_upper_left: $('#id_lat_upper_left').val(),
      lon_upper_left: $('#id_lon_upper_left').val(),
      lat_bottom_right: $('#id_lat_bottom_right').val(),
      lon_bottom_right: $('#id_lon_bottom_right').val()
    };
  }

  args['layout'] = $('input[name=layout]:checked').val();
  args['stylesheet'] = $('input[name=stylesheet]:checked').val();

  $.ajax('/apis/papersize/', { type: 'post', data: args })
    .complete(function() { $('#paper-size-loading').hide(); })
    .error(function() { $('#paper-size-loading-error').show(); })
    .success(function(data) {

      function get_paper_def(paper) {
        for (i in data) {
          if (paper == data[i][0]) {
            return data[i];
          }
        }

        return null;
      }

      function handle_paper_size_click(w, h, p_ok, l_ok) {
        var l = $('#paper-selection input[value=landscape]');
        var p = $('#paper-selection input[value=portrait]');

        if (l_ok) {
          l.removeAttr('disabled');
          if (!p_ok) { l.attr('checked', 'checked'); }
        } else {
          l.attr('disabled', 'disabled');
        }

        if (p_ok) {
          p.removeAttr('disabled');
          if (!l_ok) { p.attr('checked', 'checked'); }
        } else {
          p.attr('disabled', 'disabled');
        }

        $('#id_paper_width_mm').val(w);
        $('#id_paper_height_mm').val(h);
      }

      var default_paper = null;

      $.each($('#paper-size ul li'), function(i, item) {
        $(item).hide();

        var paper = $('label input[value]', item).val();
        var def = get_paper_def(paper);
        if (def) {
          $('label', item).bind('click', function() {
            handle_paper_size_click(def[1], def[2], def[3], def[4]);
          });

          if (def[5]) {
            default_paper = $(item);
          }

          $(item).show();

          // TODO: fix for i18n
          if (paper == 'Best fit') {
            w = def[1] / 10;
            h = def[2] / 10;
            $('label em.papersize', item).html('(' + w.toFixed(1) + ' &times; ' + h.toFixed(1) + ' cm²)');
          }
        }
      });

      $('label input', default_paper).click();
      $('#paper-selection').show();
      $('#nextlink').show();
    });
});

$('#wizard-step-lang-title').bind('prepare', function(e) {
  // Prepare the language list
  var list = $('#id_map_language');
  list.html(languages);

  /*
   * The goal is to build a list of languages in which we have first
   * the languages matching the current country code, then an empty
   * disabled entry used as a separator and finally all other
   * languages. To do so, we use prependTo(), which adds elements at
   * the beginning of the list. So we start by prepending the
   * separator, then the "no localization" special language, and
   * finally the languages matching the current country code.
   */
  $('<option disabled="disabled"></option>').prependTo(list);
  $('option[value=C]', list).prependTo(list);
  list.children('option').reverse().each(function() {
    if ($(this).val().match('.._' + country.toUpperCase() + '\..*') != null) {
      $(this).prependTo(list);
    }
  });
  $('option:first', list).attr('selected', 'selected');

  // Seed the summary fields
  if ($('#id_administrative_osmid').val()) {
    $('#summary-location').text($('#id_administrative_city').val());
  } else {
    $('#summary-location').html(
      '(' + $('#id_lat_upper_left').val() + ', ' +
            $('#id_lon_upper_left').val() + ')' +
      '&nbsp;&rarr;&nbsp;' +
      '(' + $('#id_lat_bottom_right').val() + ', ' +
            $('#id_lon_bottom_right').val() + ')');
  }

  $('#summary-layout').text($('input[name=layout]:checked').parent().text().trim());
  $('#summary-stylesheet').text($('input[name=stylesheet]:checked').parent().text().trim());
  $('#summary-paper-size').text(
      ($('input[value=landscape]').attr('checked') == 'checked'
          ? '{% trans "Landscape" %}'
          : '{% trans "Portrait" %}'
      ) + ', ' + $('input[name=papersize]:checked').parent().text().trim());
});

function wizardmap(elt) {
  var map = create_map($('#step-location-map'));
  var lock = false;
  var bbox = null;
  var bbox_style = {
    fill: true,
    fillColor: "#FFFFFF",
    fillOpacity: 0.5,
    stroke: true,
    strokeOpacity: 0.8,
    strokeColor: "#FF0000",
    strokeWidth: 2
  };
  var countryquery = null;

  /**
   * Update the 4 text fields with the area coordinates.
   *
   * If a feature has been drawned (bbox != null), the bounding box of the
   * feature is used, otherwise the map extent is used.
   */
  var update_fields = function() {
    if (lock) {
      return;
    }

    var bounds = new OpenLayers.Bounds((bbox || map.getExtent()).toArray());
    bounds.transform(epsg_projection, epsg_display_projection);

    $('#id_lat_upper_left').val(bounds.top.toFixed(4));
    $('#id_lon_upper_left').val(bounds.left.toFixed(4));
    $('#id_lat_bottom_right').val(bounds.bottom.toFixed(4));
    $('#id_lon_bottom_right').val(bounds.right.toFixed(4));

    var center = bounds.getCenterLonLat();
    var upper_left = new OpenLayers.LonLat(bounds.left, bounds.top);
    var upper_right = new OpenLayers.LonLat(bounds.right, bounds.top);
    var bottom_right = new OpenLayers.LonLat(bounds.right, bounds.bottom);
    var width = OpenLayers.Util.distVincenty(upper_left, upper_right);
    var height = OpenLayers.Util.distVincenty(upper_right, bottom_right);

    if (width < BBOX_MAXIMUM_LENGTH_IN_KM &&
        height < BBOX_MAXIMUM_LENGTH_IN_KM) {
      $('#area-size-alert').hide();
      $('#nextlink').show();

      // Attempt to get the country by reverse geo lookup
      if (countryquery != null) { countryquery.abort(); }
      countryquery = $.getJSON(
        '/apis/reversegeo/' + center.lat + '/' + center.lon + '/',
        function(data) {
          $.each(data, function(i, item) {
            if (typeof item.country_code != 'undefined') {
              country = item.country_code;
            }
          });
        });
    } else {
      $('#area-size-alert').show();
      $('#nextlink').hide();
    }
  };

  /**
   * Set the map bounds and extent to the current values given by the 4 text
   * fields.
   */
  var set_map_bounds_from_fields = function() {
    lock = true;
    set_map_bounds(map, [
      [$('#id_lat_upper_left').val(), $('#id_lon_upper_left').val()],
      [$('#id_lat_bottom_right').val(), $('#id_lon_bottom_right').val()]
    ]);
    lock = false;
  };

  var vectorLayer = new OpenLayers.Layer.Vector("Overlay");
  map.addLayer(vectorLayer);

  var selectControl = new OpenLayers.Control();
  OpenLayers.Util.extend(selectControl, {
    draw: function() {
      this.box = new OpenLayers.Handler.Box(selectControl, {
        'done': this.notice
      }, {
        keyMask: navigator.platform.match(/Mac/)
          ? OpenLayers.Handler.MOD_ALT
          : OpenLayers.Handler.MOD_CTRL
      });
      this.box.activate();
    },

    notice: function(pxbounds) {
      vectorLayer.destroyFeatures();
      bbox = null;

      var ltpixel = map.getLonLatFromPixel(
        new OpenLayers.Pixel(pxbounds.left, pxbounds.top));
      var rbpixel = map.getLonLatFromPixel(
        new OpenLayers.Pixel(pxbounds.right, pxbounds.bottom));
      if (!ltpixel.equals(rbpixel)) {
        bbox = new OpenLayers.Bounds();
        bbox.extend(ltpixel);
        bbox.extend(rbpixel);

        vectorLayer.addFeatures(new OpenLayers.Feature.Vector(
            bbox.toGeometry(), {}, bbox_style));

        update_fields();
        set_map_bounds_from_fields();
      }
    }
  });

  var clearControl = new OpenLayers.Control.Button({
    displayClass: 'clear-features olControlButton',
    title: '{% trans "Clear selected area" %}',
    trigger: function() {
      vectorLayer.destroyFeatures();
      bbox = null;
      update_fields();
      set_map_bounds_from_fields();
      update_fields();
    },
  });

  var clearPanel = new OpenLayers.Control.Panel({
    defaultControl: clearControl,
    createControlMarkup: function(control) {
      var i = document.createElement('i');
      $(i).addClass('icon-retweet');
      $(i).attr('title', control.title);
      return i;
    },
  });
  clearPanel.addControls([clearControl]);

  map.addControl(new OpenLayers.Control.Navigation());
  map.addControl(new OpenLayers.Control.PanZoom());
  map.addControl(new OpenLayers.Control.PinchZoom());
  map.addControl(selectControl);
  map.addControl(clearPanel);

  /* Bind events. */
  map.events.register('zoomend', map, update_fields);
  map.events.register('moveend', map, update_fields);
  $('#step-location-bbox input').bind('keydown', function(e) {
    if (bbox) {
      return;
    }

    if (e.keyCode == 38 || e.keyCode == 40) {
      var v = parseFloat($(e.target).val()) + (0.01 * (e.keyCode == 38 ? 1 : -1));
      $(e.target).val(v.toFixed(4));
    }

    set_map_bounds_from_fields();
    update_fields();
  });

  set_map_bounds_from_fields();
  update_fields();
  return map;
}
