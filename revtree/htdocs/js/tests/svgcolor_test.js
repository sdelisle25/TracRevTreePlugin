(function() {
    var svgcolor;

    module("SvgColor test cases", {
        setup: function () {
            svgcolor = new SvgColor()
        },
        teardown: function () {
            delete svgcolor;
        }
    });

    test("SvgColor: case no parameters in constructor, random color generation", function() {
        ok(svgcolor._color instanceof Array, "");
        ok(svgcolor._color.length == 3, "");
    });

    test("SvgColor: case no parameters in constructor, creation on 2 SvgColor object generated colors must be differents ", function() {
        var color = new SvgColor();
        ok(svgcolor._color != color._color, "");
    });
})();
