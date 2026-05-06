from industry_intelligence_agent.parsers.text import clean_text


def test_clean_text_normalizes_whitespace():
    assert clean_text(" Revenue   grew\n strongly. ") == "Revenue grew strongly."

