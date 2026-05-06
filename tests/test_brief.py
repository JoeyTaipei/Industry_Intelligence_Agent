from industry_intelligence_agent.analysis.brief import generate_brief
from industry_intelligence_agent.models import SourceDocument


def test_generate_brief_contains_core_sections():
    document = SourceDocument(
        source_type="news",
        title="Sample",
        text="The market shows growth in cloud demand. Competition is a risk for margins.",
    )

    brief = generate_brief(company="ExampleCo", industry="cloud software", documents=[document])

    assert brief["company"] == "ExampleCo"
    assert brief["industry"] == "cloud software"
    assert brief["source_count"] == 1
    assert "risks" in brief
    assert "opportunities" in brief
