"""
Flask Web Application for Lawyer Practice Optimization Diagnostic

This module provides the web interface for the diagnostic questionnaire,
including multi-step form, AI guidance, and response collection.
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Optional

from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from moonshot_client import get_moonshot_client
from diagnostic_questions import diagnostic_questionnaire, DiagnosticQuestion


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Configuration
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)

# In-memory storage for sessions (in production, use Redis or database)
# Maps session_id -> {responses, metadata}
_session_store: Dict[str, Dict] = {}


def login_required(f):
    """Decorator to ensure user is logged in (has started the assessment)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "session_id" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def get_or_create_session():
    """Get or create a session for the user."""
    if "session_id" not in session:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
        session["start_time"] = datetime.now().isoformat()

        # Initialize session storage
        _session_store[session_id] = {
            "responses": {},
            "current_question": 0,
            "lawyer_name": None,
            "practice_area": "litigation",
            "completed": False
        }

    return session["session_id"]


def get_session_data() -> Optional[Dict]:
    """Get session data for current user."""
    session_id = session.get("session_id")
    if not session_id:
        return None
    return _session_store.get(session_id)


@app.route("/")
def index():
    """Landing page - introduction to the diagnostic."""
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_assessment():
    """Start the assessment - collect lawyer's name."""
    lawyer_name = request.form.get("lawyer_name", "").strip()

    if not lawyer_name:
        flash("Please enter your name to begin.", "error")
        return redirect(url_for("index"))

    # Create session
    session_id = get_or_create_session()
    _session_store[session_id]["lawyer_name"] = lawyer_name

    return redirect(url_for("question", question_idx=0))


@app.route("/question/<int:question_idx>")
@login_required
def question(question_idx: int):
    """Display a specific question in the diagnostic."""
    session_data = get_session_data()
    if not session_data:
        return redirect(url_for("index"))

    questions = diagnostic_questionnaire.get_all_questions()

    # Validate question index
    if question_idx < 0 or question_idx >= len(questions):
        return redirect(url_for("complete"))

    # Update current position
    session_data["current_question"] = question_idx

    current_question = questions[question_idx]

    # Get AI guidance for this question
    try:
        moonshot_client = get_moonshot_client()
        guidance = moonshot_client.get_question_guidance(
            question_text=current_question.question_text,
            practice_area=session_data["practice_area"]
        )
    except Exception as e:
        app.logger.error(f"Error getting AI guidance: {e}")
        guidance = "This question helps us understand your current workflow and identify optimization opportunities."

    # Get progress information
    progress = {
        "current": question_idx + 1,
        "total": len(questions),
        "percentage": int((question_idx + 1) / len(questions) * 100)
    }

    return render_template(
        "question.html",
        question=current_question,
        question_idx=question_idx,
        progress=progress,
        guidance=guidance,
        responses=session_data["responses"]
    )


@app.route("/save_response", methods=["POST"])
@login_required
def save_response():
    """Save a response to the current session."""
    session_data = get_session_data()
    if not session_data:
        return jsonify({"error": "Session not found"}), 400

    data = request.get_json()
    question_id = data.get("question_id")
    option_id = data.get("option_id")
    custom_text = data.get("custom_text", "")

    if not question_id or not option_id:
        return jsonify({"error": "Missing question_id or option_id"}), 400

    # Validate question exists
    try:
        diagnostic_questionnaire.get_question_by_id(question_id)
    except ValueError:
        return jsonify({"error": "Invalid question_id"}), 400

    # Save response
    session_data["responses"][question_id] = {
        "option_id": option_id,
        "custom_text": custom_text,
        "answered_at": datetime.now().isoformat()
    }

    return jsonify({"success": True, "question_id": question_id})


@app.route("/next_question/<int:current_idx>")
@login_required
def next_question(current_idx: int):
    """Navigate to the next question."""
    questions = diagnostic_questionnaire.get_all_questions()
    next_idx = current_idx + 1

    if next_idx >= len(questions):
        return redirect(url_for("complete"))

    return redirect(url_for("question", question_idx=next_idx))


@app.route("/prev_question/<int:current_idx>")
@login_required
def prev_question(current_idx: int):
    """Navigate to the previous question."""
    prev_idx = current_idx - 1

    if prev_idx < 0:
        return redirect(url_for("index"))

    return redirect(url_for("question", question_idx=prev_idx))


