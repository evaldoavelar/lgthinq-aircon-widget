import QtQuick
import QtTest
import "../../plasmoid/contents/ui"

TestCase {
    name: "TemperatureSelection"
    when: windowShown
    width: 180; height: 80
    TemperatureEditor {
        id: editor
        confirmedValue: 22
        revision: 1
        capability: ({minimum: 18, maximum: 30, step: 0.5})
        capabilityKey: "temperature.targetTemperature.C"
        enabled: true
        canSubmit: true
    }
    SignalSpy { id: sent; target: editor; signalName: "requested" }
    function init() {
        editor.cancel()
        editor.confirmedValue = 22
        editor.revision = 1
        editor.capabilityKey = "temperature.targetTemperature.C"
        editor.enabled = true
        editor.canSubmit = true
        sent.clear()
    }
    function test_rapid_clicks_coalesce_and_show_preview() {
        for (let i = 0; i < 6; ++i) {
            editor.adjust(1)
            wait(50)
        }
        compare(editor.displayValue, 25)
        compare(editor.confirmedValue, 22)
        compare(sent.count, 0)
        wait(450)
        compare(sent.count, 0)
        tryCompare(sent, "count", 1, 1000)
        compare(sent.signalArguments[0][0], 25)
        editor.acknowledge(true)
        editor.observe("connected", null, 1)
        verify(editor.hasDraft, "Old cache must not acknowledge the command")
        editor.confirmedValue = 25
        editor.observe("connected", null, 2)
        verify(!editor.hasDraft)
    }
    function test_drag_shows_value_without_sending_until_release() {
        editor.beginDrag()
        editor.select(26.5)
        compare(editor.displayValue, 26.5)
        wait(800)
        compare(sent.count, 0)
        editor.endDrag()
        tryCompare(sent, "count", 1, 1500)
        compare(sent.signalArguments[0][0], 26.5)
    }
    function test_busy_and_new_edits_preserve_latest_intent() {
        editor.select(24)
        tryCompare(sent, "count", 1, 1500)
        editor.acknowledge(true)
        editor.canSubmit = false
        editor.select(25)
        wait(800)
        compare(sent.count, 1)
        editor.confirmedValue = 24
        editor.revision = 2
        editor.observe("connected", null, 2)
        editor.canSubmit = true
        tryCompare(sent, "count", 2, 500)
        compare(sent.signalArguments[1][0], 25)
    }
    function test_returning_to_confirmed_value_sends_nothing() {
        editor.adjust(1)
        editor.adjust(-1)
        wait(800)
        compare(sent.count, 0)
        verify(!editor.hasDraft)
    }
    function test_failure_and_disconnect_cancel_draft() {
        editor.select(24)
        editor.observe("error", "network_error", 1)
        compare(editor.displayValue, 22)
        wait(800)
        compare(sent.count, 0)
        editor.select(25)
        editor.enabled = false
        wait(800)
        compare(sent.count, 0)
        compare(editor.displayValue, 22)
    }
    function test_profile_limits_and_unit_change() {
        editor.select(50)
        compare(editor.displayValue, 30)
        editor.select(17)
        compare(editor.displayValue, 18)
        editor.capabilityKey = "temperature.targetTemperature.F"
        verify(!editor.hasDraft)
        wait(800)
        compare(sent.count, 0)
    }
}
