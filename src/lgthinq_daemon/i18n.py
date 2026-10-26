"""Presentation translations, including zipapp resources; no protocol localization."""

import gettext as translations
import io
import locale
import os
import pkgutil

DOMAIN = "lgthinq-kde-widget"  # Existing catalog contract, independent of package name.


def load_translation(languages=None):
    if languages is None:
        languages = next(
            (
                os.environ[key].split(":")
                for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
                if os.environ.get(key)
            ),
            [],
        )
    result = None
    candidates = []
    for language in languages:
        if language in {"C", "POSIX", "C.UTF-8"}:
            break
        normalized = locale.normalize(language).split(".")[0].split("@")[0]
        for candidate in (normalized, normalized.split("_")[0]):
            if candidate not in candidates:
                candidates.append(candidate)
    for language in candidates:
        # Locale names originate in the environment; they must never become paths.
        if not language.replace("_", "").isalpha():
            continue
        try:
            data = pkgutil.get_data(__name__, f"locale/{language}/LC_MESSAGES/{DOMAIN}.mo")
        except (OSError, ImportError):
            continue
        if data is None:
            continue
        catalog = translations.GNUTranslations(io.BytesIO(data))
        if result is None:
            result = catalog
        else:
            result.add_fallback(catalog)
    return result or translations.NullTranslations()


_translation = load_translation()
gettext = _translation.gettext
pgettext = _translation.pgettext
ngettext = _translation.ngettext
npgettext = _translation.npgettext
