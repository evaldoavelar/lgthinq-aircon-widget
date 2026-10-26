import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.plasma.workspace.dbus as DBus

ColumnLayout {
    id: page
    spacing: 12
    property var settings: ({})
    property bool working: false
    property bool loaded: false
    property bool reachable: false
    property string feedback: i18n("Conectando ao componente local…")
    property string selectedDevice: ""
    readonly property string serviceName: "org.lgthinq.LGThinq"
    readonly property string objectPath: "/org/lgthinq/LGThinq/AirConditioner"
    readonly property string interfaceName: "org.lgthinq.LGThinq.Configuration1"

    function errorText(code) {
        return ({credential_required: i18n("Desbloqueie o KWallet/Secret Service ou informe um PAT válido."),
            auth_required: i18n("PAT recusado pela LG. Substitua a credencial e salve novamente."),
            selection_required: i18n("Selecione o aparelho e clique em Salvar e conectar."),
            no_devices: i18n("Nenhum ar-condicionado encontrado. Confira país e conta LG."),
            device_absent: i18n("O aparelho salvo não está disponível. Selecione outro aparelho."),
            invalid_settings: i18n("Confira o país, o aparelho e a confirmação de mudança para modo local."),
            region_unsupported: i18n("Região indisponível. Confira o país da conta LG."),
            network_error: i18n("Não foi possível acessar a LG. Confira sua conexão."),
            rate_limited: i18n("Limite de consultas atingido. Aguarde antes de tentar novamente."),
            dependency_missing: i18n("Instalação incompleta. Execute novamente o instalador local."),
            operational_error: i18n("Não foi possível concluir. Confira conexão e cofre e tente novamente.")})[code]
            || i18n("Falha na conexão. Confira a rede e tente novamente.")
    }

    function acceptSettings(value) {
        let data
        try { data = JSON.parse(String(value)) } catch (error) {
            reachable = false
            feedback = i18n("Resposta incompatível. Atualize a instalação local.")
            working = false
            return
        }
        if (data.unsupported) {
            reachable = false
            feedback = i18n("O backend antigo está em execução. Encerre-o e execute o instalador local.")
            working = false
            return
        }
        settings = data
        reachable = true
        if (!loaded) {
            country.text = data.country || "BR"
            control.checked = Boolean(data.allow_control)
            selectedDevice = data.device_id || ""
            loaded = true
        }
        if (!(data.devices || []).some(d => d.id === selectedDevice))
            selectedDevice = data.device_id || ""
        deviceBox.currentIndex = -1
        for (let i = 0; i < (data.devices || []).length; ++i) {
            if (data.devices[i].id === selectedDevice) {
                deviceBox.currentIndex = i
                break
            }
        }
        working = Boolean(data.busy)
        feedback = data.busy ? i18n("Consultando a LG…") : data.error ? errorText(data.error)
            : data.remote ? i18n("Conexão homelab preservada. Confirme abaixo para mudar para conexão local.")
            : data.device_id ? i18n("Configuração salva. O estado da conexão aparece no widget.")
            : i18n("Informe o PAT e salve para descobrir seus aparelhos.")
    }

    function call(member, signature, args, callback) {
        const reply = DBus.SessionBus.asyncCall({service: serviceName, path: objectPath,
            iface: interfaceName, member: member, signature: "(" + signature + ")", arguments: args})
        let handled = false
        const finish = () => {
            if (handled) return
            handled = true
            if (reply.isError) {
                working = false
                reachable = false
                feedback = i18n("Componente local indisponível. Execute ou atualize o instalador local e tente novamente.")
            } else callback(reply.value)
            reply.destroy()
        }
        reply.finished.connect(finish)
        if (reply.isFinished) finish()
    }
    function readSettings() { call("GetSettings", "", [], value => acceptSettings(value)) }
    function save() {
        working = true
        feedback = i18n("Salvando e conectando…")
        const values = {country: country.text.trim().toUpperCase(), allow_control: control.checked,
            convert_to_local: convert.checked}
        if (deviceBox.currentIndex >= 0)
            values.device_id = settings.devices[deviceBox.currentIndex].id
        call("Configure", "ss", [JSON.stringify(values), pat.text], accepted => {
            pat.clear()
            if (!accepted) {
                working = false
                feedback = i18n("Componente ocupado. Aguarde e tente novamente.")
            }
        })
        // Never bind a credential to Plasma configuration or retain it after submission.
        pat.clear()
    }

    QQC.Label { text: i18n("Conexão direta com a LG ThinQ"); font.bold: true }
    QQC.Label {
        Layout.fillWidth: true
        text: i18n("Cadastre seu PAT no cofre deste computador. O widget se conecta automaticamente, sem servidor separado. Use Salvar e conectar para aplicar esta aba.")
        wrapMode: Text.WordWrap
    }
    QQC.Label {
        Layout.fillWidth: true
        text: i18n("Crie seu PAT em %1 no navegador. Não informe a senha da conta LG.", "https://connect-pat.lgthinq.com/")
        wrapMode: Text.WordWrap
    }
    QQC.Label { text: i18n("País da conta LG") }
    QQC.TextField { id: country; objectName: "countryField"; text: "BR"; maximumLength: 2; enabled: !page.working }
    QQC.Label { text: i18n("PAT (deixe vazio para manter o existente)") }
    QQC.TextField {
        id: pat
        objectName: "patField"
        Layout.fillWidth: true
        echoMode: TextInput.Password
        inputMethodHints: Qt.ImhHiddenText | Qt.ImhNoPredictiveText | Qt.ImhSensitiveData
        maximumLength: 16384
        enabled: !page.working
        selectByMouse: true
    }
    QQC.Label { text: i18n("Ar-condicionado") }
    QQC.ComboBox {
        id: deviceBox
        objectName: "deviceSelector"
        Layout.fillWidth: true
        model: page.settings.devices || []
        textRole: "label"
        enabled: page.reachable && !page.working && !page.settings.remote && count > 0
        displayText: count > 0 ? currentText : page.working ? i18n("Buscando aparelhos…")
            : !page.reachable ? i18n("Aguardando componente local")
            : i18n("Salve a conexão ou clique em Buscar aparelhos")
        onActivated: page.selectedDevice = page.settings.devices[currentIndex].id
    }
    QQC.CheckBox {
        id: control
        objectName: "allowControl"
        text: i18n("Permitir comandos ao aparelho pelos controles do widget")
        enabled: !page.working
    }
    QQC.CheckBox {
        id: convert
        visible: Boolean(page.settings.remote)
        text: i18n("Substituir a conexão homelab por conexão direta neste computador")
        enabled: !page.working
    }
    RowLayout {
        QQC.Button {
            objectName: "saveConnection"
            text: i18n("Salvar e conectar")
            enabled: page.reachable && !page.working && (!page.settings.remote || convert.checked)
            onClicked: page.save()
        }
        QQC.Button {
            text: i18n("Buscar aparelhos")
            enabled: page.reachable && !page.working && !page.settings.remote
            onClicked: {
                page.working = true
                page.call("Discover", "", [], accepted => {
                    if (!accepted) { page.working = false; page.feedback = i18n("Componente ocupado. Tente novamente.") }
                })
            }
        }
        QQC.Button { text: i18n("Reconectar"); enabled: !page.working; onClicked: page.readSettings() }
        QQC.BusyIndicator { running: page.working; visible: running }
    }
    QQC.Label { Layout.fillWidth: true; text: page.feedback; wrapMode: Text.WordWrap }
    Item { Layout.fillHeight: true }
    DBus.SignalWatcher {
        busType: DBus.BusType.Session
        service: page.serviceName
        path: page.objectPath
        iface: page.interfaceName
        function dbusConfigurationChanged(value) { page.acceptSettings(value) }
    }
    Timer { interval: 1500; running: page.working; repeat: true; onTriggered: page.readSettings() }
    Component.onCompleted: readSettings()
    Component.onDestruction: pat.clear()
}
