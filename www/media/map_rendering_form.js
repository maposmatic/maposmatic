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

/* This function updates the landscape/portrait selectors according to
 * the portraitOk/landscapeOk booleans telling whether portrait and
 * landscape are possible. */
function filterAllowedOrientations(portraitOk, landscapeOk)
{
  landscape = $("input[value='landscape']");
  portrait  = $("input[value='portrait']");

  if (landscapeOk) {
    landscape.attr("disabled", "");
    landscape.attr("checked", "checked");
    landscape.parent().parent().removeClass("disabled");
  }
  else {
    landscape.attr("disabled", "disabled");
    landscape.parent().parent().addClass("disabled");
  }

  if (portraitOk) {
    portrait.attr("disabled", "");
    if (! landscapeOk)
      portrait.attr("checked", "checked");
    portrait.parent().parent().removeClass("disabled");
  }
  else {
    portrait.attr("disabled", "disabled");
    portrait.parent().parent().addClass("disabled");
  }
}

function bindPaperClickCallback(fn, portraitOk, landscapeOk)
{
  return (function(e) {
    fn(portraitOk, landscapeOk);
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
                            bindPaperClickCallback(filterAllowedOrientations,
                                                   paperDef[3], paperDef[4]));
      $(item).show();
    }
    else
      $(item).hide();

    if (paper == "Best fit") {
      paperSizeText = $("label em[class='papersize']", item);
      width_cm = paperDef[1] / 10;
      height_cm = paperDef[2] / 10;
      paperSizeText.html("(" + width_cm.toFixed(1) + " &times; " + height_cm.toFixed(1) + " cm²)");
    }
  });

  $("#paperselection").show();

  /* Make sure that default paper size and orientation are selected
   * by simulating a click on the first available paper */
  $("label input", $($("#papersizeselection ul li:visible")[0])).click();
}

function preparePaperPanel()
{
  /* Start the Ajax request to get the list of allowed paper
   * sizes */
  $("#paperselection").hide();
  if (getCurrentMode() == 'bbox') {
    args = {
      lat_upper_left   : $("#lat_upper_left").val(),
      lon_upper_left   : $("#lon_upper_left").val(),
      lat_bottom_right : $("#lat_bottom_right").val(),
      lon_bottom_right : $("#lon_bottom_right").val(),
      layout           : $("input[name='layout']:checked").val()
    };
  }
  else {
    args = {
      osmid  : $("#id_administrative_osmid").val(),
      layout : $("input[name='layout']:checked").val()
    };
  }

  $.post("/apis/papersize/", args,
         function(data) { filterAllowedPaper(data); });
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

/* Filter the set of available languages according to the country in
 * which the administrative boundary is. There is no filtering done
 * when the area is given by bounding box. */
function prepareLanguagePanel()
{
  var seen = false;

  $('#id_map_language').html(savedLanguageList);

  $('#id_map_language').children('option').each(function() {
    if (! ($(this).val().match('.._' + selectedCountry.toUpperCase() + '\..*') != null
           || $(this).val() == 'C'))
	  {
	    $(this).remove();
	  }
	  else {
      if (! seen) {
        $(this).attr("selected", "selected");
        seen = true;
      }
    }
  });
}

function prepareSummaryPanel()
{
  if (getCurrentMode() == 'bbox') {
    $("#summary-area").
      html("(" +
           $("#lat_upper_left").val() + ","          +
           $("#lon_upper_left").val() + ") &rarr; (" +
           $("#lat_bottom_right").val() + ","        +
           $("#lon_bottom_right").val() + ")");
  }
  else {
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

  function appendValidResult(item)
  {
    var id = 'rad_' + item.country_code + '_' + item.ocitysmap_params['id'];
    $results.append('<li style="list-style-type: disc; list-style-image: url('
                    + item.icon + ');" class="suggestok" id="' + id + '">'
                    + item.display_name + '</li>');

    var e = $('#' + id)
    e.bind('click', function(e) { setResult($(this)); });
    e.bind('mouseover', function(e) { setSelectedResultTo($(this)); });
  }

  function appendInvalidResult(item)
  {
    $results.append('<li style="list-style-type: disc; list-style-image: url('
                    + item.icon + ');" class="suggestoff">'
                    + item.display_name + ' (' + item.ocitysmap_params["reason_text"] + ')</li>');
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
      $results.append('<li class="info">' + $('#noadminlimitinfo').html() + '</li>');
  }

  function doQuery(excludes) {
    if (!$input.val().length) {
      closeSuggest(true);
      return;
    }
    $(input).css('cursor', 'wait');
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

/** Callback that the slippy map calls when a new area is defined. The
 * boolean tells whether the area is valid (not too big) or not valid
 * (too large to be rendered) */
function mapAreaSelectionNotifier(isvalid) {
    if (isvalid) {
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

  savedLanguageList = $('#id_map_language').html();

  suggest('#id_administrative_city', '#suggest',
          '#id_administrative_osmid',
          { selectedClass: 'selected',
            timeout: 150
          });
});
