import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// Keep options in the card's scene; Plasma Dialog and Qt Popup use different origins.
QQC.Pane {
    id: menu
    default property alias entries: menuLayout.data
    visible: false
    z: 101
    padding: 4
    width: Math.min(implicitWidth, parent.width - 40)
    Accessible.role: Accessible.PopupMenu

    function open() {
        visible = true
        focusEntry(1, true)
    }
    function close() { visible = false }
    function focusEntry(direction, reset) {
        const items = menuLayout.children.filter(item => item.visible && item.enabled
            && typeof item.triggered === "function")
        if (!items.length) return
        const current = reset ? -1 : items.findIndex(item => item.activeFocus)
        items[(current + direction + items.length) % items.length].forceActiveFocus(Qt.TabFocusReason)
    }
    Keys.onEscapePressed: close()
    Keys.onDownPressed: focusEntry(1)
    Keys.onUpPressed: focusEntry(-1)

    background: Rectangle {
        radius: 8
        color: Kirigami.Theme.backgroundColor
        border.color: Qt.alpha(Kirigami.Theme.textColor, 0.25)
    }
    contentItem: ColumnLayout {
        id: menuLayout
        spacing: 0
    }
}
