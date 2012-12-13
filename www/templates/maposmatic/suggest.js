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
 * Administrative boundary auto-suggest/auto-complete box.
 *
 * @param input The input text element.
 * @param list The results list element.
 * @param target The OSM ID input field element.
 * @param timeout An optional timeout value for the auto suggestions, in
 * milliseconds.
 */
(function suggest(input, list, target, timeout) {

  input.attr('autocomplete', 'off').attr('placeholder', '{% trans "Start typing for suggestions..." %}').focus();

  var timeoutId = null;
  var ajaxquery = null;

  function show() { if ($(list).css('display') == 'none') { list.show(); } }
  function hide() { if ($(list).css('display') != 'none') { list.hide(); list.empty(); } }

  function query(exclude) {
    hide();
    $('#error-icon').hide();
    $('#loading-icon').show();

    if (ajaxquery != null) {
      ajaxquery.abort();
    }

    ajaxquery = $.getJSON('/apis/nominatim/', {q: input.val()})
      .complete(function() { $('#loading-icon').hide(); })
      .success(function(data) { process(data); })
      .error(function(xhr, ts, error) {
        if (ts != 'abort') {
          $('#error-icon').attr('title', error).show();
        }
      });
  }

  function process(data) {
    var entries = data.entries;

    if (!entries.length) {
      return;
    }

    $.each(entries, function(i, entry) {
      if (entry.ocitysmap_params &&
          entry.ocitysmap_params['valid'] == 1) {
        var id = 'rad_' + entry.country_code + '_' + entry.ocitysmap_params['id'];
        list.append('<li><a class="suggestok" href="#" id="' + id + '">' +
          '<img src="' + entry.icon + '" />' +
          entry.display_name + '</a></li>');
      } else {
        list.append('<li><a class="suggestoff" title="' +
          (entry.ocitysmap_params ? entry.ocitysmap_params['reason_text'] : '') + '">' +
          '<img src="' + entry.icon + '" />' + entry.display_name + '</a></li>');
      }
    });

    // Bind each result's click event to set the result field.
    $('a.suggestok', list).bind('click', function() {
      set($(this));
    });
    show();
  }

  function set(result) {
    var temp = result.attr('id').split('_');

    country = temp[1];
    target.val(temp[2]);
    input.val(result.text());
    $('#id_maptitle').val(result.text());
    hide();

    setPrevNextLinks();
    $('#nextlink').focus();
  }

  input.keypress(function(e) {
    if (e.keyCode == 13) {
      if (target.val()) {
        $('#wizard').carousel('next');
        return false;
      }
    }
  });

  // The escape key can only reliably get caught on the document.
  $(document).keyup(function(e) {
    if (e.keyCode == 27) {
      hide();
      input.focus();
    }
  });

  input.keyup(function(e) {
    switch (e.keyCode) {
      case 9:  // TAB
      case 13: // OK
        return false;
        break;

      case 37: // LEFT
      case 39: // RIGHT
        break;

      case 38: // UP
        hide();
        return false;
        break;

      case 40: // DOWN
      default:
        target.val('');
        setPrevNextLinks();

        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        timeoutId = setTimeout(function() {
          if (input.val()) {
            query();
          }
        }, timeout);
        break;
    }
  });
})($('#id_administrative_city'), $('#suggest'), $('#id_administrative_osmid'), 200);
