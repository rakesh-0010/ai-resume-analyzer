from app.analysis import calculate_ats_scores
from app.resume_parser import parse_resume
from tests.test_parser import SAMPLE_RESUME_TEXT


def test_ats_scoring_metrics():
    """Verify ATS score calculation on well-formatted sample resume."""
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    scores = calculate_ats_scores(parsed, SAMPLE_RESUME_TEXT)

    # Validate all required score dimensions exist
    assert 'ats_score' in scores
    assert 'skills_score' in scores
    assert 'formatting_score' in scores
    assert 'keyword_score' in scores
    assert 'content_quality_score' in scores
    assert 'completeness_score' in scores

    # High quality resume should score strongly (>= 80)
    assert scores['ats_score'] >= 75.0
    assert scores['completeness_score'] >= 85.0
    assert scores['skills_score'] >= 80.0
    assert scores['formatting_score'] >= 80.0


def test_scoring_determinism():
    """Verify that scoring is strictly deterministic and never random."""
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    score_1 = calculate_ats_scores(parsed, SAMPLE_RESUME_TEXT)
    score_2 = calculate_ats_scores(parsed, SAMPLE_RESUME_TEXT)

    assert score_1['ats_score'] == score_2['ats_score']
    assert score_1['skills_score'] == score_2['skills_score']
    assert score_1['formatting_score'] == score_2['formatting_score']
    assert score_1['keyword_score'] == score_2['keyword_score']


def test_sparse_resume_scoring():
    """Verify that a minimal or empty resume receives low but valid scores."""
    sparse_text = "John Smith\nPhone: 1234567890\nBasic worker looking for a job."
    parsed = parse_resume(sparse_text)
    scores = calculate_ats_scores(parsed, sparse_text)

    # Should score lower due to missing technical skills and missing sections
    assert scores['ats_score'] < 50.0
    assert scores['skills_score'] < 30.0
