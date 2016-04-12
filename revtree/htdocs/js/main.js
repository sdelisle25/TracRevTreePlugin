/**
 * @ main.js
 * Main application entry point
 * @author Neotion (c) 2015
 */

'use strict';

/**
 * Register jQuery previously loaded by Trac
 */
define('jquery', [], function() { return window.jQuery; });

/**
 * require.js configuration
 */
require.config({
  // The shim config allows us to configure dependencies for
  // scripts that do not call define() to register a module
//    shim: {
//      underscore: {
//        exports: '_'
//      }
//    },
    /* Paths for js loader */
    paths: {
      'underscore': 'underscore-1.7.0/underscore'
    }
});


/**
 * Main entry point
 */
require(['jquery', 'revtree'],
  function($, RevTree) {
    $(document).ready(function($) {
        var warning_ctrl;
        var window_ctrl;
        var tools_ctrl;
        var tools_top;
        var tools_margin_left;
        var xhr;

        initializeFilters();

        $("#nav-changeset").hide();
        $("#warning").hide();
        warning_ctrl = $("#warning").clone(true);

        $("#group").change(function() {
          $("#groupdesc").enable(this.selectedIndex != 0);
        }).change();

        $(".foldable").enableFolding(false);

        $("input[name$='_branch']").each(function() {
          $(this).neosuggest('', 'autocompletion', null);
        });

        $(".datepicker").datepicker();

        window_ctrl = $(window);
        tools_ctrl = $("#tools");
        tools_margin_left = tools_ctrl.offset().left;
        tools_top = tools_ctrl.offset().top;

        $(window).scroll(function() {
          var sv_flag;
          var sh_flag;

          sv_flag = window_ctrl.scrollTop() >= tools_top;
          sh_flag = window_ctrl.scrollLeft();

          tools_ctrl.toggleClass('fixed', sv_flag);
          if (window_ctrl.scrollTop() >= tools_top) {
            $("#svg").css("margin-top", tools_ctrl.outerHeight(true) + "px");
          }
          else {
            $("#svg").css("margin-top", "0px");
          }

          if(sv_flag) {
            tools_ctrl.css("left", tools_margin_left + "px");
          }

          if(sh_flag && !sv_flag) {
            tools_ctrl.css("margin-left", window_ctrl.scrollLeft() +"px");
          }
          else {
             tools_ctrl.css("margin-left", "0px");
          }
        });

        $("#svg").dblclick(function(event){
          event.preventDefault();
          event.stopPropagation();

          RevTree.prototype.abort_action_selector(event);
        });

        var ajax_success = function(data) {
           var tree;

           $("#main :input").attr("disabled", "disabled");

           tree = new RevTree(data.tree, data.url, data.style);

           window.revtree = tree;
           tree.init();

           var field = $("#metrics");
           field.css("font-family", data.fontfamily);
           field.css("font-size", data.fontsize);

           tree.build(1.0);
           tree.render();

           tree = null;

           $("#main :input").removeAttr("disabled");

           $("#zoom").show();
           $("#scale").show();

           /* REMARK: fix strange behavior float property not properly done */
           $("#svgview").css("display", "none");
           $("#svgview").css("display", "block");

           $("select[name$='_revision']").each(function() {
             var value = $(this).val();
             $(this).empty();
             $(this).addOptions(data.revisions);

             window.revisions = data.revisions;
             $(this).val(value);
           });

           $("select[name$='_author']").each(function() {
             var value = $(this).val();
             $(this).empty();
             $(this).addOptions(data.authors);

             window.authors = data.authors;

             $(this).val(value);
           });

           $("body h1").removeClass("blink");

           /* Adjust toolbox position with footer position */
           var bottom;

           bottom = $(document).height() - $("#footer").offset().top;
           $("#toolbox").css("bottom", bottom + 5);
         };

         var ajax_error =  function(xhr, ajaxOptions, thrownError)
         {
           if(xhr.status == 404) {
             var ctrl;
             ctrl = warning_ctrl.clone(true);
             $("#warning").replaceWith(ctrl.append(xhr.responseText));
             $("#warning").show();
           }
           else {
             $("#svg_errormsg").html(xhr.responseText);
             $("#svg_errormsg").show();
           }
           $("body h1").removeClass("blink");
         };

        $('#submit_reset').on('click', function(event) {
           event.preventDefault();
           event.stopPropagation();

           $.ajax({
             url: "",
             type: "POST",
             async: true,
             dataType: 'json', /* Server response data format */
             data: $("#query_form").serialize() + "&reset=True",
             success: function(data) {
               /* Redirect to revtree main page */
               window.location.href = "revtree";
             }
           });
        });


        // Ajax request for filter processing
        $('#submit_filters').on('click', function(event) {
           event.preventDefault();
           event.stopPropagation();

           $("#info_esc").removeClass("indicator-esc-show");

           if(xhr && xhr.readyState != 4) {
             xhr.abort();
           }

           $("#warning").hide();
           $("#svg_errormsg").hide();
           $("#nav-changeset").hide();
           $("#zoom").hide();
           $("#scale").hide();
           $("#svg").empty();

           $("body h1").addClass("blink");

           xhr = $.ajax({
             url: "",
             type: "POST",
             async: true,
             dataType: 'json', /* Server response data format */
             data: $("#query_form").serialize(),
             success: ajax_success,
             error: ajax_error
           });
        });

        // Simulate click on filter update button
        $('#submit_filters').trigger('click');
      });
  }
);
