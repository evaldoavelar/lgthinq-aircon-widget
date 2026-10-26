// Legacy component name retained for callers. This is an abstract decoration,
// not a depiction of a device or a set of measurements. Rights review pending.
pragma ComponentBehavior: Bound
import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: decoration
    property bool powered: false
    implicitWidth: 96
    implicitHeight: 96
    Accessible.ignored: true
    PanelIcon {
        objectName: "neutralMark"
        anchors.centerIn: parent
        width: Math.min(decoration.width, decoration.height)
        height: width
        powered: decoration.powered
        foreground: decoration.powered ? Kirigami.Theme.highlightColor
                                      : Kirigami.Theme.disabledTextColor
    }
}
