from datetime import timedelta

from app import textfmt
from app.models import utcnow
from conftest import make_quake


def test_relative_time_in_turkish():
    now = utcnow()
    assert textfmt.relative_tr(now - timedelta(seconds=30), now) == "az önce"
    assert textfmt.relative_tr(now - timedelta(minutes=12), now) == "12 dk önce"
    assert textfmt.relative_tr(now - timedelta(hours=5, minutes=59), now) == "5 sa önce"
    assert textfmt.relative_tr(now - timedelta(days=3, hours=2), now) == "3 gün önce"


def test_parse_magnitude():
    assert textfmt.parse_magnitude(None, 4.0, 2.0, 8.0) == 4.0
    assert textfmt.parse_magnitude(" 4,5 ", 4.0, 2.0, 8.0) == 4.5
    assert textfmt.parse_magnitude("1", 4.0, 2.0, 8.0) == 2.0
    assert textfmt.parse_magnitude("12", 4.0, 2.0, 8.0) == 8.0
    assert textfmt.parse_magnitude("dört", 4.0, 2.0, 8.0) is None


def test_messages_escape_html_and_link_to_map():
    quake = make_quake("59 8", minutes_ago=3, mag=4.2, location="Kozan <b>& Adana")
    line = textfmt.quake_line(quake, utcnow(), "https://deprem.test", distance_km=12.4)
    assert "Kozan &lt;b&gt;&amp; Adana" in line
    assert "🟠 <b>M4.2</b>" in line and "12 km uzakta" in line
    assert 'href="https://deprem.test/?q=59%208"' in line
    alert = textfmt.alert_text(quake, "https://deprem.test")
    assert alert.startswith("🟠 <b>Deprem: M4.2</b>") and "TSİ" in alert
