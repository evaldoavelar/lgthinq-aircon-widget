import QtQuick
import QtTest
import "../../plasmoid/contents/ui"

TestCase {
    name: "PanelIconRendering"
    when: windowShown
    visible: true
    width: 40; height: 40
    Rectangle { width: 40; height: 40; color: "#ff00ff" }
    PanelIcon { id: icon; width: 24; height: 24; powered: true }
    function test_monochrome_theme_changes() {
        for (const foreground of ["#ffffff", "#000000"]) {
            icon.foreground = foreground
            wait(50)
            const picture = grabImage(icon)
            compare(picture.pixel(6, 5), foreground)
            compare(picture.pixel(0, 0), "#ff00ff")
            compare(picture.pixel(12, 8), "#ff00ff")
        }
    }
}
