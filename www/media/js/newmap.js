/* coding: utf-8 -*- mode: espresso; espresso-indent-level: 2; indent-tabs-mode: nil -*-
 *
 * maposmatic, the web front-end of the MapOSMatic city map generation system
 * Copyright (C) 2009-2010 David Decotigny
 * Copyright (C) 2009-2010 Frédéric Lehobey
 * Copyright (C) 2009-2010 David Mentré
 * Copyright (C) 2009-2010 Maxime Petazzoni
 * Copyright (C) 2009-2010 Thomas Petazzoni
 * Copyright (C) 2009-2010 Gaël Utard
 * Copyright (C) 2009-2010 Étienne Loks
 * Copyright (C) 2010 Pierre Mauduit
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

function mapTitleChange()
{
  if ($("#id_maptitle").val().length != 0)
    allowNextStep();
  else
    disallowNextStep();
}

function prepareTitlePanel()
{
  if (getCurrentMode() == 'bbox') {
    $("#id_maptitle").val("");
    disallowNextStep();
  }
  else {
    $("#id_maptitle").val($("#id_administrative_city").val());
    allowNextStep();
  }

  $('#id_maptitle').keyup(mapTitleChange);
}

/* Given a list of allowed paper sizes (paperlist), find the element
 * that correspond to a given paper name (paper) */
function getPaperDef(paperlist, paper)
{
  for (i in paperlist) {
    item = paperlist[i];
    if (paper == item[0])
      return item;
  }

  return null;
}

/* This function :
 *   - updates the landscape/portrait selectors according to the
 *     portraitOk/landscapeOk booleans telling whether portrait and
 *     landscape are possible.
 *   - updates the hidden fields paper_width_mm and paper_height_mm
 */
function handlePaperSizeClick(width_mm, height_mm, portrait_ok, landscape_ok)
{
  landscape = $("input[value='landscape']");
  portrait  = $("input[value='portrait']");

  if (landscape_ok) {
    landscape.attr("disabled", "");
    if (! portrait_ok)
      landscape.attr("checked", "checked");
    landscape.parent().parent().removeClass("disabled");
  }
  else {
    landscape.attr("disabled", "disabled");
    landscape.parent().parent().addClass("disabled");
  }

  if (portrait_ok) {
    portrait.attr("disabled", "");
    portrait.attr("checked", "checked");
    portrait.parent().parent().removeClass("disabled");
  }
  else {
    portrait.attr("disabled", "disabled");
    portrait.parent().parent().addClass("disabled");
  }

  $("#id_paper_width_mm").val(width_mm);
  $("#id_paper_height_mm").val(height_mm);
}

function bindPaperClickCallback(fn, width_mm, height_mm, portrait_ok, landscape_ok)
{
  return (function(e) {
    fn(width_mm, height_mm, portrait_ok, landscape_ok);
  });
}

function filterAllowedPaper(paperlist)
{
  /* Iterate through all paper lists, and hide those that do not
   * apply to the selected rendering, and bind click callbacks on
   * those that are available. The callback is in charge of updating
   * the available orientation for the choosen paper size */
  $.each($("#papersizeselection ul li"), function(id, item) {
    paper = $('label input[value]', item).val();
    paperDef = getPaperDef(paperlist, paper);
    if (paperDef != null) {
      $('label', item).bind('click',
                            bindPaperClickCallback(handlePaperSizeClick,
                                                   paperDef[1], paperDef[2],
                                                   paperDef[3], paperDef[4]));
      $(item).show();
      /* select the default paper size */
      if (paperDef[5])
          default_paper = $(item);
    }
    else
      $(item).hide();

    if (paperDef != null && paper == "Best fit") {
      paperSizeText = $("label em[class='papersize']", item);
      width_cm = paperDef[1] / 10;
      height_cm = paperDef[2] / 10;
      paperSizeText.html("(" +
                         width_cm.toFixed(1) + " &times; " +
                         height_cm.toFixed(1) + " cm²)");
    }
  });

  $("#paperselection").show();
  $("label input", $(default_paper)).click();
}

function preparePaperPanel()
{
  /* Start the Ajax request to get the list of allowed paper
   * sizes */
  $("#paperselection").hide();
  $("#nextlink").hide();
  if (getCurrentMode() == 'bbox') {
    args = {
      lat_upper_left   : $("#lat_upper_left").val(),
      lon_upper_left   : $("#lon_upper_left").val(),
      lat_bottom_right : $("#lat_bottom_right").val(),
      lon_bottom_right : $("#lon_bottom_right").val(),
      layout           : $("input[name='layout']:checked").val(),
      stylesheet       : $("input[name='stylesheet']:checked").val()
    };
  }
  else {
    args = {
      osmid      : $("#id_administrative_osmid").val(),
      layout     : $("input[name='layout']:checked").val(),
      stylesheet : $("input[name='stylesheet']:checked").val()
    };
  }

  $.post("/apis/papersize/", args,
         function(data) { filterAllowedPaper(data);
                          $("#nextlink").show()
                        });
}

