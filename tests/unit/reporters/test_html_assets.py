"""Tests de los assets estáticos (CSS/JS) del reporter HTML."""

from importlib.resources import files

import pytest

from pypex.reporters.html import HTMLReporter, HTMLScripts, HTMLStyles
from pypex.reporters.html.static_assets import load_static_asset
from tests.unit.core.test_results_processor import _project_with_entities

STATIC_DIR = files("pypex.reporters.html") / "static"


class TestStaticAssetFiles:
    """Los ficheros estáticos existen como recursos del paquete y no están vacíos."""

    @pytest.mark.parametrize("name", ["styles.css", "scripts.js"])
    def test_asset_is_package_resource(self, name):
        resource = STATIC_DIR / name
        assert resource.is_file()
        assert resource.read_text(encoding="utf-8").strip()

    @pytest.mark.parametrize("name", ["styles.css", "scripts.js"])
    def test_load_static_asset_matches_file(self, name):
        assert load_static_asset(name) == (STATIC_DIR / name).read_text(encoding="utf-8")

    def test_unknown_asset_raises(self):
        with pytest.raises(FileNotFoundError):
            load_static_asset("no_existe.css")

    def test_assets_have_no_wrapping_tags(self):
        assert "<style>" not in load_static_asset("styles.css")
        assert "<script>" not in load_static_asset("scripts.js")


class TestPublicAPI:
    """get_styles/get_scripts siguen devolviendo el bloque inline completo."""

    def test_get_styles_wraps_css(self):
        styles = HTMLStyles.get_styles()
        assert styles == f"\n<style>\n{load_static_asset('styles.css')}</style>\n"
        assert "--color-primary: #1a365d;" in styles

    def test_get_scripts_wraps_js(self):
        scripts = HTMLScripts.get_scripts()
        assert scripts == f"\n<script>\n{load_static_asset('scripts.js')}</script>\n"
        assert "document.addEventListener('DOMContentLoaded'" in scripts

    def test_regex_escape_is_preserved(self):
        # En el string Python original era '\\\\$&'; en JS debe quedar '\\$&'
        assert r"/[.*+?^${}()|[\]\\]/g, '\\$&'" in HTMLScripts.get_scripts()


class TestReportIsSelfContained:
    """El reporte generado incrusta el CSS y el JS inline."""

    def test_report_embeds_styles_and_scripts(self, tmp_path):
        output = tmp_path / "reporte.html"
        HTMLReporter(str(output)).generate_report(_project_with_entities())
        html = output.read_text(encoding="utf-8")

        assert html.count("<style>") == 1
        assert html.count("<script>") == 1
        assert HTMLStyles.get_styles() in html
        assert HTMLScripts.get_scripts() in html
        assert "<link" not in html
        assert "<script src" not in html
