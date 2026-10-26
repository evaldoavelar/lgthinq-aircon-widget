pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Controls as QQC
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC
import org.kde.plasma.workspace.dbus as DBus

PlasmoidItem {
    id: root
    readonly property string serviceName: "org.lgthinq.LGThinq"
    readonly property string objectPath: "/org/lgthinq/LGThinq/AirConditioner"
    readonly property string interfaceName: "org.lgthinq.LGThinq.AirConditioner1"
    property var snapshot: ({connection: "disconnected", state: {}, capabilities: {}})
    property bool available: false
    property bool pending: false
    property bool popupOpen: false
    property bool refreshOnOpenPending: false
    readonly property url bundledIcon: Qt.resolvedUrl("../images/lgthinq.svg")
    Plasmoid.icon: bundledIcon.toString().startsWith("file://")
        ? decodeURIComponent(bundledIcon.toString().substring(7)) : bundledIcon.toString()
    property string message: i18n("Aguardando serviço local…")
    readonly property bool busy: pending || snapshot.connection === "command_pending" || snapshot.connection === "connecting"
    readonly property bool canControl: available && snapshot.connection === "connected" && !busy
    property var keys: []
    readonly property bool controlsAllowed: keys.some(key => snapshot.capabilities[key] && snapshot.capabilities[key].writable)
    readonly property string summary: temperatureSummary()
    readonly property var confirmedPower: {
        const key = keys.find(name => name.endsWith("airConOperationMode"))
        return key ? valueFor(snapshot.capabilities[key]) : undefined
    }
    readonly property string preferredUnit: Plasmoid.configuration.preferredUnit || "C"
    readonly property string powerKey: findKey("airConOperationMode")
    readonly property string targetKey: findKey("targetTemperature", preferredUnit)
    readonly property string currentKey: findKey("currentTemperature", preferredUnit)
    readonly property var targetCap: snapshot.capabilities[targetKey] || ({})
    readonly property var ambientTemperature: currentKey ? valueFor(snapshot.capabilities[currentKey]) : undefined
    readonly property var targetTemperature: targetKey ? valueFor(targetCap) : undefined
    readonly property bool hasTemperatureRange: typeof targetCap.minimum === "number"
        && typeof targetCap.maximum === "number" && targetCap.maximum > targetCap.minimum
        && typeof targetCap.step === "number" && targetCap.step > 0
    readonly property string ecoKey: findKey("powerSaveEnabled")
    readonly property var featureKeys: [findKey("currentJobMode"), findKey("windStrength"),
        findKey("relativeStopTimer", "", "sleepTimer"), findKey("rotateUpDown")].filter(key => key)
    readonly property bool inPanel: Plasmoid.formFactor === PlasmaCore.Types.Horizontal
        || Plasmoid.formFactor === PlasmaCore.Types.Vertical
    preferredRepresentation: inPanel ? compactRepresentation : fullRepresentation
    Layout.minimumWidth: inPanel ? 24 : 400
    Layout.minimumHeight: inPanel ? 24 : 520
    Layout.preferredWidth: inPanel ? 64 : 440
    Layout.preferredHeight: inPanel ? 32 : 540
    implicitWidth: inPanel ? 64 : 440
    implicitHeight: inPanel ? 32 : 540
    width: implicitWidth
    height: implicitHeight
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    toolTipMainText: Plasmoid.configuration.deviceLabel || i18n("LG ThinQ AirCon Widget")
    toolTipSubText: i18n("%1 · %2", summary, message)

    function valueFor(cap) {
        if (!cap || !Array.isArray(cap.path)) return undefined
        let value = snapshot.state
        for (const part of cap.path || []) {
            if (Array.isArray(value)) value = value.find(entry => entry.unit === cap.unit)
            if (value === null || value === undefined) return undefined
            value = value[part]
        }
        return value
    }

    function display(value, unit) {
        if (value === null || value === undefined) return i18n("Indisponível")
        return String(value) + (unit ? " " + unit : "")
    }

    function findKey(leaf, unit, resource) {
        const matches = keys.filter(key => {
            const cap = snapshot.capabilities[key]
            return cap && Array.isArray(cap.path) && cap.path[cap.path.length - 1] === leaf && (!resource || cap.path[0] === resource)
        })
        return matches.find(key => unit && snapshot.capabilities[key].unit === unit)
            || matches.find(key => !snapshot.capabilities[key].unit) || matches[0] || ""
    }

    function prettyValue(value) {
        const labels = {POWER_ON: i18n("Ligado"), POWER_OFF: i18n("Desligado"), COOL: i18n("Frio"), HEAT: i18n("Aquecer"),
            AUTO: i18n("Auto"), AIR_DRY: i18n("Desumidificar"), FAN: i18n("Ventilar"), LOW: i18n("Baixa"), MID: i18n("Média"),
            HIGH: i18n("Alta"), NATURE: i18n("Natural"), UNSET: i18n("Desativado"), NORMAL: i18n("Normal")}
        if (value === undefined || value === null) return i18n("Indisponível")
        if (value === true) return i18n("Ativado")
        if (value === false) return i18n("Desativado")
        return labels[value] || String(value)
    }

    function featureTitle(key) {
        if (key.indexOf("JobMode") >= 0) return i18n("Modo")
        if (key.indexOf("windStrength") >= 0) return i18n("Ventilação")
        if (key.indexOf("sleepTimer") >= 0) return i18n("Sono")
        if (key.indexOf("rotateUpDown") >= 0) return i18n("Direção")
        return i18n("Função")
    }

    function featureIcon(key) {
        if (key.indexOf("JobMode") >= 0) return "snow"
        if (key.indexOf("windStrength") >= 0) return "fan"
        if (key.indexOf("sleepTimer") >= 0) return "moon"
        return "airflow"
    }

    function temperatureSummary() {
        const key = findKey("targetTemperature", preferredUnit)
        return key ? display(valueFor(snapshot.capabilities[key]), snapshot.capabilities[key].unit)
                   : available ? i18n("LG ThinQ AirCon Widget") : i18n("Offline")
    }

    function canWrite(key) {
        return canControl && key && snapshot.capabilities[key].writable
    }

    TemperatureEditor {
        id: temperatureEditor
        confirmedValue: root.targetTemperature
        revision: root.snapshot.updated_at
        capability: root.targetCap
        capabilityKey: root.targetKey
        enabled: root.available && root.hasTemperatureRange && root.targetCap.writable === true
            && ["connected", "connecting", "command_pending"].indexOf(root.snapshot.connection) >= 0
        canSubmit: root.canControl
        onRequested: value => {
            if (!root.command(root.targetKey, value, accepted => acknowledge(accepted)))
                acknowledge(false)
        }
    }

    function connectionMessage(data) {
        const errors = {
            setup_required: i18n("Abra as configurações para conectar à LG"),
            credential_required: i18n("Confira PAT e cofre nas configurações"),
            auth_required: i18n("Substitua o PAT nas configurações"),
            network_error: i18n("Não foi possível acessar a LG. Confira sua conexão."),
            device_offline: i18n("O aparelho está desconectado. Confira sua conexão Wi-Fi."),
            device_absent: i18n("O aparelho salvo não está disponível. Selecione outro aparelho."),
            selection_required: i18n("Selecione o aparelho e clique em Salvar e conectar."),
            region_unsupported: i18n("Região indisponível. Confira o país da conta LG."),
            rate_limited: i18n("Limite de consultas atingido. Aguarde antes de tentar novamente."),
            unsupported: i18n("Recurso indisponível para este aparelho."),
            real_control_not_authorized: i18n("Habilite Permitir comandos nas configurações de conexão."),
            dependency_missing: i18n("Instalação incompleta. Execute novamente o instalador local."),
            invalid_response: i18n("Resposta incompatível do serviço")
        }
        if (data.error) return errors[data.error] || i18n("Não foi possível concluir. Atualize o estado e tente novamente.")
        return ({connected: i18n("Conectado"),
            connecting: data.updated_at ? i18n("Atualizando…") : i18n("Conectando…"),
            disconnected: i18n("Desconectado"), auth_required: i18n("Autenticação necessária"),
            command_pending: i18n("Comando em andamento…"),
            operational_error: i18n("Erro operacional")})[data.connection] || i18n("Estado indisponível")
    }

    function acceptSnapshot(json) {
        try {
            const data = JSON.parse(String(json))
            if (!data || typeof data.state !== "object" || typeof data.capabilities !== "object") throw new Error("schema")
            snapshot = data
            const nextKeys = Object.keys(data.capabilities)
            if (JSON.stringify(keys) !== JSON.stringify(nextKeys)) keys = nextKeys
            available = true
            message = connectionMessage(data)
            temperatureEditor.observe(data.connection, data.error, data.updated_at)
        } catch (error) {
            available = false
            message = i18n("Resposta incompatível do serviço")
        }
    }

    function call(member, signature, args, callback) {
        const reply = DBus.SessionBus.asyncCall({service: serviceName, path: objectPath, iface: interfaceName,
            member: member, signature: "(" + signature + ")", arguments: args})
        let handled = false
        const finish = () => {
            if (handled) return
            handled = true
            if (reply.isError) {
                available = false
                pending = false
                message = i18n("Conexão local indisponível; confira a instalação do widget")
            } else {
                callback(reply.value)
            }
            reply.destroy()
        }
        reply.finished.connect(finish)
        if (reply.isFinished) finish()
    }

    function readSnapshot() { call("GetSnapshot", "", [], value => acceptSnapshot(value)) }

    // Bounded retries also request D-Bus activation after a backend crash.
    property int activationAttempts: 0
    Timer {
        interval: 5000
        repeat: true
        running: !root.available && root.activationAttempts < 3
        onTriggered: { root.activationAttempts += 1; root.readSnapshot() }
    }
    onAvailableChanged: {
        if (available) { activationAttempts = 0; Qt.callLater(refreshAfterOpening) }
        else temperatureEditor.cancel()
    }

    function refreshStatus() {
        if (!available || busy) return
        call("Refresh", "", [], () => readSnapshot())
    }

    function refreshAfterOpening() {
        if (!popupOpen || !refreshOnOpenPending || !available || busy) return
        refreshOnOpenPending = false
        refreshStatus()
    }

    onPopupOpenChanged: {
        refreshOnOpenPending = popupOpen
        if (popupOpen) Qt.callLater(refreshAfterOpening)
    }
    onBusyChanged: if (!busy) Qt.callLater(refreshAfterOpening)

    // Read local cache as a watchdog; never makes network calls from QML.
    Timer {
        interval: 5000
        running: root.available
        repeat: true
        onTriggered: root.readSnapshot()
    }


    function command(key, value, acknowledgment) {
        if (!canControl) return false
        pending = true
        call("Command", "ss", [key, JSON.stringify(value)], accepted => {
            pending = false
            if (!accepted) message = i18n("Comando rejeitado pelo serviço")
            if (acknowledgment) acknowledgment(accepted)
            readSnapshot()
        })
        return true
    }

    DBus.SignalWatcher {
        busType: DBus.BusType.Session
        service: root.serviceName
        path: root.objectPath
        iface: root.interfaceName
        function dbusSnapshotChanged(json) { root.acceptSnapshot(json) }
    }
    DBus.DBusServiceWatcher {
        id: watcher
        busType: DBus.BusType.Session
        watchedService: root.serviceName
        onRegisteredChanged: {
            root.available = false
            root.pending = false
            if (registered) root.readSnapshot()
            else root.message = i18n("Serviço local indisponível")
        }
    }
    Component.onCompleted: readSnapshot()

    compactRepresentation: Item {
        implicitWidth: panelRow.implicitWidth + 12
        implicitHeight: Kirigami.Units.iconSizes.smallMedium
        RowLayout {
            id: panelRow
            anchors.centerIn: parent
            spacing: 5
            PanelIcon {
                id: panelIcon
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                powered: root.available && root.confirmedPower === "POWER_ON"
            }
            PC.Label {
                visible: Plasmoid.configuration.showPanelTemperature
                text: root.ambientTemperature === undefined || root.ambientTemperature === null
                    ? "—" : root.ambientTemperature + "°"
            }
        }
        MouseArea { anchors.fill: parent; onClicked: root.popupOpen = !root.popupOpen }
        Accessible.name: root.toolTipMainText + ": " + root.summary
    }

    // No native AppletPopup in the panel: it forces a themed background.
    fullRepresentation: inPanel ? emptyRepresentation : cardComponent
    property Component emptyRepresentation: Item {}
    onExpandedChanged: {
        if (inPanel && expanded) {
            popupOpen = !popupOpen
            expanded = false
        }
    }
    PlasmaCore.Dialog {
        id: cardDialog
        visualParent: root.compactRepresentationItem
        location: Plasmoid.location
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        backgroundHints: PlasmaCore.Types.NoBackground
        hideOnWindowDeactivate: true
        visible: root.inPanel && root.popupOpen
        onVisibleChanged: {
            if (!visible && root.inPanel) root.popupOpen = false
        }
        mainItem: Loader {
            sourceComponent: root.inPanel ? cardComponent : null
            width: 440
            height: Math.min(item ? item.implicitHeight : 540,
                Math.max(240, Screen.desktopAvailableHeight - 80))
        }
    }
    // Review layout from the text brief: native controls and a vertical feature list.
    // Existing protocol/controller logic above remains subject to its rights review.
    property Component cardComponent: Rectangle {
        id: popupRoot
        Layout.minimumWidth: 400
        Layout.minimumHeight: 520
        Layout.preferredWidth: 440
        Layout.preferredHeight: 540
        implicitWidth: 440
        implicitHeight: Math.max(540, cardContent.implicitHeight + footer.implicitHeight + 52)
        radius: 4
        Kirigami.Theme.inherit: false
        Kirigami.Theme.colorSet: Kirigami.Theme.Window
        color: Kirigami.Theme.backgroundColor
        border.color: Qt.alpha(Kirigami.Theme.textColor, 0.20)
        border.width: 1
        function openMenu(menu, anchor) {
            settingsMenu.close()
            options.close()
            const point = anchor.mapToItem(popupRoot, anchor.width, 0)
            menu.x = Math.max(20, Math.min(width - menu.width - 20, point.x - menu.width))
            menu.y = Math.max(20, Math.min(height - menu.height - 20, point.y - menu.height))
            menu.open()
        }
        Connections {
            target: root
            function onPopupOpenChanged() {
                if (!root.popupOpen) { settingsMenu.close(); options.close() }
            }
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            QQC.ScrollView {
                id: contentScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 0
                contentWidth: availableWidth
                clip: true
                QQC.ScrollBar.horizontal.policy: QQC.ScrollBar.AlwaysOff
                ColumnLayout {
                    id: cardContent
                    width: contentScroll.availableWidth
                    spacing: 12
                    RowLayout {
                        Layout.fillWidth: true
                        AirConditioner {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            powered: root.available && root.confirmedPower === "POWER_ON"
                        }
                        QQC.Label {
                            text: root.toolTipMainText
                            font.bold: true
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                        QQC.Button {
                            id: powerButton
                            objectName: "powerButton"
                            text: root.confirmedPower === "POWER_ON" ? i18n("Desligar") : i18n("Ligar")
                            Accessible.name: text
                            enabled: root.canWrite(root.powerKey)
                            onClicked: root.command(root.powerKey, root.confirmedPower === "POWER_ON" ? "POWER_OFF" : "POWER_ON")
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        QQC.Label { text: i18n("Ambiente"); Layout.fillWidth: true }
                        QQC.Label {
                            text: root.currentKey ? root.display(root.valueFor(root.snapshot.capabilities[root.currentKey]),
                                  root.snapshot.capabilities[root.currentKey].unit ? "°" + root.snapshot.capabilities[root.currentKey].unit : "") : "—"
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        QQC.Label { text: i18n("Temperatura desejada"); Layout.fillWidth: true }
                        QQC.Label {
                            id: selectedTemperatureLabel
                            text: temperatureEditor.displayValue === undefined ? "—" : String(temperatureEditor.displayValue)
                            font.pixelSize: 28
                            Accessible.name: i18n("Temperatura selecionada %1", text)
                        }
                        QQC.Label { text: root.targetCap.unit ? "°" + root.targetCap.unit : "" }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        visible: root.hasTemperatureRange
                        QQC.Button {
                            id: decreaseButton
                            text: "−"
                            implicitWidth: 40
                            enabled: temperatureEditor.enabled && temperatureEditor.displayValue > root.targetCap.minimum
                            Accessible.name: i18n("Diminuir temperatura")
                            onClicked: temperatureEditor.adjust(-1)
                        }
                        QQC.Slider {
                            id: targetSlider
                            Layout.fillWidth: true
                            from: root.hasTemperatureRange ? root.targetCap.minimum : 0
                            to: root.hasTemperatureRange ? root.targetCap.maximum : 1
                            stepSize: root.targetCap.step || 1
                            value: typeof temperatureEditor.displayValue === "number" ? temperatureEditor.displayValue : from
                            enabled: temperatureEditor.enabled
                            snapMode: QQC.Slider.SnapAlways
                            onMoved: temperatureEditor.select(value)
                            Accessible.name: i18n("Temperatura desejada")
                            onPressedChanged: {
                                if (pressed) temperatureEditor.beginDrag()
                                else {
                                    temperatureEditor.endDrag()
                                    value = Qt.binding(() => typeof temperatureEditor.displayValue === "number" ? temperatureEditor.displayValue : from)
                                }
                            }
                        }
                        QQC.Button {
                            id: increaseButton
                            objectName: "increaseButton"
                            text: "+"
                            implicitWidth: 40
                            enabled: temperatureEditor.enabled && temperatureEditor.displayValue < root.targetCap.maximum
                            Accessible.name: i18n("Aumentar temperatura")
                            onClicked: temperatureEditor.adjust(1)
                        }
                    }
                    QQC.Label {
                        Layout.fillWidth: true
                        visible: temperatureEditor.hasDraft
                        text: temperatureEditor.sending
                            ? i18n("Aplicando seleção…  Confirmada: %1", root.display(root.targetTemperature, root.targetCap.unit ? "°" + root.targetCap.unit : ""))
                            : i18n("Selecionada · aguardando envio…  Confirmada: %1", root.display(root.targetTemperature, root.targetCap.unit ? "°" + root.targetCap.unit : ""))
                        wrapMode: Text.WordWrap
                    }
                    QQC.Button {
                        id: ecoButton
                        Layout.fillWidth: true
                        visible: root.ecoKey !== ""
                        enabled: root.canWrite(root.ecoKey)
                        text: i18nc("Feature name and value", "%1: %2", i18n("Eco"), root.ecoKey ? root.prettyValue(root.valueFor(root.snapshot.capabilities[root.ecoKey])) : i18n("Indisponível"))
                        Accessible.name: i18n("Economia de energia")
                        Accessible.description: text
                        onClicked: root.command(root.ecoKey, !root.valueFor(root.snapshot.capabilities[root.ecoKey]))
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Repeater {
                            model: root.featureKeys
                            delegate: FeatureCard {
                                id: feature
                                required property string modelData
                                readonly property var cap: root.snapshot.capabilities[modelData] || ({values: []})
                                Layout.fillWidth: true
                                heading: root.featureTitle(modelData)
                                iconName: root.featureIcon(modelData)
                                valueText: root.prettyValue(root.valueFor(cap))
                                actionable: root.canWrite(modelData) && cap.values.length > 1
                                active: root.valueFor(cap) !== false && root.valueFor(cap) !== "UNSET"
                                onClicked: { if (actionable) { options.capKey = modelData; popupRoot.openMenu(options, feature) } }
                            }
                        }
                    }
                    QQC.Label {
                        id: readOnlyNotice
                        Layout.fillWidth: true
                        visible: root.available && root.keys.length > 0 && !root.snapshot.simulated
                            && !root.controlsAllowed
                        text: i18n("Habilite Permitir comandos nas configurações de conexão. No modo homelab, confira também a permissão de controle no servidor.")
                        color: Kirigami.Theme.neutralTextColor
                        wrapMode: Text.WordWrap
                    }
                }
            }
            RowLayout {
                id: footer
                Layout.fillWidth: true
                QQC.Label {
                    Layout.fillWidth: true
                    text: root.snapshot.simulated ? i18n("Simulação · nenhum aparelho real") : (root.available && root.snapshot.connection === "connected" && !root.controlsAllowed ? i18n("%1 · somente leitura", root.message) : root.message)
                    color: Kirigami.Theme.disabledTextColor
                    wrapMode: Text.WordWrap
                }
                PC.BusyIndicator { running: root.busy; visible: running; implicitWidth: 14; implicitHeight: 14 }
                QQC.ToolButton {
                    text: "↻"
                    enabled: !root.busy
                    Accessible.name: i18n("Atualizar estado")
                    onClicked: root.refreshStatus()
                }
                QQC.ToolButton {
                    id: settingsButton
                    text: "⋯"
                    Accessible.name: i18n("Mais opções")
                    onClicked: popupRoot.openMenu(settingsMenu, settingsButton)
                }
            }
        }
        MouseArea {
            anchors.fill: parent
            z: 100
            visible: settingsMenu.visible || options.visible
            onClicked: { settingsMenu.close(); options.close() }
        }
        CardMenu {
            id: options
            property string capKey: ""
            Repeater {
                model: options.capKey && root.snapshot.capabilities[options.capKey] ? root.snapshot.capabilities[options.capKey].values : []
                delegate: QQC.MenuItem {
                    required property var modelData
                    Layout.fillWidth: true
                    text: root.prettyValue(modelData)
                    onTriggered: { options.close(); root.command(options.capKey, modelData) }
                }
            }
        }
        CardMenu {
            id: settingsMenu
            QQC.MenuItem {
                Layout.fillWidth: true
                text: i18n("Configurar widget…"); icon.name: "configure"
                onTriggered: { settingsMenu.close(); Plasmoid.internalAction("configure").trigger() }
            }
            QQC.MenuItem {
                Layout.fillWidth: true
                text: i18n("Atualizar"); icon.name: "view-refresh"; enabled: !root.busy
                onTriggered: { settingsMenu.close(); root.refreshStatus() }
            }
            QQC.MenuSeparator { Layout.fillWidth: true }
            QQC.MenuItem { Layout.fillWidth: true; text: i18n("Credenciais protegidas pelo cofre"); enabled: false }
        }
    }
}
