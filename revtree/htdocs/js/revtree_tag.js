(function() {
  var UNIT = 25.;

  /* RevTreeTag class  */
  var RevTreeTag = function(parent, name)
  {
    this._name = name;
    this._parent = parent;

    /* Colors */
    this._fillcolor = this._parent.fillcolor();
    this._strokecolor = this._parent.strokecolor(); // @@ this._fillcolor.darker(1.5);
    this._textcolor = 1;

    /* Changeset extent */
    this._htw = RevTreeUtilsObj.textwidth(this._name);

    this._tw = this._htw;
    this._th = RevTreeUtilsObj.textheight();

    this._w = this._tw + UNIT;
    this._h = this._th + UNIT / 4;

    this._extent = [this._w, this._h];

    this._url = parent._url;

  };

  /* Publish RevTreeTag object */
  window.RevTreeTag = RevTreeTag;

  RevTreeTag.prototype.build = function()
  {
    this._position = this._parent.tag_offset(this._h)
  }

  RevTreeTag.prototype.render = function(renderer)
  {
    var x, y;

    x = this._position[0];
    y = this._position[1];

    renderer.writeStartElement('svg:a');
    renderer.writeAttributeString("xmlns:xlink", "http://www.w3.org/1999/xlink");
    renderer.writeAttributeString("xlink:href", this._url);
    renderer.writeAttributeString("onmouseover", "revtree_mouseover(this, " + this._parent._revision.toString() + ")");
    renderer.writeAttributeString("onmouseout", "revtree_mouseout(this)");

      renderer.writeStartElement('svg:rect');
      renderer.writeAttributeString("fill", this._fillcolor)
      renderer.writeAttributeString("stroke", this._strokecolor);
      renderer.writeAttributeString("stroke-width", 3);
      renderer.writeAttributeString("rx", 12);
      renderer.writeAttributeString("ry", 12);
      renderer.writeAttributeString("x", x);
      renderer.writeAttributeString("y", y);
      renderer.writeAttributeString("width", this._w);
      renderer.writeAttributeString("height", this._h);
      renderer.writeEndElement();

      renderer.writeStartElement("svg:text");
      renderer.writeAttributeString("class", "changeset_text");
      renderer.writeAttributeString("x", x + this._w / 2);
      renderer.writeAttributeString("y",  y + this._h / 2 + this._th / 4);
      renderer.writeAttributeString("text-anchor", "middle");
      renderer.writeString(this._name.toString());
      renderer.writeEndElement();
    renderer.writeEndElement()
  }

  RevTreeTag.prototype.extend = function()
  {
    return this._extent;
  }

  RevTreeTag.prototype.position = function()
  {
    return this._position;
  }
})();
