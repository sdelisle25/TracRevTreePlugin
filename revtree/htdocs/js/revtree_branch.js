/**
  RevTree branch module
  @file revtree_branch.js
  @author Neotion (c) 2014-2015
 */

"use strict";

define(['jquery', 'revtree_changeset', 'revtree_color', 'revtree_branchheader', 'revtreeutils'],
    function($, RevTreeChangeSet, RevTreeColor,
             RevTreeBranchHeader, revtreeutils) {
      var UNIT = 25.;

      /**: RevTreeBranch(parent, branch, style)
       Object prototype to create revision tree branch.

       :param parent: branch parent obejct
       :param branch: information for branch creation
       :param style: branch style
       */
      function RevTreeBranch(parent, branch, style)
      {
        var idx, chgset, color;

        this._parent = parent;
        this._name = branch.name;
        this._path = branch.path;
        this._revisions = branch.revisions;
        this._extent = [0, 0];
        this._first_chgset = null;
        this._lastrev = branch.lastrev;
        this._style = style;
        this._group = branch.name

        color = this._get_color(this._name);

        this._fillcolor = color.rgb();
        this._strokecolor = color.darker(1.5).rgb();

        /* Max revision text size */
        this.tw = revtreeutils.textwidth(this._parent.max_rev);
        this.th = revtreeutils.textheight();

        this.chgset_diam = (this.tw / 2 + UNIT / 3) * 2;

        this._maxchgextent = [this.chgset_diam, this.chgset_diam];

        /* Position */
        this._position = null;

        /* slot position for changesets */
        this._slot_position = null;

        this._changesets = new Array();

        /* Branch header */
        this._branch_header = new RevTreeBranchHeader(this,
                                                      this._name,
                                                      this._path,
                                                      this._revisions[0].rev);

        /* Changesets */
        var head_rev;
        for(var idx=0, lg=this._revisions.length; idx < lg; idx++) {
          head_rev = false;
          if((idx == 0) && (this._lastrev)) {
            head_rev = true;
          }

          chgset = new RevTreeChangeSet(this,
                                        this._revisions[idx],
                                        null,
                                        head_rev);

          if(this._first_chgset == null) {
            this._first_chgset = chgset;
          }

          this._changesets.push(chgset);

          this._parent.add_changeset(chgset);
        }
      };

      RevTreeBranch.prototype.url = function()
      {
        return this._parent.url();
      };

      RevTreeBranch.prototype.changesets = function()
      {
        return this._changesets;
      };

      RevTreeBranch.prototype.header = function()
      {
        return this._branch_header;
      };

      RevTreeBranch.prototype.get_changeset = function(revision)
      {
        return this._parent.get_changeset(revision);
      };

      RevTreeBranch.prototype.branch = function()
      {
        return this._parent;
      };

      RevTreeBranch.prototype.build = function(xpos, ypos)
      {
        var h, w, x, y, extent, position;
        this._position = [xpos, ypos];

        // Build branch header
        this._branch_header.build();
        extent = this._branch_header.extend();

        /* Update branch extend */
        this._update_extent([extent[0], this.chgset_diam]);

        /* Init slot position generator */
        x = this._position[0] + extent[0] / 2;
        y = this._position[1] + 2 * this._maxchgextent[1];
        this._slot_position = [x, y];

        for (var idx=0, lg=this._changesets.length; idx < lg; idx++) {
          this._changesets[idx].build();

          extent = this._changesets[idx].extend();

          /* Update branch extend */
          this._update_extent(extent);
        }

        this.layers = {'layer1': this.render_layer1,
                       'layer2': this.render_layer2,
                       'layer3': this.render_layer3};
      };

      RevTreeBranch.prototype._update_extent = function(extent)
      {
        if(this._maxchgextent[0] < extent[0]) {
          this._maxchgextent[0] = extent[0];
        }

        /* REMARK: specific case max changeset extent */
        if(this._maxchgextent[1] < extent[1]) {

          if(extent[1] - this._maxchgextent[1] > this.chgset_diam/2) {
            var factor = Math.ceil(extent[1] / (this.chgset_diam * 3));
            this._maxchgextent[1] = this.chgset_diam * (factor + 1);
          }
          else {
            this._maxchgextent[1] = this.chgset_diam;
          }
        }
        else {
          this._maxchgextent[1] = this.chgset_diam;
        }

        /* x axis */
        if(this._extent[0] < extent[0])
          this._extent[0] = extent[0];

        /* y axis */
        this._extent[1] = this._extent[1] + extent[1];
      };

      RevTreeBranch.prototype.extend = function()
      {
        return this._extent;
      };

      RevTreeBranch.prototype.get_chgset = function(revision)
      {
        var chgset = null;

        for(var idx in this._changesets) {
            if(this._changesets[idx].get_revision() == revision) {
              chgset = this._changesets[idx];
              break;
            }
        }
        return chgset;
      };

      RevTreeBranch.prototype.get_slot = function(revision)
      {
        var x, y, maxextent;
        var scale = 3 * this._parent.scale;

        /* Compute next position for changeset */
        x = this._slot_position[0];

        if(this._style == 'compact') {
            this._slot_position[1] = this._slot_position[1] + scale * this._maxchgextent[1];

            y = this._slot_position[1];
        }
        else {
          maxextent = this._parent._maxchgextent[1];
          maxextent = this.chgset_diam;

          if(revision == 0) {
            y = this._slot_position[1] + scale * maxextent;
          }
          else {
            y = this._parent.changeset_offset(revision);
            y = (y + 2) * scale * maxextent;
          }

          this._slot_position[1] = y;
        }

        return [x, y];
      };

      RevTreeBranch.prototype.render = function(renderer, layer)
      {
        var render_func;

        render_func = this.layers[layer];
        if(render_func === 'undefined')
            return

        render_func.call(this, renderer, layer);
      };

      RevTreeBranch.prototype.render_layer1 = function(renderer)
      {
        var idx, lg;

        /* Render groups */
        for(idx=0, lg=this._changesets.length; idx < lg; idx++) {
          /* Draw connection line */
          this._changesets[idx].render(renderer, "layer1");
        }
      };

      RevTreeBranch.prototype.render_layer2 = function(renderer)
      {
        var idx, lg;

        /* Render changesets */
        for(idx=0, lg=this._changesets.length; idx < lg; idx++) {
          /* Draw connection line */
          this._changesets[idx].render(renderer, "layer2");
        }

        /* Render branch header */
        this._branch_header.render(renderer);
      };

      String.prototype.format = function() {
        var f = this;

        for (var i in arguments) {
            f = f.replace('{'+i+'}', arguments[i]);
        }
        return f;
      }

      RevTreeBranch.prototype.render_layer3 = function(renderer)
      {
        var x, y, x1, y1, xl, yl, position;
        var idx, lg;

        /* Render changesets */
        for(idx=0, lg=this._changesets.length; idx < lg; idx++) {
          this._changesets[idx].render(renderer, "layer3");
        }

        x = this._position[0]; y = this._position[1];

        /* Init default values */
        xl = 0; yl = 0;

        /* Render changesets */
        for(idx=0, lg=this._changesets.length; idx < lg; idx++) {
          if (xl && yl) {
            var marker_end = this._parent.get_arrow(false, "gray", renderer);

            position = this._changesets[idx].position('n');
            renderer.writeStartElement("svg:line");
            renderer.writeAttributeString("stroke", "gray");
            renderer.writeAttributeString("stroke-width", 3);
            renderer.writeAttributeString("marker-end", marker_end);
            renderer.writeAttributeString("x2", xl);

            renderer.writeAttributeString("y2", yl);
            renderer.writeAttributeString("x1", position[0]);
            renderer.writeAttributeString("y1", position[1] - 1);
            renderer.writeEndElement();
          }
          position = this._changesets[idx].position('s');

          xl = position[0];
          yl = position[1] + 1;
        }

        /* Draw axis between header and changeset */
        position = this._branch_header.position('s');
        xl = position[0];
        yl = position[1];

        position = this._first_chgset.position('n');
        renderer.writeStartElement("svg:line");
        renderer.writeAttributeString("stroke", "gray");
        renderer.writeAttributeString("stroke-width", 3);
        renderer.writeAttributeString("stroke-dasharray", "4, 4");
        renderer.writeAttributeString("x2", xl);
        renderer.writeAttributeString("y2", yl + 1);
        renderer.writeAttributeString("x1", position[0]);
        renderer.writeAttributeString("y1", position[1] - 1);
        renderer.writeEndElement();

        /* Display arrow to indicates that more recent revisions exist */
        if(this._lastrev == false) {
            var pos, x, y;
            var points = '{0},{1} {2},{3} {4},{5}';

            pos = position = this._branch_header.position('s');
            x = pos[0];
            y = pos[1] + 10;

            renderer.writeStartElement("svg:g");
            renderer.writeAttributeString("stroke", "#E80000");
            renderer.writeAttributeString("fill", "#E80000");

            renderer.writeStartElement("svg:line");
            renderer.writeAttributeString("stroke", "white");
            renderer.writeAttributeString("stroke-width", 4);
            renderer.writeAttributeString("x2", x);
            renderer.writeAttributeString("y2", y + 40);
            renderer.writeAttributeString("x1", x);
            renderer.writeAttributeString("y1", y - 3);
            renderer.writeEndElement();

              renderer.writeStartElement("svg:polygon");

              renderer.writeAttributeString("points", points.format(x, y, x - 8, y + 15, x + 8, y + 15));
              renderer.writeEndElement();

              y = y + 20
              renderer.writeStartElement("svg:polygon");

              renderer.writeAttributeString("points", points.format(x, y, x - 8, y + 15, x + 8, y + 15));

              renderer.writeStartElement("svg:polygon");
              renderer.writeEndElement();

              renderer.writeEndElement();
            renderer.writeEndElement();
        }
      };

      RevTreeBranch.prototype._get_color = function(name, trunks)
      {
        if(name == "trunk") {
          return new RevTreeColor(null, "#cdc9c9"); /* REMARK: ol value #8eb8e2 */
        }

        return new RevTreeColor(name);
      };

      RevTreeBranch.prototype.fillcolor = function()
      {
        return this._fillcolor;
      };

      RevTreeBranch.prototype.strokecolor = function()
      {
        return this._strokecolor;
      };

      RevTreeBranch.prototype.position = function()
      {
        return this._position;
      };

      RevTreeBranch.prototype.vaxis = function()
      {
        return this._branch_header.position('s')[0];
      };

      RevTreeBranch.prototype.move = function(x, y)
      {
        return ' M ' + x.toString() + ' ' + y.toString();
      };

      RevTreeBranch.prototype.line = function(x, y)
      {
        return ' L ' + x.toString() + ' ' + y.toString();
      };

      RevTreeBranch.prototype.qbezier = function(x1, y1, x, y)
      {
        return 'Q' + x1.toString() + ',' + y1.toString() + ' ' + x.toString() + ',' + y.toString();
      };

      RevTreeBranch.prototype.action = function(renderer, source_rev, dest_rev, color)
      {
        var pos, xs, ys, xe, ye;
        var tmp;
        var ps, pe, ss, se;
        var xbranches, head;
        var points, pc;
        var head = false;
        var source, dest;

        points = [];

        source = this._parent.get_changeset(source_rev);
        if(source == null)
            return
        dest = this._parent.get_changeset(dest_rev);
        if(source == null)
            return

        if(source.branch() == dest.branch()) {
          return;
        }

        /* Get the position of the changeset to tie */
        pos = source.position('');
        xs = pos[0]; ys = pos[1];

        pos = dest.position('');
        xe = pos[0]; ye = pos[1];

        /* Swap start and end points so that xs < xe */
        if (xs > xe) {
          head = true;
          tmp = source;
          source = dest;
          dest = tmp;
          pos = source.position('');
          xs = pos[0]; ys = pos[1];

          pos = dest.position('');
          xe = pos[0]; ye = pos[1];
        }
        else {
          head = false;
        }

        /* Branches between source and destination changesets */
        xbranches = this._parent.xbranches(source, dest);

        /* find which points on the changeset widget are used for connections */
        if(xs < xe) {
          ss = 'e';
          se = 'w';
        }
        else {
          ss = 'w';
          se = 'e';
        }
        ps = source.position(ss);
        pe = dest.position(se);

        /* Compute the straight line from start to end widgets */
        var a, b, c, xct, yct, br, x, y;
        var ycu, ycd;

        a = (ye - ys) / (xe - xs);
        b = ys - (a * xs);

        /* compute the points through which the 'operation' curve should go */
        xct = ps[0]; yct = ps[1];

        var hpos, hchg, pc, schangesets, yc;

        if(head) {
          points = [[xct + UNIT, yct]];
        }
        else {
          points = [[xct, yct]];
        }

        for(var idx in xbranches) {
            br = xbranches[idx];
            x = br.vaxis();

            y = (a * x) + b;
            ycu = ycd = null;
            tmp = br.changesets();
            schangesets = [];

            for(var idx in tmp) {
              schangesets[idx] = tmp[idx];
            }

            /* add an invisible changeset in place of the branch header to avoid special case for the first changeset */
            hpos = br.header().position('');

            hchg = new RevTreeChangeSet(br,
                                        {'rev': 0},
                                        [hpos[0], hpos[1] + 3 * this._parent.scale * this.chgset_diam],
                                        false);
            schangesets.unshift(hchg);

            pc = null;
            for(var idx in schangesets) {
              c = schangesets[idx];
              /* find the changesets which are right above and under the selected point, and store their vertical position */
              yc = c.position('')[1];
              if(yc < y) {
                ycu = yc;
              }
              if(yc >= y) {
                ycd = yc;
                if(!ycu) {
                   if(pc) {
                     ycu = pc.position('')[1];
                   }
                   else {
                     var last;

                     last = schangesets.slice(-1)[0];
                     if(c != last) {
                       ycu = last.position('')[1];
                     }
                   }
                }
                break;
              }
              pc = c;
           }
           var xt, yt, a2, b2, xl, yl;

           var nx, ny;
           var dist, radius, add_point;

            if ((!ycu) || (!ycd)) {
            /* In this case, we need to create a virtual point (TODO) */
            }
            else {
              xt = x;
              yt = (ycu + ycd) / 2;
              if(a != 0) {
                a2 = -1 / a;
                b2 = yt - a2 * xt;
                xl = (b2 - b) / (a - a2);
                yl = a2 * xl + b2;

                nx = xt - xl;
                ny = yt - yl;

                dist = Math.sqrt(nx * nx + ny * ny);

                radius = (3 * c.radius) / 2;

                add_point = (dist < radius)?true:false;
              }
              else {
                add_point = true;
              }

              /* Do not insert a point if the ideal curve is far enough from
              an existing changeset */
              if(add_point) {
                  /* update the vertical position for the bezier control
                  point with the point that stands between both closest
                  changesets */

                tmp = this._parent.fixup_point([xt, yt]);
                points.push(tmp);
              }
            }
          }

        if(head) {
          points.push(pe);
        }
        else {
          points.push([pe[0] - UNIT, pe[1]]);
        }

        /* Compute the qbezier curve */
        var d;
        if(head) {
          d = this.move(ps[0], ps[1]);
          d = d + this.line(points[0][0], points[0][1]);
        }
        else {
          d = this.move(points[0][0], points[0][1]);
        }

        var lg = points.length - 1;
        for(var i = 0; i < lg; i++) {
          var xl, yl, yr, xr, xi, yi;

          xl = points[i][0]; yl = points[i][1];
          xr = points[i + 1][0]; yr = points[i + 1][1];
          xi = (xl + xr) / 2;
          yi = (yl + yr) / 2;

          d = d + this.qbezier(xl + 2 * UNIT, yl, xi, yi);
          d = d + this.qbezier(xr - 2 * UNIT, yr, xr, yr);
        }

        if(!head) {
          d = d + this.line(pe[0], pe[1]);
        }

        color = color != 'undifined'?color:'red';
        var arrow = this._parent.get_arrow(head, color, renderer);

        renderer.writeStartElement('svg:g');
        renderer.writeAttributeString("group", 'arrow');
        renderer.writeAttributeString("changesets", "" + source_rev + "," + dest_rev);
//        renderer.writeAttributeString("onclick", "window.action_selector(evt, this, "
//                                      + source_rev  + "," + dest_rev + ")");

        renderer.writeStartElement('svg:path');
        renderer.writeAttributeString("fill", 'none');
        renderer.writeAttributeString("stroke", color);
        renderer.writeAttributeString("stroke-width", 4);
        renderer.writeAttributeString("marker-" + (head?'start':'end'), arrow)
        renderer.writeAttributeString("d", d);
        renderer.writeEndElement();
        renderer.writeEndElement();

        /* Test */
        renderer.writeStartElement('svg:g');
        renderer.writeAttributeString("group", 'arrow');
        renderer.writeAttributeString("onclick", "window.action_selector(evt, this, "
                                      + source_rev  + "," + dest_rev + ")");

        renderer.writeStartElement('svg:path');
        renderer.writeAttributeString("fill", 'none');
        renderer.writeAttributeString("stroke", color);
        renderer.writeAttributeString("stroke-width", 20);
        renderer.writeAttributeString("stroke-opacity", 0);
        renderer.writeAttributeString("d", d);
        renderer.writeEndElement();
        renderer.writeEndElement();
      }

      window.action_selector = function(event, widget, src_rev, dest_rev) {
          var src, dest;
          var src_grp, dest_grp;
          var tmp;

          /* Prevent default handler, and stop propagation */
          event.preventDefault();
          event.stopPropagation();

          src = window.revtree.get_changeset(src_rev);
          dest = window.revtree.get_changeset(dest_rev);
          if((src == null) || (dest == null))return

          $("#info_esc").addClass("indicator-esc-show");

          $("#svg").hide();

          $("[group]").css("opacity", "0.3");

          $("[group='arrow']").css("opacity", "1");
          $("[group2]").css("opacity", "0.5");

          src_grp = "[group='";
          src_grp += src._parent._group;
          src_grp += "']";

          dest_grp = "[group='";
          dest_grp += dest._parent._group;
          dest_grp += "']";

          window.neorevtree.src_rev = src_rev;
          window.neorevtree.dest_rev = dest_rev;

          $(src_grp).css("opacity", "1");
          $(dest_grp).css("opacity", "1");

          $(src_grp + "> [group='arrow']").css("opacity", "0.3");
          $(dest_grp + "> [group='arrow']").css("opacity", "0.3");

          $(src_grp + "> [group2]").css("opacity", "0.15");
          $(dest_grp + "> [group2]").css("opacity", "0.15");

          $("[changesets='" + src_rev + "," + dest_rev + "']").css("opacity", "1");

          tmp = src_grp + "[group2='" + src._parent._group + "']";
          $(tmp).css("opacity", "0.5");

          tmp = dest_grp + "[group2='" + dest._parent._group + "']";
          $(tmp).css("opacity", "0.5");

          /* Display navigation changeset widget */
          $("#nav-changeset").show();

          $("#svg").show();

          return false;
      };

      return RevTreeBranch;
    }
);