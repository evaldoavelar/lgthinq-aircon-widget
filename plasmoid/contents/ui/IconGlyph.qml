// Six abstract primitive recipes, 2026-10-24. Legacy kind keys are API aliases;
// these drawings do not depict snow, fan blades, a moon, a leaf or an appliance.
// No icon-library paths were imported. Proposal only; rights review pending.
pragma ComponentBehavior: Bound
import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: glyph
    property string kind: "snow"
    property color ink: Kirigami.Theme.textColor
    implicitWidth: 24
    implicitHeight: 24
    // Each entry is x, y, width, height, corner radius on a 24-unit grid.
    readonly property var primitives: {
        switch (kind) {
        case "snow": return [[4,4,6,6,0], [14,4,6,6,0], [4,14,6,6,0], [14,14,6,6,0]]
        case "fan": return [[4,13,3,7,0], [10,8,3,12,0], [16,3,3,17,0]]
        case "moon": return [[4,4,4,4,2], [4,12,16,2,0], [4,18,10,2,0]]
        case "leaf": return [[4,16,4,4,2], [10,10,4,4,2], [16,4,4,4,2]]
        case "power": return [[8,8,8,8,0], [2,10,2,4,0], [20,10,2,4,0]]
        default: return [[3,4,18,3,0], [3,10,13,3,0], [3,16,8,3,0]]
        }
    }
    Repeater {
        model: glyph.primitives
        delegate: Rectangle {
            required property var modelData
            x: modelData[0] * glyph.width / 24
            y: modelData[1] * glyph.height / 24
            width: modelData[2] * glyph.width / 24
            height: modelData[3] * glyph.height / 24
            radius: modelData[4] * Math.min(glyph.width, glyph.height) / 24
            color: glyph.ink
        }
    }
}
