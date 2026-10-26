pragma ComponentBehavior: Bound
import QtQuick

QtObject {
    id: editor
    property var confirmedValue: undefined
    property var revision: null
    property var capability: ({})
    property string capabilityKey: ""
    property bool enabled: false
    property bool canSubmit: false
    property bool dragging: false
    property int delay: 700
    property var draft: undefined
    property bool sending: false
    property bool accepted: false
    property var submittedValue: undefined
    property var submittedRevision: null
    property bool delayElapsed: false
    readonly property bool hasDraft: typeof draft === "number"
    readonly property var displayValue: hasDraft ? draft : confirmedValue
    signal requested(real value)

    property Timer debounce: Timer {
        interval: editor.delay
        repeat: false
        onTriggered: {
            editor.delayElapsed = true
            editor.flush()
        }
    }

    function cancel() {
        debounce.stop()
        draft = undefined
        sending = false
        accepted = false
        delayElapsed = false
        dragging = false
    }

    function select(value) {
        if (!enabled || typeof value !== "number" || !isFinite(value)) return
        const cap = capability
        const snapped = cap.minimum + Math.round((value - cap.minimum) / cap.step) * cap.step
        draft = Number(Math.max(cap.minimum, Math.min(cap.maximum, snapped)).toFixed(6))
        delayElapsed = false
        debounce.stop()
        if (!dragging) debounce.restart()
    }

    function adjust(direction) {
        if (typeof displayValue === "number") select(displayValue + direction * capability.step)
    }

    function beginDrag() { dragging = true; debounce.stop(); delayElapsed = false }
    function endDrag() { dragging = false; if (hasDraft) debounce.restart() }

    function flush() {
        if (!enabled || !canSubmit || sending || dragging || !hasDraft || !delayElapsed) return
        if (draft === confirmedValue) { draft = undefined; return }
        submittedValue = draft
        submittedRevision = revision
        accepted = false
        sending = true
        requested(submittedValue)
    }

    function acknowledge(wasAccepted) {
        if (!wasAccepted) { cancel(); return }
        accepted = true
    }

    function observe(connection, error, newRevision) {
        if (error || connection === "disconnected" || connection === "auth_required") {
            cancel()
            return
        }
        // A fresh readback, not queue acceptance or the intended value, completes a command.
        if (sending && accepted && connection === "connected" && newRevision > submittedRevision) {
            sending = false
            accepted = false
            if (draft === submittedValue) draft = undefined
            Qt.callLater(flush)
        }
    }

    onCanSubmitChanged: if (canSubmit) Qt.callLater(flush)
    onEnabledChanged: if (!enabled) cancel()
    onCapabilityKeyChanged: cancel()
}
