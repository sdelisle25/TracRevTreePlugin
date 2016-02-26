/* Warning: this module is deprecated and will be removed in Trac 1.1.x
 *
 * Don't use $.suggest in your own plugins, rather look into jquery-ui's
 * autocomplete features (http://docs.jquery.com/UI/Autocomplete).
 */
(function($){


  /*
   Text field auto-completion plugin for jQuery.
   Based on http://www.dyve.net/jquery/?autocomplete by Dylan Verheul.
  */
  $.neosuggest = function(input, url, paramName, callback, minChars, delay) {
    var input = $(input).addClass("suggest").attr("autocomplete", "off");
    var timeout = null;
    var prev = "";
    var selectedIndex = -1;
    var results = null;
    var result;
    var scroll_done;

    input.keydown(function(e) {
      switch(e.keyCode) {
        case 27: // escape
          hide();
          break;
        case 38: // up
        case 40: // down
          e.preventDefault();
          if (results) {
            var items = $("li", results);
            if (!items) return;
            var index = selectedIndex + (e.keyCode == 38 ? -1 : 1);
            if (index >= 0 && index < items.length) {
              move(index);
            }
          } else {
            show();
          }
          break;
        case 9:  // tab
          if(results) {
            e.preventDefault();
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(show, delay);
            result = search_common_prefix(input.val());
            if(result) {
              input.val(result);
            }
            break;
          }
        case 13: // return
        case 39: // right
          if (results) {
            var li = $("li.selected", results);
            if (li.length) {
              select(li);
              e.preventDefault();
            }
          }
          break;
        default:
          if (timeout) clearTimeout(timeout);
          timeout = setTimeout(show, delay);
          break;
      }
    });
    input.blur(function() {
      if (timeout) clearTimeout(timeout);
      timeout = setTimeout(hide, 200);
    });

    function search_common_prefix(prefix)
    {
      var mo_list = new Array();
      var jq_ctrl;
      var value;
      var shorten_string=null;

      if(!results) {
        return null;
      }
      $.each($("li", results), function(index, value) {
        jq_ctrl = $(value);

        value = jq_ctrl.text();
        if(value.indexOf(prefix) == 0) {
          mo_list.push(value);
          if(!shorten_string) {
            shorten_string = value;
          }
          else
            if(value.length < shorten_string.length) {
              shorten_string = value;
            }
        }
      });

      /* Prefix not match */
      if(!mo_list) {
        return null;
      }

      /* One match */
      if(mo_list.length == 1) {
        return mo_list[0];
      }

      /* Search longest prefix */
      var idx = prefix.length;
      iter:
      for(; idx < shorten_string.length; idx++) {
        for(var i=0; i < mo_list.length; i++) {
          if(shorten_string[idx] != mo_list[i][idx]) {
            break iter;
          }
        }
      }

      return shorten_string.substring(0, idx);
    }

    function hide() {
      if (timeout) clearTimeout(timeout);
      input.removeClass("loading");
      if (results) {
        results.fadeOut("fast").remove();
        results = null;
      }
      $("iframe.iefix").remove();
      selectedIndex = -1;
    }

    function move(index, scroll)
    {
      var item_pos;
      var items, item;
      var scroll_pos, container;
      var hcontainer, container_pos;
      var hitem;

      if (!results) return;

      /* List container */
      container = $("ul", results);
      items = $("li", results);
      items.removeClass("selected");
      $(items[index]).addClass("selected");
      selectedIndex = index;

      /* Get scroll position */
      scroll_pos = container.scrollTop();

      item = $(items[index]);
      if(!item) {
        return;
      }

      item_pos = item.position();
      if(!item_pos) {
        return;
      }

      hcontainer = results.height();
      container_pos = results.position();
      hitem = item.outerHeight(true);

      scroll_done = true;
      /* Item is above container */
      if((item_pos.top + hitem) > hcontainer)
      {
        container.scrollTop(scroll_pos + hitem);
      }
      else
      /* Item is below container */
      if((item_pos.top + hitem) <= scroll_pos) {
        container.scrollTop(scroll_pos - hitem);
      }
      else {
        scroll_done = false;
      }
    }

    function move_hover(event, index) {
      var items, item;
      var container;

      event.preventDefault();

      if (!results) return;

      if(scroll_done === true) {
        scroll_done = false;
        return;
      }

      /* List container */
      container = $("ul", results);
      items = $("li", results);
      items.removeClass("selected");

      $(items[index]).addClass("selected");
      selectedIndex = index;
    }

    function select(li) {
      if (!li) li = $("<li>");
      else li = $(li);
      var val = $.trim(li.text());
      prev = val;
      input.val(val);
      hide();
      selectedIndex = -1;
    }

    function show() {
      var val = input.val();
      if (val == prev) return;
      prev = val;
      if (val.length < minChars) { hide(); return; }
      input.addClass("loading");
      var params = {};
      params[paramName] = val;

      if(callback != null) {
        var params_ext = callback()
        for(var key in params_ext) {
          params[key] = params_ext[key]
        }
      }

      $.get(url, params, function(data) {
        var items;
        var parent;

        if (!data) { hide(); return; }

        /* Suggest droplist */
        if (!results) {
          var offset = input.offset();

          results = $("<div>").addClass("suggestions").css({
            position: "absolute",
            minWidth: input.get(0).offsetWidth + "px",
            top: (offset.top + input.get(0).offsetHeight) + "px",
            left: offset.left + "px",
            zIndex: 1010
          }).appendTo("body");
        }

        results.html(data).fadeTo("fast", 0.92);
        items = $("li", results);

        // REMARK: disable hover becauseof side effects with direction keys
        items.hover(function(event) { move_hover(event, items.index(this)) },
                     function() { $(this).removeClass("selected") }).click(
                       function() { select(this); input.get(0).focus() });

        move(0);
      }, 'html');
    }
  }

  $.fn.neosuggest = function(url, paramName, callback, minChars, delay) {
    url = url || window.location.pathname;
    paramName = paramName || 'q';
    minChars = minChars || 1;
    delay = delay || 200;
    callback = callback
    return this.each(function() {
      new $.neosuggest(this, url, paramName, callback, minChars, delay);
    });
  }

})(jQuery);
