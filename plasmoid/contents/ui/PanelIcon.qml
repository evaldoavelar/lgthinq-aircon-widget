// Proposal from the documented five-block recipe, 2026-10-24; rights pending.
pragma ComponentBehavior: Bound
import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: mark
    property bool powered: false
    property color foreground: Kirigami.Theme.textColor
    implicitWidth: 24
    implicitHeight: 24
    readonly property var cells: [[4, 3], [4, 10], [4, 17], [15, 6], [15, 13]]
    Repeater {
        model: mark.cells
        delegate: Rectangle {
            required property var modelData
            x: modelData[0] * mark.width / 24
            y: modelData[1] * mark.height / 24
            width: 5 * mark.width / 24
            height: 4 * mark.height / 24
            color: mark.foreground
        }
    }
}
