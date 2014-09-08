(function() {
  var UNIT = 25.;

  /* RevTreeBranchHeader object  */
  function RevTreeBranchHeader(parent, title, path, lastrev)
  {
    this._parent = parent;
    this._title = title;
    this._path = path;
    this._rev = lastrev;

    this._tw = RevTreeUtilsObj.textwidth(this._title);
    this._th = RevTreeUtilsObj.textheight();

    this._w = this._tw + UNIT;
    this._h = this._th + UNIT;

    this._recw = this._tw + UNIT;
    this._rech = this._th + UNIT;

    this._fillcolor = this._parent.fillcolor();
    this._strokecolor = this._parent.strokecolor(); // @@ SD this._fillcolor.darker(1.5); // TODO must be set in parent

    this._url = this.url() + '/browser/' + this._path + '?rev=' + lastrev
  };

  /* Publish RevTreeBranchHeader object*/
  window.RevTreeBranchHeader = RevTreeBranchHeader;

  RevTreeBranchHeader.prototype.url = function()
  {
    return this._parent.url();
  };

  RevTreeBranchHeader.prototype.extend = function()
  {
    return [this._recw, this._rech];
  };

  RevTreeBranchHeader.prototype.position = function(anchor)
  {
    var x, y;

    x = this._position[0];
    y = this._position[1];

    if(anchor.indexOf('s') != -1)
      y += this._rech;
      x += this._recw / 2;
    if(anchor.indexOf('e') != -1)
      x += this._recw;

    return [x, y];
  };

  RevTreeBranchHeader.prototype.build = function()
  {
    this._position = this._parent.position();
  };

  RevTreeBranchHeader.prototype.render = function(renderer)
  {
    var x, y;

    x = this._position[0];
    y = this._position[1];

    renderer.writeStartElement('svg:a');
    renderer.writeAttributeString("xmlns:xlink", "http://www.w3.org/1999/xlink");
    renderer.writeAttributeString("xlink:href", this._url);
      renderer.writeStartElement('svg:rect');
      renderer.writeAttributeString("fill", this._fillcolor)
      renderer.writeAttributeString("stroke", this._strokecolor);
      renderer.writeAttributeString("stroke-width", 3);
      renderer.writeAttributeString("rx", 12);
      renderer.writeAttributeString("ry", 12);
      renderer.writeAttributeString("x", x);
      renderer.writeAttributeString("y", y);
      renderer.writeAttributeString("width", this._recw);
      renderer.writeAttributeString("height", this._rech);
      renderer.writeEndElement();

      renderer.writeStartElement("svg:text");
      renderer.writeAttributeString("class", "changeset_text");
      renderer.writeAttributeString("x", x + this._recw / 2);
      renderer.writeAttributeString("y", y + this._rech / 2 + (14. / 2.5));
      renderer.writeAttributeString("text-anchor", "middle");
      renderer.writeString(this._title.toString());
      renderer.writeEndElement();
    renderer.writeEndElement()
  };
})();

