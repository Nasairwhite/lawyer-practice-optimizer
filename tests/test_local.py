#!/usr/bin/env python3
"""
Local test script for Lawyer Practice Optimization Diagnostic
Tests the application without sending emails.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from diagnostic_questions import diagnostic_questionnaire
from analyzer import practice_analyzer

def test_questions():
    """Test the question system."""
    print("Testing Questions...")
    print("=" * 70)

    questions = diagnostic_questionnaire.get_all_questions()
    print(f"✅ Loaded {len(questions)} questions")

    # Show first question
    first_q = questions[0]
    print(f"\nFirst question:")
    print(f"   Category: {diagnostic_questionnaire.categories[first_q.category]}")
    print(f"   Text: {first_q.question_text}")
    print(f"   Options: {len(first_q.options)}")

    print("\n✅ Questions system working!")
    return True

def test_scoring():
    """Test the scoring system."""
    print("\n\nTesting Scoring...")
    print("=" * 70)

    # Simulate responses (all middle-of-road answers)
    questions = diagnostic_questionnaire.get_all_questions()
    responses = {}
    for q in questions:
        # Choose option B for most questions
        responses[q.id] = q.options[1].id

    # Calculate score
    results = diagnostic_questionnaire.calculate_score(responses)
    print(f"✅ Total Score: {results['total_score']}")
    print(f"✅ Max Possible: {results['max_possible']}")
    print(f"✅ Overall Percentage: {results['overall_percentage']:.1f}%")
    print(f"✅ Grade: {diagnostic_questionnaire.get_optimization_grade(results['overall_percentage'])}")

    print("\nCategory Breakdown:")
    for category, percentage in results['category_percentages'].items():
        cat_name = diagnostic_questionnaire.categories[category]
        print(f"   - {cat_name}: {percentage:.1f}%")

    print("\n✅ Scoring system working!")
    return True

def test_analysis():
    """Test the analyzer."""
    print("\n\nTesting Analysis...")
    print("=" * 70)

    # Simulate responses (some good, some bad for variety)
    questions = diagnostic_questionnaire.get_all_questions()
    responses = {}
    for i, q in enumerate(questions):
        # Choose different option based on question index
        option_idx = i % 3  # Cycle through first 3 options
        responses[q.id] = q.options[option_idx].id

    # Run analysis
    analysis = practice_analyzer.analyze_responses_detailed(responses)

    print(f"✅ Analysis generated")
    print(f"✅ Score: {analysis['score_results']['overall_percentage']:.1f}%")
    print(f"✅ Total weekly savings: {analysis['recommendations']['total_weekly_savings']:.1f} hours")
    print(f"✅ # of quick wins: {len(analysis['recommendations']['quick_wins'])}")

    # Show first recommendation
    if analysis['recommendations']['quick_wins']:
        first_rec = analysis['recommendations']['quick_wins'][0]
        print(f"\nExample Quick Win:")
        print(f"   - Area: {first_rec.area}")
        print(f"   - Savings: {first_rec.time_savings:.1f} hours/week")
        print(f"   - Difficulty: {first_rec.implementation_time}")

    print("\n✅ Analysis system working!")
    return True

def test_ai_client():
    """Test AI client (if API key is available)."""
    print("\n\nTesting AI Client...")
    print("=" * 70)

    try:
        from moonshot_client import get_moonshot_client
        client = get_moonshot_client()
        print("✅ Moonshot client initialized")

        # Test guidance generation
        guidance = client.get_question_guidance(
            question_text="How do you track billable time?",
            practice_area="litigation"
        )
        print("✅ AI guidance generated:")
        print(f"   {guidance[:100]}...")

        print("\n✅ AI Client working!")
        return True

    except ValueError as e:
        print(f"⚠️  AI Client not configured: {e}")
        print("   (This is OK - set MOONSHOT_API_KEY in .env to enable AI features)")
        return True
    except Exception as e:
        print(f"❌ AI Client error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("Lawyer Practice Optimization Diagnostic - Local Test")
    print("=" * 70)
    print()

    all_passed = True

    try:
        all_passed &= test_questions()
        all_passed &= test_scoring()
        all_passed &= test_analysis()
        all_passed &= test_ai_client()

        print("\n" + "=" * 70)
        if all_passed:
            print("✅ All tests passed!")
            print()
            print("You can now:")
            print("1. Run the application: python app.py")
            print("2. Open http://localhost:5000 in your browser")
            print("3. Test the diagnostic workflow")
            print()
            print("To send emails to lawyers:")
            print("1. Set up your .env file with SMTP credentials")
            print("2. Run: python demo.py")
        else:
            print("❌ Some tests failed. Check the output above.")

        print("=" * 70)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
