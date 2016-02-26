/**
 * Main RevTree module
 *
 * @file revtree.js
 * @author Neotion (c) 2014-2015
 */

"use strict";
define(['jquery', 'revtree_branch'],
    function($, RevTreeBranch) {
        var UNIT = 25;
        var zoom_ratio = 1.0;
        var neorevtree = {};
        var tooltip_timer = null;

        /* Publish neorevtree object */
        window.neorevtree = neorevtree;

        function zoom(ratio) {
            var svgbox = $("#svgview");

            zoom_ratio = zoom_ratio * ratio;

            /* REMARK: for safari to force redraw hide current SVG */
            svgbox.css('display', 'none');
            svgbox.attr("width", svgbox.attr("width") * ratio);
            svgbox.attr("height", svgbox.attr("height") * ratio);
            svgbox.css('display', 'block');

            svgbox = null;
        }

        /* Publish zoom */
        window.neorevtree.zoom = zoom;

        function scale(ratio) {
            var svgbox = $("#svgview");
            var width = svgbox.attr("width");
            var height;

            svgbox.css('display', 'none');
            $("#svg").empty();

            window.revtree.build(ratio);
            window.revtree.render();

            svgbox.attr("width", svgbox.attr("width") * zoom_ratio);
            svgbox.attr("height", svgbox.attr("height") * zoom_ratio);
            svgbox.css('display', 'block');

            svgbox = null;
        }
        /* Publish scale */
        window.neorevtree.scale = scale;

        function scroll_src(event) {
            var widget = $("[changeset='" + window.neorevtree.src_rev + "']");
            var xoffset;
            var yoffset;

            xoffset = (window.innerWidth / 2);
            yoffset = (window.innerHeight / 2);

            $('html,body').animate({
                scrollLeft : widget.offset().left - xoffset + (widget.width() / 2),
                scrollTop : widget.offset().top - yoffset - (widget.height() / 2)
            }, 500);
            event.preventDefault();
            event.stopPropagation();

            widget = null;
        }
        /* Publish scrolling to source */
        window.neorevtree.scroll_src = scroll_src;

        function scroll_dest(event) {
            var widget = $("[changeset='" + window.neorevtree.dest_rev + "']");
            var xoffset;
            var yoffset;

            xoffset = (window.innerWidth / 2);
            yoffset = (window.innerHeight / 2);

            $('html,body').animate({
                scrollLeft : widget.offset().left - xoffset + (widget.width() / 2),
                scrollTop : widget.offset().top - yoffset - (widget.height() / 2)
            }, 500);
            event.preventDefault();
            event.stopPropagation();

            widget = null;
        }
        /* Publish scrolling to destination */
        window.neorevtree.scroll_dest = scroll_dest;

        /* Keyboard handler */
        var setKeyboardHandler = function(id) {
            $(document).bind('keydown', function(event) {
                var ratio = 0;
                if (event.ctrlKey || event.metaKey) {
                    switch (String.fromCharCode(event.which).toLowerCase()) {
                    /* scale in */
                    case 'q':
                        scale(1.05);
                        event.preventDefault();
                        event.stopPropagation();
                        break;

                    /* scale out */
                    case 's':
                        scale(0.95);
                        event.preventDefault();
                        event.stopPropagation();
                        break;

                    /* Zoom In */
                    case 'a':
                        zoom(1.05);
                        event.preventDefault();
                        event.stopPropagation();
                        break;

                    /* Zoom Out */
                    case 'z':
                        zoom(0.95);
                        event.preventDefault();
                        event.stopPropagation();
                        break;

                    /* Goto source changeset */
                    case 's':
                        scroll_src(event);
                        break;

                    /* Goto destination changeset */
                    case 'd':
                        scroll_dest(event);
                        break;
                    }
                } else {
                    switch (event.which) {
                    case 27:
                        abort_action_selector();
                        break;
                    }
                }
            });
        };

        function loginfo_update(data) {
            var ctrl = document.getElementById('tooltip_body');

            $("#tooltip_body").removeClass("tooltip_waiting");
            ctrl.innerHTML = data;

            ctrl = null;
        }

        function tooltip_cancel() {
            if (tooltip_timer) {
                clearTimeout(tooltip_timer);
                tooltip_timer = null;
            }
        }

        function revtree_mouseover(widget, revision) {
            var x, y;
            var div;
            var rect;
            var div;
            var chgset;
            var url;
            var ww = window.innerWidth;
            var wh = window.innerHeight;
            var u = window.scrollWidth;
            var right, left, bottom, top;
            var tooltip = $("#tooltip");

            tooltip_cancel();

            chgset = window.revtree.get_changeset(revision);

            /* Adjust position by using scroll bars position */
            rect = widget.getBoundingClientRect();

            var px = window.pageXOffset;
            var py = window.pageYOffset;

            right = rect.right;
            left = rect.left;
            bottom = rect.bottom;
            top = rect.top;

            /* Tooltip connection */
            if (ww - right < 200) {
                x = left - 19;
                y = bottom - rect.height / 2 - 2;
            } else {
                x = right;
                y = bottom - rect.height / 2 - 2;
            }

            div = $("#tooltip_connect");
            div.css("left", x + px + "px");
            div.css("top", y + py + "px");
            div.css("background-color", chgset.fillcolor());
            div.css("border-color", chgset.strokecolor());

            /* Tool tip tittle */
            div = $("#tooltip_title");
            div.hover(function() {
                tooltip_cancel();
            }, function() {
                window.revtree_mouseout();
            });
            url = widget.getAttributeNS("http://www.w3.org/1999/xlink", "href");

            var val = '<a ' + 'href="' + url + '"' + '>' + revision + '</a>';
            document.getElementById("tooltip_url").innerHTML = val;
            div.css("background-color", chgset.fillcolor());

            if (chgset._clause !== null) {
                document.getElementById("tooltip_clause").innerHTML = chgset._clause;
            } else {
                document.getElementById("tooltip_clause").innerHTML = "";
            }

            /* Tooltip */
            if (ww - right < 200) { /* TODO: use css max-wdth */
                x = ww - left - px;
                if ($.browser.opera || $.browser.safari) {
                    x = x + 17;
                }

                tooltip.css("left", '');
                tooltip.css("right", x + "px");
            } else {
                x = right + 17;
                tooltip.css("left", x + px + "px");
                tooltip.css("right", '');
            }

            if (wh - bottom < 100) { /* TODO: use css style definition */
                y = wh - bottom - py + (bottom - top) / 2 - 20;

                if (!($.browser.opera || $.browser.safari)) {
                    if ($(document).width() > $(window).width()) {
                        y = y - 15;
                    }
                }

                tooltip.css("top", '');
                tooltip.css("bottom", y + "px");
            } else {
                y = bottom - rect.height / 2 - 20;
                tooltip.css("bottom", '');
                tooltip.css("top", y + py + "px");
            }

            div = $("#tooltip");
            div.hover(function() {
                tooltip_cancel();
            }, function() {
                window.revtree_mouseout();
            });
            div.css("background-color", "#FFFFFF");
            div.css("border-color", chgset.strokecolor());

            /* Tool tip tittle */
            div = $("#tooltip_title");
            div.hover(function() {
                tooltip_cancel();
            }, function() {
                window.revtree_mouseout();
            });
            url = widget.getAttributeNS("http://www.w3.org/1999/xlink", "href");

            var val = '<a ' + 'href="' + url + '"' + '>' + revision + '</a>';
            document.getElementById("tooltip_url").innerHTML = val;
            div.css("background-color", chgset.fillcolor());

            var t = $("#tooltip").outerWidth()

            var logurl = "revtree/revtree_log/" + chgset._revision;
            $.ajax({
                async : true,
                type : "GET",
                dataType : 'text',
                url : logurl,
                success : loginfo_update
            });

            div = $("#tooltip_body");
            div.hover(function() {
                tooltip_cancel();
            }, function() {
                window.revtree_mouseout();
            });
            div.addClass("tooltip_waiting");

            var hellip = String.fromCharCode(8230);

            var t = document.getElementById('tooltip_body');
            t.innerHTML = '<span>loading changeset info ' + hellip + "</span>";
            t = null;

            $("#tooltip").removeClass("hidden");
            $("#tooltip_connect").removeClass("hidden");

            tooltip = null;
            div = null;
        }

        function tooltip_remove() {
            tooltip_cancel();

            $("#tooltip").addClass("hidden");
            $("#tooltip_connect").addClass("hidden");
        }

        function revtree_mouseout(event) {
            tooltip_cancel();
            tooltip_timer = setTimeout(tooltip_remove, 300);
        }

        window.revtree_mouseover = revtree_mouseover;
        window.revtree_mouseout = revtree_mouseout;

        function RevTreeUtils() {
            /* Compute character max width/height */
            var field = $("#metrics");

            /* font character width average between bigger and small caracter */
            field.text('M');
            this._cw = field.width();
            field.text('l');
            this._cw = this._cw + field.width();
            this._cw = this._cw / 2;

            /* font caracter height */
            this._ch = field.height();

            field = null;
        }
        ;

        RevTreeUtils.prototype.textheight = function() {
            return this._ch;
        };

        RevTreeUtils.prototype.textwidth = function(text) {
            if (typeof text == "undefined") {
                return 0;
            }

            return this._cw * text.length;
        };

        /* RevTree object */
        function RevTree(tree, url, style) {
            this._branches = new Array();
            this._oppoints = new Array();
            this._url = url;
            this._extent = [ 0, 0 ];
            this._makers = {};
            this._style = style;
            this.scale = 1;

            this.max_rev = tree.max_rev.toString()

            /* Publish RevTreeUtils object */
            window.RevTreeUtilsObj = new RevTreeUtils();

            this._changesets = new Array();
            this._revisions = [];
            this._maxchgextent = [ 0, 0 ]

            for ( var idx = 0, lg = tree.brc.length; idx < lg; idx++) {
                this._branches[idx] = new RevTreeBranch(this, tree.brc[idx],
                        this._style);

                this._maxchgextent[0] = Math.max(this._maxchgextent[0],
                        this._branches[idx]._maxchgextent[0]);

                this._maxchgextent[1] = Math.max(this._maxchgextent[1],
                        this._branches[idx]._maxchgextent[1]);

            }
        };

        RevTree.prototype.init = function() {
            setKeyboardHandler("#svgview");
        };

        RevTree.prototype.url = function() {
            return this._url;
        };

        RevTree.prototype.branches = function() {
            return this._branches;
        };

        RevTree.prototype.changeset_offset = function(revision) {
            return this._revisions[0] - revision;
        }

        RevTree.prototype.fixup_point = function(point) {
            var x, y, kx;
            var val, inc;

            x = point[0];
            y = point[1];

            kx = x;

            if (kx in this._oppoints) {
                val = 1;
                inc = 1;

                while (this._oppoints[kx].indexOf(y) != -1) {
                    y += val * (UNIT / 3);
                    val = -val + inc;
                    inc = -inc;
                }
            } else {
                this._oppoints[kx] = [];
            }

            this._oppoints[kx].push(y);

            return [ x, y ];
        };

        RevTree.prototype.xbranches = function(c1, c2) {
            var a1, a2, branches, br;

            a1 = c1.branch().vaxis();
            a2 = c2.branch().vaxis();

            branches = [];
            for ( var idx in this._branches) {
                br = this._branches[idx];

                if ((a1 < br.vaxis()) && (br.vaxis() < a2)) {
                    branches.push(br);
                }
            }

            return branches;
        };

        RevTree.prototype.extend = function() {
            return this._extent;
        }

        RevTree.prototype.build = function(scale) {
            var brc_xpos = UNIT;
            var max = this._branches.length;
            var idx = 0;
            var extent;
            var xy;

            this.scale = this.scale * scale;

            while (idx < max) {
                this._branches[idx].build(brc_xpos, UNIT);

                extent = this._branches[idx].extend()
                brc_xpos = brc_xpos + extent[0] + UNIT * 4;

                /* Update SVG tree extend */
                xy = this._branches[idx].get_slot(0)

                idx++;
                this._extent = [ brc_xpos * 0.6,
                        Math.max(xy[1] * 0.6, this._extent[1]) ];
            }
        };

        RevTree.prototype.add_changeset = function(chgset) {
            var revision = chgset.get_revision();

            this._changesets[revision] = chgset;
            this._revisions.push(revision);
            this._revisions.sort(function(a, b) {
                return b - a;
            });
        }

        RevTree.prototype.get_changeset = function(revision) {
            var chgset;

            chgset = this._changesets[revision];
            if (chgset === 'undefined')
                chgset = null;

            return chgset;
        }

        RevTree.prototype.get_arrow = function(head, color, renderer) {
            var id;

            if ([ head, color ] in this._makers) {
                return this._makers[[ head, color ]];
            }

            id = "arrow_" + (head ? "head" : "tail") + "_" + color;
            if (!head) {
                renderer.writeStartElement("svg:marker");
                renderer.writeAttributeString("id", id);
                renderer.writeAttributeString("refX", 7);
                renderer.writeAttributeString("refY", 3);
                renderer.writeAttributeString("markerWidth", 4.6);
                renderer.writeAttributeString("markerHeight", 5.6);
                renderer.writeAttributeString("orient", "auto");
                renderer.writeAttributeString("stroke", color);
                renderer.writeAttributeString("fill", color);
                renderer.writeAttributeString("viewBox", "0 0 6 6");

                renderer.writeStartElement("svg:path");
                renderer.writeAttributeString("d", "M0,0 L6,3 L0,6 L0,0");
                renderer.writeEndElement();
                renderer.writeEndElement();
            } else {
                renderer.writeStartElement("svg:marker");
                renderer.writeAttributeString("id", id);
                renderer.writeAttributeString("refX", -1);
                renderer.writeAttributeString("refY", 3);
                renderer.writeAttributeString("markerWidth", 4.6);
                renderer.writeAttributeString("markerHeight", 5.6);
                renderer.writeAttributeString("orient", "auto");
                renderer.writeAttributeString("stroke", color);
                renderer.writeAttributeString("fill", color);
                renderer.writeAttributeString("viewBox", "0 0 6 6");

                renderer.writeStartElement("svg:path");
                renderer.writeAttributeString("d", "M6,6 L0,3 L6,0 L6,6");
                renderer.writeEndElement();
                renderer.writeEndElement();
            }
            this._makers[[ head, color ]] = "url(#" + id + ")";

            return this._makers[[ head, color ]];
        }

        function abort_action_selector(event) {
            $("#svg").hide();

            $("[group]").css("opacity", "1");
            $("[group2]").css("opacity", "0.5");

            $("[changeset]").css("opacity", "1");

            /* Clear navigation changeset widget */
            $("#nav-changeset").hide();

            $("#svg").show();

            event.preventDefault();
            event.stopPropagation();
        };
        window.neorevtree.abort_action_selector = abort_action_selector;
        RevTree.prototype.abort_action_selector = abort_action_selector;

        RevTree.prototype.render = function(scale) {
            var layers = [ "layer1", "layer2", "layer3" ];
            var height = this._extent[1].toFixed(1);
            var width = this._extent[0].toFixed(1);

            this._makers = {};

            var renderer = new XMLWriter('UTF-8');
            renderer
                    .writeDocType(' PUBLIC "-//W3C//DTD XHTML 1.1 plus MathML 2.0 plus SVG 1.1//EN" "http://www.w3.org/2002/04/xhtml-math-svg/xhtml-math-svg.dtd"');
            renderer.writeStartDocument();
            renderer.writeStartElement('svg:svg');
            renderer
                    .writeAttributeString("xmlns:svg", "http://www.w3.org/2000/svg");
            renderer.writeAttributeString("version", "1.1");
            renderer.writeAttributeString("height", height);
            renderer.writeAttributeString("width", width);
            renderer.writeAttributeString("viewBox", "0 0 " + width + " " + height);
            renderer.writeAttributeString("id", "svgview");

            renderer.writeStartElement('svg:g');
            renderer.writeAttributeString("font-size", $("#metrics").css(
                    "font-size"));
            renderer.writeAttributeString("font-family", $("#metrics").css(
                    "font-family"));
            renderer.writeAttributeString("transform", "scale(0.6)");

            for ( var idx = 0; idx < layers.length; idx++) {
                for ( var brc = 0; brc < this._branches.length; brc++) {
                    renderer.writeStartElement('svg:g');
                    renderer.writeAttributeString("group",
                            this._branches[brc]._group);
                    this._branches[brc].render(renderer, layers[idx]);
                    renderer.writeEndElement();
                }
            }

            renderer.writeEndElement('svg:g');
            renderer.writeEndElement();
            renderer.writeEndDocument();

            var xmlDoc = (new DOMParser()).parseFromString(renderer.flush(),
                    'text/xml')

            $("#svg").hide()
            $("#svg").append(xmlDoc.documentElement);
            $("#svg").show()
        };

        /* Publish RevTree object */
        return RevTree;
    }
);
