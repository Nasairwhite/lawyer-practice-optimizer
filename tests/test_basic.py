"""Basic tests for lawyer practice optimizer."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

def test_import_modules():
    """Test that all modules can be imported."""
    try:
        from diagnostic_questions import diagnostic_questionnaire
        from analyzer import practice_analyzer
        assert diagnostic_questionnaire is not None
        assert practice_analyzer is not None
        print("✓ All modules imported successfully")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        raise

def test_question_count():
    """Test that we have the expected number of questions."""
    from diagnostic_questions import diagnostic_questionnaire
    questions = diagnostic_questionnaire.get_all_questions()
    assert len(questions) == 22, f"Expected 22 questions, got {len(questions)}"
    print(f"✓ Correct number of questions: {len(questions)}")

def test_categories():
    """Test that all categories are present."""
    from diagnostic_questions import diagnostic_questionnaire
    expected_categories = ['intake', 'documents', 'case_management', 
                          'billing', 'admin', 'pain_points']
    for cat in expected_categories:
        questions = diagnostic_questionnaire.get_questions_by_category(cat)
        assert len(questions) > 0, f"No questions found for category: {cat}"
    print(f"✓ All categories have questions")

if __name__ == "__main__":
    test_import_modules()
    test_question_count()
    test_categories()
    print("\n✅ All tests passed!")
