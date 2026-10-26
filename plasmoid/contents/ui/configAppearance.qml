import QtQuick
import QtQuick.Controls as QQC
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: page
    property alias cfg_deviceLabel: labelField.text
    property string cfg_preferredUnit: "C"
    property alias cfg_showPanelTemperature: panelCheck.checked
    QQC.TextField {
        id: labelField
        Kirigami.FormData.label: i18n("Nome:")
        placeholderText: i18n("Ar-condicionado")
        maximumLength: 80
    }
    QQC.ComboBox {
        Kirigami.FormData.label: i18n("Unidade preferida:")
        model: ["C", "F"]
        currentIndex: page.cfg_preferredUnit === "F" ? 1 : 0
        onActivated: index => page.cfg_preferredUnit = index === 1 ? "F" : "C"
    }
    QQC.CheckBox { id: panelCheck; text: i18n("Mostrar temperatura na barra") }
    QQC.Label {
        text: i18n("A unidade só é usada se o aparelho a disponibilizar.")
        wrapMode: Text.WordWrap
    }
}
