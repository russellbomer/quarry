from pathlib import Path

from quarry.lib.schemas import ExtractionSchema
from quarry.tools.excavate.parser import SchemaParser
from quarry.tools.scout.analyzer import analyze_page
from quarry.tools.survey.builder import _merge_template_fields
from quarry.tools.survey.templates import get_template


def test_scout_survey_excavate_pipeline(tmp_path):
    html = Path("tests/fixtures/wizard_sample.html").read_text()
    analysis = analyze_page(html, url="https://example.com/news")

    template = get_template("article")
    merged_fields, matches = _merge_template_fields(
        template["fields"],
        (analysis.get("suggestions") or {}).get("field_candidates") or [],
    )

    assert matches  # Scout should map at least one field

    item_selector = (analysis.get("suggestions") or {}).get("item_selector")
    assert item_selector == "#newstwone > div"

    schema = ExtractionSchema(
        name="news_wizard",
        item_selector=item_selector,
        fields=merged_fields,
        url="https://example.com/news",
    )

    parser = SchemaParser(schema)
    items = parser.parse(html)

    assert len(items) == 3
    assert {item["title"] for item in items} == {
        "Alpha Headline",
        "Beta Headline",
        "Gamma Headline",
    }
    assert all(item["link"].startswith("https://example.com/news/") for item in items)
    assert all(item["image"].endswith(("alpha.png", "beta.png", "gamma.png")) for item in items)