/** When using a by admin boundary area, contains the country code of
 * the location to render. */
var selectedCountry;

/** Variable in which the HTML code of the language list is saved so
 * that we can remove items from this list and still be able to
 * repopulate with all items later. This is due to the unfortunate
 * fact that many browsers to do support .hide() and .show() on
 * <option> elements. */
var savedLanguageList;

function setSelectedCountryCallback(geoResults)
{
  $.each(geoResults, function(i, item) {
    if (typeof item.country_code != 'undefined') {
      selectedCountry = item.country_code;
    }
  });
}

/* We add the reverse() method to jQuery. See
 * http://www.mail-archive.com/discuss@jquery.com/msg04261.html for
 * details */
jQuery.fn.reverse = [].reverse;

/* Filter the set of available languages according to the country in
 * which the administrative boundary is. There is no filtering done
 * when the area is given by bounding box. */
function prepareLanguagePanel()
{
  var langlist = $('#id_map_language');

  langlist.html(savedLanguageList);

  /* The goal is to build a list of languages in which we have first
   * the languages matching the current country code, then an empty
   * disabled entry used as a separator and finally all other
   * languages. To do so, we use prependTo(), which adds elements at
   * the beginning of the list. So we start by prepending the
   * separator, then the "no localization" special language, and
   * finally the languages matching the current country code.
   */
  $('<option disabled="disabled"></option>').prependTo(langlist);
  $('option[value=C]', langlist).prependTo(langlist);

  langlist.children('option').reverse().each(function() {
    if ($(this).val().match('.._' + selectedCountry.toUpperCase() + '\..*') != null) {
      $(this).prependTo(langlist);
    }
  });

  $('option:first', langlist).attr("selected", "selected");
}

function prepareSummaryPanel()
{
  if (getCurrentMode() == 'bbox') {
    $("#summary-area").
      html("(" +
           $("#lat_upper_left").val() + ", "         +
           $("#lon_upper_left").val() + ") &rarr; (" +
           $("#lat_bottom_right").val() + ", "       +
           $("#lon_bottom_right").val() + ")");
  }
  else {
    osmid = $("#id_administrative_osmid").val();
    $("#summary-area").
      html($("#id_administrative_city").val() +
           ' (<a href="http://www.openstreetmap.org/browse/relation/' +
           Math.abs(osmid) + '" title="OSM ID: ' + Math.abs(osmid) + '">' +
           'OpenStreetMap</a>)');
  }

  $("#summary-title").html($("#id_maptitle").val().trim());
  $("#summary-layout").html($("input[name='layout']:checked").parent().text().trim());
  $("#summary-papersize").html($("input[name='papersize']:checked").parent().text().trim());
  $("#summary-stylesheet").html($("input[name='stylesheet']:checked").parent().text().trim());
  $("#summary-language").html($("#id_map_language :selected").text());
}

/** Function called *before* showing a given panel. It gives the
 * opportunity to update informations in this panel. */
function prepareNextPage(next)
{
    if (next == "step-title")
        prepareTitlePanel();
    else if (next == "step-paper")
        preparePaperPanel();
    else if (next == "step-summary")
        prepareSummaryPanel();
    else if (next == "step-language")
        prepareLanguagePanel();
}

/*
 * Helper functions to hide/show the back/next links
 */

function allowPrevStep() {
  $('#prevlink').addClass('allowed');
}

function disallowPrevStep() {
  $("#prevlink").removeClass('allowed');
}

function allowNextStep() {
  $("#nextlink").addClass('allowed');
}

function disallowNextStep() {
  $("#nextlink").removeClass('allowed');
}

/** Hide a panel and un-highlight the corresponding title in the
 * progress bar */
function hidePanel(panel) {
  id = panel.attr("id");
  panel.hide();
  $("#" + id + "-title").removeClass("title-current-step");
}

/** Show a panel and highlight the corresponding title in the progress
 * bar */
function showPanel(panel) {
  id = panel.attr("id");
  panel.show();
  $("#" + id + "-title").addClass("title-current-step");
}

