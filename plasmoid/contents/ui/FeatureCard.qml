// Neutral feature row for the review candidate; functional API retained.
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC
import org.kde.kirigami as Kirigami

QQC.AbstractButton {
    id: card
    property string heading: ""
    property string valueText: i18n("Indisponível")
    property string iconName: "configure"
    property bool actionable: false
    property bool active: false
    implicitWidth: 240
    implicitHeight: 48
    hoverEnabled: actionable
    activeFocusOnTab: actionable
    Accessible.name: i18nc("Feature name and value", "%1: %2", heading, valueText)
    Accessible.description: actionable ? i18n("Selecionar opção") : i18n("Somente leitura")
    background: Rectangle {
        color: card.down && card.actionable ? Qt.alpha(Kirigami.Theme.textColor, 0.12)
            : card.hovered && card.actionable ? Qt.alpha(Kirigami.Theme.textColor, 0.06)
            : "transparent"
        border.width: card.activeFocus ? 1 : 0
        border.color: Kirigami.Theme.focusColor
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: Qt.alpha(Kirigami.Theme.textColor, 0.15)
        }
    }
    contentItem: RowLayout {
        spacing: 12
        IconGlyph {
            kind: card.iconName
            implicitWidth: 20
            implicitHeight: 20
            ink: card.active ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
        }
        QQC.Label { text: card.heading; Layout.fillWidth: true; elide: Text.ElideRight }
        QQC.Label { text: card.valueText; Layout.maximumWidth: card.width / 2; elide: Text.ElideRight }
        QQC.Label { text: "›"; visible: card.actionable; Accessible.ignored: true }
    }
    padding: 8
}
