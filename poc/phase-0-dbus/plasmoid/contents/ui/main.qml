pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root

    property real targetTemperature: 23.0
    property bool power: false
    property bool serviceResponded: false
    property string statusText: "Aguardando serviço D-Bus…"

    readonly property string serviceName: "org.lgthinq.LGThinq"
    readonly property string objectPath: "/org/lgthinq/LGThinq/AirConditioner"
    readonly property string interfaceName: "org.lgthinq.LGThinq.AirConditioner"

    preferredRepresentation: fullRepresentation

    function callMethod(member, signature, args, onSuccess) {
        const pendingReply = DBus.SessionBus.asyncCall({
            "service": root.serviceName,
            "path": root.objectPath,
            "iface": root.interfaceName,
            "member": member,
            "signature": "(" + signature + ")",
            "arguments": args
        })

        let handled = false
        const finish = () => {
            if (handled) return
            handled = true
            try {
                if (pendingReply.isError) {
                    root.serviceResponded = false
                    root.statusText = "Erro D-Bus: " + pendingReply.error.message
                    console.warn("[LG ThinQ PoC] " + root.statusText)
                } else {
                    root.serviceResponded = true
                    onSuccess(pendingReply.value)
                }
            } catch (error) {
                root.statusText = "Falha ao processar resposta D-Bus"
                console.warn("[LG ThinQ PoC] " + error)
            }
            pendingReply.destroy()
        }
        pendingReply.finished.connect(finish)
        if (pendingReply.isFinished) finish()
    }

    function refreshState() {
        root.statusText = "Consultando serviço…"
        callMethod("GetTemperature", "", [], (value) => {
            root.targetTemperature = Number(value)
            console.log("POC_INITIAL_TEMPERATURE", root.targetTemperature)
            root.statusText = "Conectado — estado fictício"
        })
        callMethod("GetPower", "", [], (value) => {
            root.power = Boolean(value)
            root.statusText = "Conectado — estado fictício"
        })
    }

    function requestTemperature(value) {
        callMethod("SetTemperature", "d", [value], (accepted) => {
            if (!Boolean(accepted)) {
                root.statusText = "O serviço rejeitou a temperatura de demonstração"
            } else {
                root.statusText = "Comando aceito; aguardando sinal de estado"
            }
        })
    }

    function requestPower(value) {
        callMethod("SetPower", "b", [value], (accepted) => {
            if (!Boolean(accepted)) {
                root.statusText = "O serviço rejeitou o comando de demonstração"
            } else {
                root.statusText = "Comando aceito; aguardando sinal de estado"
            }
        })
    }

    DBus.SignalWatcher {
        busType: DBus.BusType.Session
        service: root.serviceName
        path: root.objectPath
        iface: root.interfaceName

        function dbusStateChanged(temperature, isPowered) {
            root.targetTemperature = Number(temperature)
            root.power = Boolean(isPowered)
            root.serviceResponded = true
            root.statusText = "Estado atualizado por sinal D-Bus"
            console.log("[LG ThinQ PoC] StateChanged recebido:", temperature, isPowered)
        }
    }

    DBus.DBusServiceWatcher {
        busType: DBus.BusType.Session
        watchedService: root.serviceName
        onRegisteredChanged: {
            console.log("POC_SERVICE_AVAILABLE", registered)
            root.serviceResponded = false
            if (registered) root.refreshState()
            else root.statusText = "Serviço indisponível"
        }
    }

    Component.onCompleted: refreshState()

    fullRepresentation: Item {
        Layout.minimumWidth: 320
        Layout.minimumHeight: 250
        Layout.preferredWidth: 360
        Layout.preferredHeight: 280

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: "LG ThinQ — PoC D-Bus"
                font.bold: true
                font.pixelSize: 18
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: "Demonstração local; não controla o ar-condicionado real."
                wrapMode: Text.WordWrap
                opacity: 0.8
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 1
                color: "#808080"
                opacity: 0.35
            }

            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    text: "Energia: " + (root.power ? "Ligado" : "Desligado")
                }
                PlasmaComponents.Button {
                    text: root.power ? "Desligar (teste)" : "Ligar (teste)"
                    enabled: root.serviceResponded
                    onClicked: root.requestPower(!root.power)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents.Button {
                    text: "−"
                    enabled: root.serviceResponded && root.targetTemperature > 10.0
                    onClicked: root.requestTemperature(root.targetTemperature - 1.0)
                }
                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: root.targetTemperature.toFixed(1) + " °C"
                    font.pixelSize: 24
                    font.bold: true
                }
                PlasmaComponents.Button {
                    id: increaseButton
                    text: "+"
                    enabled: root.serviceResponded && root.targetTemperature < 35.0
                    onClicked: root.requestTemperature(root.targetTemperature + 1.0)
                }
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: root.statusText
                wrapMode: Text.WordWrap
                font.pixelSize: 12
            }

            PlasmaComponents.Button {
                Layout.alignment: Qt.AlignRight
                text: "Consultar estado"
                onClicked: root.refreshState()
            }
        }
    }
}