/** Selectors used in loadNextStep() and loadPrevStep() to
 * respectively find all panels and the currently visible panel */
const STEP_PANEL_SELECTOR = "div[id|=step][class=wizardstep]";
const VISIBLE_STEP_PANEL_SELECTOR = "div[id|=step][class=wizardstep]:visible";
const FIRST_INPUT_SELECTOR =
    VISIBLE_STEP_PANEL_SELECTOR + " input:visible:first, " +
    VISIBLE_STEP_PANEL_SELECTOR + " select:visible:first"

/** Replace the panel of the current step by the panel of the next
    step, after preparing it. Also makes sure that Back/Next links are
    enabled/disabled as needed. */
function loadNextStep()
{
  current = $(VISIBLE_STEP_PANEL_SELECTOR);
  next = current.next(STEP_PANEL_SELECTOR);
  hasafternext = (next.next(STEP_PANEL_SELECTOR).length != 0);

  prepareNextPage(next.attr("id"));
  hidePanel(current);
  showPanel(next);

  allowPrevStep();
  if (! hasafternext)
    disallowNextStep();

  $(FIRST_INPUT_SELECTOR).focus()
}

/** Replace the panel of the current step by the panel of the next
    step. Also makes sure that Back/Next links are enabled/disabled as
    needed. */
function loadPrevStep()
{
  current = $(VISIBLE_STEP_PANEL_SELECTOR);
  prev = current.prev(STEP_PANEL_SELECTOR);
  hasbeforeprev = (prev.prev(STEP_PANEL_SELECTOR).length != 0);

  hidePanel(current);
  showPanel(prev);

  allowNextStep();
  if (! hasbeforeprev)
    disallowPrevStep();
}

/** Auto-suggest feature. */
function suggest(input, results, osm_id, options) {
  var $input = $(input).attr('autocomplete', 'off');
  var $results = $(results);
  var $osm_id = $(osm_id);
  var timeout = false;
  var shown = false;
  var ajaxSuggestQuery = null;

  closeSuggest(true);

  // Setup the keyup event.
  $input.keyup(processKey);

  // Disable form validation via the Enter key
  $input.keypress(function(e) {
    if (e.keyCode == 13) {
        if  ($osm_id.val() != '')
            loadNextStep();
        return false;
    }
  });

  function appendValidResult(item)
  {
    var id = 'rad_' + item.country_code + '_' + item.ocitysmap_params['id'];
    $results.append('<li class="suggestok" id="' + id + '"><img src="'
                    + item.icon + '" />'
                    + item.display_name + '</li>');

    var e = $('#' + id)
    e.bind('click', function(e) { setResult($(this)); });
    e.bind('mouseover', function(e) { setSelectedResultTo($(this)); });
  }

  function appendInvalidResult(item)
  {
    $results.append('<li class="suggestoff" title="'
                    + item.ocitysmap_params["reason_text"] + '">'
                    + '<img src="' + item.icon + '" />'
                    + item.display_name + '</li>');
  }

  /* Empty and close the suggestion box. */
  function closeSuggest(hide)
  {
    $results.empty();

    if (hide)
      $results.hide();
    else
      $results.show();

    shown = !hide;
  }

  function bindDoQuery(excludes)
  {
    return (function(e) {
      closeSuggest(true);
      doQuery(excludes);
    });
  }

  /* Handle the JSON result. */
  function handleNominatimResults(data, textResult)
  {
    var unusable_token = false;
    var entries = data.entries
    $(input).css('cursor', 'text');
    closeSuggest(false);

    /* Hide the nice loading icon since loading is finished */
    $('#id_administrative_city').css("background-image", "");

    if (!entries.length) {
      $results.append('<li class="info">' + $('#noresultsinfo').html() + '</li>');
      return;
    }

    $.each(entries, function(i, item) {
      if (item.ocitysmap_params["valid"] == 1) {
        appendValidResult(item);
      }
      else {
        appendInvalidResult(item);
        unusable_token = true;
      }
    });

    if (data.hasprev != "" || data.hasnext != "")
    {
      $results.append('<li class="info">');
      if (data.hasprev != "") {
        $results.append('<input type="submit" id="suggestprev" value="Previous"/>');
        $("#suggestprev").bind('click', bindDoQuery(data.prevexcludes));
      }

      if (data.hasnext != "") {
        $results.append('<input type="submit" id="suggestnext" value="Next"/>');
        $("#suggestnext").bind('click', bindDoQuery(data.nextexcludes));
      }
      $results.append('</li>');
    }

    if (unusable_token)
      $results.append('<li class="info">' + $('#noadminboundary').html() + '</li>');
  }

  function doQuery(excludes) {
    if (!$input.val().length) {
      closeSuggest(true);
      return;
    }
    $(input).css('cursor', 'wait');

    /* Show a nice loading icon */
    $('#id_administrative_city').css("background-image", "url(/smedia/loading.gif)");

    if (ajaxSuggestQuery != null)
      ajaxSuggestQuery.abort();

    ajaxSuggestQuery =
      $.getJSON("/apis/nominatim/",
                { q: $input.val(), exclude: excludes },
                handleNominatimResults);
  }

  function processKey(e) {
    if (e.keyCode != 13) {
      clearResult();
    }

    switch (e.keyCode) {
      case 27:  // ESC
        closeSuggest(true);
        break;
      case 9:   // TAB
      case 13:  // OK
        var elt = getCurrentResult();
        if (elt)
          setResult(elt);
        return false;
        break;
      case 38:  // UP
        if (!shown)
          doQuery('');
        prevResult();
        break;
      case 40:  // DOWN
        if (!shown)
          doQuery('');
        nextResult();
        break;
      case 37: //LEFT
      case 39: //RIGHT
        break;
      default:
        if (timeout)
          clearTimeout(timeout);
        timeout = setTimeout(function() { doQuery(''); }, options.timeout);
      }
  }

  /* Returns the currently selected result. */
  function getCurrentResult() {
    var children = $results.children('li.' + options.selectedClass);
    if (children.length)
      return children;
    return false;
  }

  /* Set the form to the given result. */
  function setResult(elt) {
    var temp = elt.attr('id').split('_');

    selectedCountry = temp[1];
    $osm_id.val(temp[2]);
    $input.val(elt.text());

    closeSuggest(true);
    allowNextStep();
  }

  function clearResult() {
    $osm_id.val('');
    disallowNextStep();
  }

  /** Functions to manipulate the current selection. */

  /* Set the currently selected item in the drop-down list. */
  function setSelectedResultTo(elt) {
    $results.children('li').removeClass(options.selectedClass);
    if (elt)
      elt.addClass(options.selectedClass);
  }

  /* Move to the previous valid result. */
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

  /* Move to the next valid result. */
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
}