@app.route("/save_and_exit", methods=["POST"])
@login_required
def save_and_exit():
    """Save current progress and exit - user can return later."""
    session_data = get_session_data()
    if not session_data:
        return jsonify({"error": "Session not found"}), 400

    # Save responses (in a real app, this would go to a database)
    # For now, just acknowledge it's saved

    return jsonify({
        "success": True,
        "message": "Your progress has been saved. You can return to complete the assessment later."
    })


@app.route("/complete")
@login_required
def complete():
    """Show completion page before generating report."""
    session_data = get_session_data()
    if not session_data:
        return redirect(url_for("index"))

    # Mark as completed
    session_data["completed"] = True
    session_data["completed_at"] = datetime.now().isoformat()

    # Check how many questions were answered
    total_questions = len(diagnostic_questionnaire.get_all_questions())
    answered_questions = len(session_data["responses"])

    return render_template(
        "complete.html",
        lawyer_name=session_data["lawyer_name"],
        answered=answered_questions,
        total=total_questions
    )


@app.route("/generate_report")
@login_required
def generate_report():
    """Generate the final analysis report."""
    session_data = get_session_data()
    if not session_data:
        return redirect(url_for("index"))

    # Extract just the option_id from responses (remove custom_text and metadata)
    simple_responses = {}
    for q_id, response_data in session_data["responses"].items():
        simple_responses[q_id] = response_data["option_id"]

    # Calculate scores
    score_results = diagnostic_questionnaire.calculate_score(simple_responses)
    optimization_grade = diagnostic_questionnaire.get_optimization_grade(
        score_results["overall_percentage"]
    )

    # Get AI analysis
    try:
        moonshot_client = get_moonshot_client()
        analysis_results = moonshot_client.analyze_responses(
            responses=simple_responses,
            practice_area=session_data["practice_area"]
        )

        # Generate final report summary
        full_report = moonshot_client.generate_report_summary(
            analysis_results=analysis_results,
            lawyer_name=session_data["lawyer_name"]
        )

    except Exception as e:
        app.logger.error(f"Error generating AI report: {e}")
        full_report = f"""# Practice Optimization Report for {session_data["lawyer_name"]}

## Note
We encountered a technical issue generating your personalized AI analysis. However, you completed the diagnostic successfully. Your responses have been recorded and will be analyzed manually.

## Score Summary
- Overall Optimization Grade: {optimization_grade}
- Score: {score_results["overall_percentage"]:.1f}%
- Total Questions Answered: {len(simple_responses)}
"""

    # Save report to session for potential re-download
    session_data["report_data"] = {
        "grade": optimization_grade,
        "score": score_results["overall_percentage"],
        "full_report": full_report,
        "score_breakdown": score_results
    }

    return render_template(
        "report.html",
        lawyer_name=session_data["lawyer_name"],
        grade=optimization_grade,
        score=score_results["overall_percentage"],
        full_report=full_report,
        score_breakdown=score_results
    )


@app.route("/download_report")
@login_required
def download_report():
    """Download report as a text file."""
    session_data = get_session_data()
    if not session_data or "report_data" not in session_data:
        flash("Please complete the assessment first.", "error")
        return redirect(url_for("index"))

    report = session_data["report_data"]["full_report"]
    lawyer_name = session_data["lawyer_name"]

    return app.response_class(
        report,
        mimetype="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=practice-optimization-report-{lawyer_name.replace(' ', '-')}.md"
        }
    )


@app.route("/api/guidance/<question_id>")
@login_required
def api_get_guidance(question_id: str):
    """API endpoint to get AI guidance for a specific question."""
    session_data = get_session_data()
    if not session_data:
        return jsonify({"error": "Session not found"}), 400

    try:
        question = diagnostic_questionnaire.get_question_by_id(question_id)
        moonshot_client = get_moonshot_client()

        guidance = moonshot_client.get_question_guidance(
            question_text=question.question_text,
            practice_area=session_data["practice_area"]
        )

        return jsonify({"guidance": guidance})

    except ValueError:
        return jsonify({"error": "Invalid question ID"}), 400
    except Exception as e:
        app.logger.error(f"Error getting guidance: {e}")
        return jsonify({
            "guidance": "This question helps us understand your current workflow and identify optimization opportunities."
        })


@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template("500.html"), 500


if __name__ == "__main__":
    # Check for required environment variables
    required_vars = ["MOONSHOT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file.")
        print("Application will use demo mode with limited functionality.")

    # Run the app
    debug_mode = os.getenv("FLASK_ENV") == "development"
    port = int(os.getenv("PORT", 5000))

    app.run(debug=debug_mode, host="0.0.0.0", port=port)
