from backend.app.services.clauses import segment_clauses


def test_mixed_case_prose_is_not_mistaken_for_a_heading():
    prose = (
        "This is ordinary contract prose with a capitalized opening and enough words to remain a useful clause.\n"
        "this lower-case continuation is still part of the same paragraph and must not become a title."
    )

    clauses = segment_clauses([{"page": 1, "text": prose}])

    assert len(clauses) == 1
    assert clauses[0].title == ""
    assert "ordinary contract prose" in clauses[0].text
    assert "lower-case continuation" in clauses[0].text


def test_uppercase_and_case_insensitive_numbered_headings_are_recognized():
    pages = [{
        "page": 4,
        "text": (
            "CONFIDENTIALITY\nThe recipient shall protect confidential information under this agreement.\n"
            "section 2.1\nThe parties will use the protected information only for the stated purpose."
        ),
    }]

    clauses = segment_clauses(pages)

    assert [clause.title for clause in clauses] == ["CONFIDENTIALITY", "section 2.1"]
    assert all(clause.page == 4 for clause in clauses)


def test_heading_match_does_not_require_global_ignorecase():
    pages = [{
        "page": 1,
        "text": (
            "ARTICLE 1\nThis first section contains enough words to create a real clause in the output.\n"
            "Mixed Case Prose That Is Not a Heading\nThis sentence continues with further ordinary contract text.\n"
            "ARTICLE 2\nThe second clause has enough content to be retained in the output."
        ),
    }]

    clauses = segment_clauses(pages)

    assert clauses[0].title == "ARTICLE 1"
    assert all(clause.title != "Mixed Case Prose That Is Not a Heading" for clause in clauses)
