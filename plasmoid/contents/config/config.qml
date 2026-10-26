import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory {
        name: i18n("Aparência")
        icon: "preferences-desktop-theme"
        source: "configAppearance.qml"
    }
    ConfigCategory {
        name: i18n("Conexão e credenciais")
        icon: "preferences-system-network"
        source: "configConnection.qml"
    }
}
