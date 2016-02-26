"use strict";

define(['jquery'],
    function($) {
      /*

      # HSV: Hue, Saturation, Value
      # H: position in the spectrum
      # S: color saturation ("purity")
      # V: color brightness
      */

      var colormap = {'black':     [0, 0, 0],
                      'white':     [0xff, 0xff, 0xff],
                      'darkred':   [0x7f, 0, 0],
                      'darkgreen': [0, 0x7f, 0],
                      'darkblue':  [0, 0, 0x7f],
                      'red':       [0xdf, 0, 0],
                      'green':     [0, 0xdf, 0],
                      'blue':      [0, 0, 0xdf],
                      'gray':      [0x7f, 0x7f, 0x7f],
                      'orange':    [0xff, 0x9f, 0]};

      /* RevTreeColor object */
      function RevTreeColor(name, value)
      {
        if(typeof value != "undefined") {
          if(value instanceof RevTreeColor)
            this._color = value._color;
          else if(value instanceof Array)
            this._color = value;
          else
            this._color = this.str2col(value);
        } else {
          if(typeof name != "undefined")
            this._color = this.from_name(name);
          else
            this._color = this.random();
        }
      };

      RevTreeColor.prototype.rgb = function()
      {
        return "rgb(" + this._color[0] + "," + this._color[1] + "," +
                    this._color[2] + ")";
      };

      RevTreeColor.prototype.darker = function(k) {
        k = Math.pow(.7, arguments.length ? k : 1);
        return new RevTreeColor(null, [~~(k * this._color[0]),
                                       ~~(k * this._color[1]),
                                       ~~(k * this._color[2])]);
      };

      RevTreeColor.prototype.set = function(string)
      {
        this._color = this.str2col(string);
      };

      RevTreeColor.prototype.str2col = function(string)
      {
        if(string.charAt(0) == "#") {
          var r, g, b;
          var rgb = string.substring(1);

          if(rgb.length == 6) {
            r = parseInt(rgb.substring(0, 2), 16);
            g = parseInt(rgb.substring(2, 4), 16);
            b = parseInt(rgb.substring(4, 6), 16);

            return [r, g, b];
          }
          else {
            if(rgb.length == 3) {
              r = int(rgb.substring(0, 1), 16) * 16;
              g = int(rgb.substring(1, 2), 16) * 16;
              b = int(rgb.substring(2, 3), 16) * 16;

              return [r, g, b];
            }
          }
        }

        return colormap[string]
      };

      RevTreeColor.prototype.random = function()
      {
        var rand = Math.floor(Math.random() * 1000);
        var str_rand = rand.toString();

        if(str_rand.length < 3)
          str_rand = '0' + str_rand;

        return [128 + 14 * parseInt(str_rand.charAt(0)),
                128 + 14 * parseInt(str_rand.charAt(1)),
                128 + 14 * parseInt(str_rand.charAt(2))];
      };

      RevTreeColor.prototype.from_name = function(name)
      {
        var digest = $.md5(name);

        var vr = 14 * (digest.charCodeAt(0) % 10);
        var vg = 14 * (digest.charCodeAt(1) % 10);
        var vb = 14 * (digest.charCodeAt(2) % 10);

        digest = null;

        return [128 + vr, 128 + vg, 128 + vb];
      };

      RevTreeColor.prototype.invert = function()
      {
        this._color = [0xff - this._color[0],
                       0xff - this._color[1],
                       0xff - this._color[2]];
      };

      return RevTreeColor;
    }
);
