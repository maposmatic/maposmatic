/* coding: utf-8 -*- mode: espresso; indent-tabs-mode: nil -*-
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

var currentPanel = 1;

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

function filterAllowedPaperSizes(papersizelist)
{
  $.each($("#step-papersize ul li"), function(id, item) {
     papersize = $('label input[value]', item).val();
     if (jQuery.inArray(papersize, papersizelist) < 0)
       $(item).hide();
     else
       $(item).show();
  });

  $("#step-papersize ul").show();
  $("label input", $($("#step-papersize ul li:visible")[0])).attr("checked", "true");
}

function preparePaperSizePanel()
{
    $("#step-papersize ul").hide();
    if (getCurrentMode() == 'bbox')
    {
      $.post("/papersize/", {
                lat_upper_left   : $("#lat_upper_left").val(),
                lon_upper_left   : $("#lon_upper_left").val(),
                lat_bottom_right : $("#lat_bottom_right").val(),
                lon_bottom_right : $("#lon_bottom_right").val(),
                layout           : $("input[name='layout']:checked").val()
             },
             function(data) {
                filterAllowedPaperSizes(data);
             }
            );
    }
    else
    {
      $.post("/papersize/", {
                osmid: $("#id_administrative_osmid").val(),
                layout           : $("input[name='layout']:checked").val()
             },
             function(data) {
                filterAllowedPaperSizes(data);
             }
            );
    }
}

/** When using a by admin boundary area, contains the country code of
 * the location to render. */
var selectedCountry;

function prepareLanguagePanel()
{
    var seen = false;
    $('#id_map_language').children('option').each(function() {
        if (! ($(this).val().match('.._' + selectedCountry.toUpperCase() + '\..*') != null
               || $(this).val() == 'C'))
        {
            $(this).hide();
        }
        else {
            $(this).show();
            if (! seen) {
                $(this).attr("selected", "selected");
                seen = true;
            }
        }
    });
}

function prepareSummaryPanel()
{
    if (getCurrentMode() == 'bbox')
    {
        $("#summary-area").
            html("(" +
                 $("#lat_upper_left").val() + ","          +
                 $("#lon_upper_left").val() + ") &rarr; (" +
                 $("#lat_bottom_right").val() + ","        +
                 $("#lon_bottom_right").val() + ")");
    }
    else
    {
        osmid = $("#id_administrative_osmid").val();
        $("#summary-area").
            html($("#id_administrative_city").val() +
                 "<br/>(osm: <a href=\"http://www.openstreetmap.org/browse/relation/" +
                 Math.abs(osmid) + "\">relation " + Math.abs(osmid) + "</a>)");
    }

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
    else if (next == "step-papersize")
        preparePaperSizePanel();
    else if (next == "step-summary")
        prepareSummaryPanel();
    else if (next == "step-language")
        prepareLanguagePanel();
}

/*
 * Helper functions to hide/show the back/next links
 */

function allowPrevStep() {
  $("#prevlinkdisabled").hide();
  $("#prevlink").show();
}

function disallowPrevStep() {
  $("#prevlinkdisabled").show();
  $("#prevlink").hide();
}

function allowNextStep() {
  $("#nextlinkdisabled").hide();
  $("#nextlink").show();
}

function disallowNextStep() {
  $("#nextlinkdisabled").show();
  $("#nextlink").hide();
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

  closeSuggest(true);

  // Setup the keyup event.
  $input.keyup(processKey);

  // Disable form validation via the Enter key
  $input.keypress(function(e) { if (e.keyCode == 13) return false; });

  function appendValidResult(item) {
    var id = 'rad_' + item.country_code + '_' + item.ocitysmap_params['id'];
    $results.append('<li class="suggestok" id="' + id + '">'
       + item.display_name + '</li>');

    var e = $('#' + id)
    e.bind('click', function(e) { setResult($(this)); });
    e.bind('mouseover', function(e) { setSelectedResultTo($(this)); });
  }

  /* Empty and close the suggestion box. */
  function closeSuggest(hide) {
    $results.empty();

    if (hide)
      $results.hide();
    else
      $results.show();

    shown = !hide;
  }

  /* Handle the JSON result. */
  function handleNominatimResults(data, textResult) {
    var unusable_token = false;
    $(input).css('cursor', 'text');
    closeSuggest(false);

    if (!data.length) {
      $results.append('<li class="info">' + $('#noresultsinfo').html() + '</li>');
      return;
    }

    $.each(data, function(i, item) {
      if (typeof item.ocitysmap_params != 'undefined' &&
          item.ocitysmap_params['admin_level'] == 6) {
        appendValidResult(item);
      } else {
        $results.append('<li class="suggestoff">'
          + item.display_name + '</li>');
        unusable_token = true;
      }
    });

    if (unusable_token)
      $results.append('<li class="info">' + $('#noadminlimitinfo').html() + '</li>');
  }

  function doQuery() {
    if (!$input.val().length) {
      closeSuggest(true);
      return;
    }
    $(input).css('cursor', 'wait');
    $.getJSON("/nominatim/", { q: $input.val() }, handleNominatimResults);
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
          doQuery();
        prevResult();
        break;
      case 40:  // DOWN
        if (!shown)
          doQuery();
        nextResult();
        break;
      default:
        if (timeout)
          clearTimeout(timeout);
        timeout = setTimeout(doQuery, options.timeout);
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
    $input.val(elt.html());

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

function mapAreaSelectionNotifier() {
  allowNextStep();
}

/** Page initialization. */
$(document).ready(function() {

  function switchToAdminMode() {
    $('#step-location-bbox').hide();
    $('#step-location-admin').show();
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

  if (getCurrentMode() == 'bbox')
    switchToBBoxMode();
  else
    switchToAdminMode();

  $('#id_mode_0').bind('click', function(e) { switchToAdminMode(); });
  $('#id_mode_1').bind('click', function(e) { switchToBBoxMode(); });

  suggest('#id_administrative_city', '#suggest',
          '#id_administrative_osmid',
          { selectedClass: 'selected',
            timeout: 150
          });
});