/** Returns whether 'admin' or 'bbox' mode is currently selected */
function getCurrentMode() {
  if ($('#id_mode_1').is(':checked'))
     return 'bbox';
  else
     return 'admin';
}

var bboxReverseGeoAjaxQuery = null;

/** Callback that the slippy map calls when a new area is defined. The
 * boolean tells whether the area is valid (not too big) or not valid
 * (too large to be rendered) */
function mapAreaSelectionNotifier(isvalid, bounds) {
  if (isvalid) {
    center = bounds.getCenterLonLat();
    if (bboxReverseGeoAjaxQuery != null)
      bboxReverseGeoAjaxQuery.abort();
    bboxReverseGeoAjaxQuery =
      $.getJSON("/apis/reversegeo/" + center.lat + "/" + center.lon + "/",
                { }, setSelectedCountryCallback);
    allowNextStep();
    $("#toobigareaerror").hide();
  }
  else {
    disallowNextStep();
    $("#toobigareaerror").show();
  }
}

/** Page initialization. */
$(document).ready(function() {

  function switchToAdminMode() {
    $('#step-location-bbox').hide();
    $('#step-location-admin').show();
    $('#id_administrative_city').focus();
    disallowNextStep();
    selectedCountry = "";
  }

  function switchToBBoxMode() {
    $('#step-location-admin').hide();
    $('#step-location-bbox').show();
    disallowNextStep();
    $('#id_administrative_city').empty();
    $('#id_administrative_osmid').empty();
    if (map == null)
      mapInit(mapAreaSelectionNotifier);
    selectedCountry = "";
  }

  $('#id_mode_0').bind('click', function(e) { switchToAdminMode(); });
  $('#id_mode_1').bind('click', function(e) { switchToBBoxMode(); });

  savedLanguageList = $('#id_map_language').html();

  suggest('#id_administrative_city', '#suggest',
          '#id_administrative_osmid',
          { selectedClass: 'selected',
            timeout: 250
          });

  $('td.step').keypress(function(e) {
     if (e.keyCode == 13) {
        current = $(VISIBLE_STEP_PANEL_SELECTOR);
        next = current.next(STEP_PANEL_SELECTOR);
        if (next.length != 0) {
          loadNextStep();
          return false;
        }
     }
  });

  $('#step-location').show();
  $('#id_administrative_city').focus();
});
