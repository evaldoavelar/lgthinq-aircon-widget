import QtQuick
import QtTest
import "../../plasmoid/contents/ui"

TestCase {
    name: "NeutralArt"
    when: windowShown
    visible: true
    width: 240; height: 160
    Rectangle { anchors.fill: parent; color: "#ff00ff" }
    PanelIcon { id: mark; foreground: "#ffffff" }
    IconGlyph { id: glyph; x: 100; ink: "#ffffff" }
    AirConditioner { id: decoration; x: 140; width: 80; height: 80 }

    function test_mark_scale_palette_and_transparency() {
        for (const size of [16, 24, 48]) {
            mark.width = size; mark.height = size
            for (const color of ["#ffffff", "#000000"]) {
                mark.foreground = color
                wait(40)
                const image = grabImage(mark)
                compare(image.pixel(Math.floor(size / 4), Math.floor(size * 5 / 24)), color)
                compare(image.pixel(0, 0), "#ff00ff")
                compare(image.pixel(Math.floor(size / 2), Math.floor(size / 2)), "#ff00ff")
            }
        }
    }
    function test_six_distinct_glyphs_and_repaint() {
        let signatures = []
        for (const kind of ["snow", "fan", "moon", "leaf", "power", "airflow"]) {
            glyph.kind = kind
            wait(40)
            let image = grabImage(glyph)
            let signature = ""
            for (let y = 0; y < 24; ++y)
                for (let x = 0; x < 24; ++x)
                    signature += String(image.pixel(x, y)) === "#ffffff" ? "1" : "0"
            verify(signature.indexOf("1") >= 0, kind + " must have visible ink")
            verify(signatures.indexOf(signature) < 0, kind + " must remain distinguishable")
            signatures.push(signature)
            compare(image.pixel(0, 0), "#ff00ff")
        }
        glyph.ink = "#000000"
        wait(40)
        compare(grabImage(glyph).pixel(5, 5), "#000000")
    }
    function test_decoration_tracks_confirmed_state_only() {
        const child = findChild(decoration, "neutralMark")
        verify(child !== null)
        decoration.powered = false
        compare(child.powered, false)
        decoration.powered = true
        compare(child.powered, true)
        verify(decoration.Accessible.ignored)
    }
}
