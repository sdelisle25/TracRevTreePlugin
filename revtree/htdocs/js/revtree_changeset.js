"use strict";

define(['jquery', 'revtree_tag'],
    function ($, RevTreeTag) {
      var UNIT = 25.;

      /* RevTreeChangeSet object  */
      function RevTreeChangeSet(parent, revision, pos, head_rev) {
        this._revision = revision.rev;
        this._parent = parent;
        this._tags = null;
        this._src = null;
        this._lastrev = false;
        this._firstrev = false;
        this._position = null;
        this._brings = null;
        this._src = null;
        this._url = null;
        this._clause = null;
        this._head_rev = head_rev;

        this._fillcolor = this._parent.fillcolor();
        this._strokecolor = this._parent.strokecolor();
        this._textcolor = 'black';
        this._tags_extend = [0, 0];

        if (pos) {
          this._position = [pos[0], pos[1]];
        }

        if ('clause' in revision)
          this._clause = revision.clause;

        if ('firstrev' in revision)
          this._firstrev = true;

        /* Changeset source revision */
        if ('src' in revision)
          this._src = revision.src;

        if ('brings' in revision) {
          this._brings = revision.brings;
        }

        if ('delivers' in revision) {
          this._delivers = revision.delivers;
        }

        if ('lastrev' in revision) {
          this._lastrev = true;
        }

        this._tw = this._parent.tw;
        this._th = this._parent.th;

        this._w = this._tw;
        this._h = this._th;
        this.radius = this._w / 2 + UNIT / 3;

        /* Changeset extent */
        this._extent = [this.radius * 2, this.radius * 2];

        this._parent._update_extent(this._extent);

        /* Tag offset */
        this._tag_offset = null;

        /* Changeset url */
        this._url = this.url() + '/changeset/' + this._revision;

        /* Source revision */
        if ('src' in revision) {
          this._src = revision.src;
        }

        /* Tags */
        if ('tags' in revision) {
          var tags = revision.tags;

          this._tags = new Array();

          for (var idx in tags) {
            this._tags[idx] = new RevTreeTag(this, tags[idx]);
          }
        }
      };

      RevTreeChangeSet.prototype.url = function () {
        return this._parent.url();
      };

      RevTreeChangeSet.prototype.fillcolor = function () {
        return this._fillcolor;
      };

      RevTreeChangeSet.prototype.strokecolor = function () {
        return this._strokecolor;
      };

      RevTreeChangeSet.prototype.get_revision = function () {
        return this._revision;
      };

      RevTreeChangeSet.prototype.branch = function () {
        return this._parent;
      };

      RevTreeChangeSet.prototype.position = function (anchor) {
        var x, y;

        x = this._position[0];
        y = this._position[1];

        if (anchor.indexOf('s') != -1)
          y += this.radius;
        if (anchor.indexOf('e') != -1)
          x += this.radius;
        if (anchor.indexOf('n') != -1)
          y -= this.radius;
        if (anchor.indexOf('w') != -1)
          x -= this.radius;
        return [x, y];
      };

      RevTreeChangeSet.prototype.tag_offset = function (height) {
        var x, y;

        x = this._tag_offset[0];
        y = this._tag_offset[1];

        this._tag_offset[1] = y + height + UNIT / 3;

        return [x, y];
      };

      RevTreeChangeSet.prototype.extent_update = function (extent_x, extent_y) {
        var x, position;

        /* Parent position */
        position = this._parent.position();

        /* x axis */
        x = this._position[0] - position[0] + this.radius;
        if (this._extent[0] < x + extent_x)
          this._extent[0] = x + extent_x;

        /* y axis */
        if (this._extent[1] < extent_y) {
          this._extent[1] = extent_y;
        }
      };

      RevTreeChangeSet.prototype.update_tags_extend = function (extent) {
        /* x axis */
        if (this._tags_extend[0] < extent[0]) {
          this._tags_extend[0] = extent[0];
        }

        /* y axis */
        this._tags_extend[1] = this._tags_extend[1] + extent[1];
      }

      RevTreeChangeSet.prototype.build = function () {
        var x, extent, position;

        /* Changeset position */
        this._position = this._parent.get_slot(this._revision);

        /* Tag position */
        x = this._position[0] + (this.radius + UNIT / 3);
        this._tag_offset = [x, this._position[1] - this.radius];

        for (var idx in this._tags) {
          this._tags[idx].build();

          extent = this._tags[idx].extend();
          this.update_tags_extend(extent)
        }

        this.extent_update(this._tags_extend[0], this._tags_extend[1]);

        /* Rendering layers */
        this.layers = {
          'layer1': this.render_layer1,
          'layer2': this.render_layer2,
          'layer3': this.render_layer3
        };
      };

      RevTreeChangeSet.prototype.render = function (renderer, layer) {
        var render_func;

        render_func = this.layers[layer];
        if (render_func === 'undefined')
          return

        render_func.call(this, renderer);
      }

      RevTreeChangeSet.prototype.render_layer3 = function (renderer) {
        var position = this._position;
        var x, y;
        var xlink;
        var textcolor, fillcolor, strokecolor;
        var stroke_width;


        textcolor = this._textcolor;
        fillcolor = this._fillcolor;
        strokecolor = this._strokecolor;
        stroke_width = this._head_rev ? 5 : 3;

        x = this._position[0];
        y = this._position[1];

        if (this._lastrev) {
          textcolor = '#FFFFFF';
          fillcolor = '#000000';
        }

        if (this._firstrev) {
          textcolor = '#FFFFFF';
          fillcolor = this._strokecolor;
          strokecolor = this._fillcolor;
        }

        for (var idx in this._tags) {
          this._tags[idx].render(renderer);
        }

        renderer.writeStartElement('svg:a');
        renderer.writeAttributeString("xmlns:xlink", "http://www.w3.org/1999/xlink");
        renderer.writeAttributeString("xlink:href", this._url);
        renderer.writeAttributeString("onmouseover", "revtree_mouseover(this, " + this._revision.toString() + ")");
        renderer.writeAttributeString("onmouseout", "revtree_mouseout(this)");

        renderer.writeStartElement('svg:circle');
        renderer.writeAttributeString("changeset", this._revision.toString())
        renderer.writeAttributeString("fill", fillcolor);
        renderer.writeAttributeString("stroke", strokecolor);

        renderer.writeAttributeString("r", this.radius);

        renderer.writeAttributeString("cx", x);
        renderer.writeAttributeString("cy", y);
        renderer.writeAttributeString("stroke-width", stroke_width);

        renderer.writeEndElement();

        renderer.writeStartElement("svg:text");
        renderer.writeAttributeString("class", "changeset_text");
        renderer.writeAttributeString("text-anchor", "middle");
        renderer.writeAttributeString("x", x);
        renderer.writeAttributeString("y", y + this._th / 4);
        renderer.writeAttributeString("fill", textcolor);
        renderer.writeString(this._revision.toString());
        renderer.writeEndElement();
        renderer.writeEndElement();
      };

      RevTreeChangeSet.prototype.render_layer2 = function (renderer) {
        /* Source changeset */
        if (this._src) {
          this._parent.action(renderer, this._src, this._revision, '#5faf5f');
        }

        /* Render brings */
        if (this._brings) {
          this._parent.action(renderer, this._brings[0], this._revision, 'blue')
        }

        /* Render delivers */
        if (this._delivers) {
          this._parent.action(renderer, this._delivers[0], this._revision, 'orange')
        }
      };

      RevTreeChangeSet.prototype.render_layer1 = function (renderer) {
        /* Render brings */
        if (this._brings) {
          var pos1, pos2, chgset1, chgset2, width, height;

          chgset1 = this._parent.get_changeset(this._brings[0]);
          chgset2 = this._parent.get_changeset(this._brings[1]);

          pos1 = chgset1.position('');
          pos2 = chgset2.position('');

          width = chgset1.radius > chgset2.radius ? chgset1.radius : chgset2.radius;
          width = width * 2 + 30;
          height = pos2[1] - pos1[1] + width;

          renderer.writeStartElement('svg:rect');
          renderer.writeAttributeString("group2", chgset1._parent._group)
          renderer.writeAttributeString("group", chgset1._parent._group)
          renderer.writeAttributeString("fill", "#fffbdb")
          renderer.writeAttributeString("stroke", "#aaa161");
          renderer.writeAttributeString("stroke-width", 3);
          renderer.writeAttributeString("rx", 12);
          renderer.writeAttributeString("ry", 12);
          renderer.writeAttributeString("x", pos1[0] - width / 2);
          renderer.writeAttributeString("y", pos1[1] - width / 2 - 5)
          renderer.writeAttributeString("width", width);
          renderer.writeAttributeString("height", height + 10);
          renderer.writeAttributeString("opacity", 0.5);
          renderer.writeAttributeString("class", "index");
          renderer.writeAttributeString("z-index", "100");
          renderer.writeEndElement();
        }

        /* Render delivers */
        if (this._delivers) {
          var pos1, pos2, chgset1, chgset2, width, height;

          chgset1 = this._parent.get_changeset(this._delivers[0]);
          chgset2 = this._parent.get_changeset(this._delivers[1]);

          pos1 = chgset1.position('');
          pos2 = chgset2.position('');

          width = chgset1.radius > chgset2.radius ? chgset1.radius : chgset2.radius;
          width = width * 2 + 30;
          height = pos2[1] - pos1[1] + width;

          renderer.writeStartElement('svg:rect');
          renderer.writeAttributeString("group2", chgset1._parent._group)
          renderer.writeAttributeString("group", chgset1._parent._group)
          renderer.writeAttributeString("fill", "#fffbdb")
          renderer.writeAttributeString("stroke", "#aaa161");
          renderer.writeAttributeString("stroke-width", 3);
          renderer.writeAttributeString("rx", 12);
          renderer.writeAttributeString("ry", 12);
          renderer.writeAttributeString("x", pos1[0] - width / 2);
          renderer.writeAttributeString("y", pos1[1] - width / 2 - 5)
          renderer.writeAttributeString("width", width);
          renderer.writeAttributeString("height", height + 10);
          renderer.writeAttributeString("opacity", 0.5);
          renderer.writeEndElement();
        }
      };

      RevTreeChangeSet.prototype.extend = function () {
        return this._extent;
      };

      return RevTreeChangeSet;
  }
);