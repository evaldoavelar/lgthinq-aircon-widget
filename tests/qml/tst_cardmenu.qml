import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import QtTest
import "../../plasmoid/contents/ui"

TestCase {
    name: "CardOptions"
    when: windowShown
    visible: true
    width: 440
    height: 360
    property int activations: 0
    CardMenu {
        id: menu
        x: 100
        y: 120
        QQC.MenuItem {
            id: first
            Layout.fillWidth: true
            text: "Configurar widget…"
            onTriggered: { activations += 1; menu.close() }
        }
        QQC.MenuItem {
            id: second
            Layout.fillWidth: true
            text: "Atualizar"
        }
        QQC.MenuItem {
            Layout.fillWidth: true
            text: "Credenciais protegidas pelo cofre"
            enabled: false
        }
    }
    function init() { menu.close(); activations = 0 }
    function test_click_activates_and_closes() {
        menu.open()
        verify(menu.visible)
        mouseClick(first)
        compare(activations, 1)
        verify(!menu.visible)
    }
    function test_keyboard_skips_disabled_and_escape_closes() {
        menu.open()
        tryCompare(first, "activeFocus", true)
        keyClick(Qt.Key_Down)
        tryCompare(second, "activeFocus", true)
        keyClick(Qt.Key_Down)
        tryCompare(first, "activeFocus", true)
        keyClick(Qt.Key_Escape)
        verify(!menu.visible)
    }
}
