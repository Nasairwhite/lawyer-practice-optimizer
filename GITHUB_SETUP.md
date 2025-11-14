# GitHub Repository Setup

Repository URL: https://github.com/Nasairwhite/lawyer-practice-optimizer

## Repository Contents

```
lawyer-practice-optimizer/
├── .env.template              # Environment configuration template
├── .gitignore                 # Git ignore file
├── LICENSE                    # License file (if applicable)
├── README.md                  # Main documentation
├── LAWYER_EXPERIENCE_VISUAL.md  # Visual lawyer journey mockups
├── USER_JOURNEY_DIAGRAMS.md   # Mermaid flowchart diagrams
├── requirements.txt           # Python dependencies
├── analyzer.py               # Response analysis engine
├── app.py                    # Flask web application
├── demo.py                   # Demo script for sending emails
├── diagnostic_questions.py   # Question library (22 questions)
├── email_sender.py           # Email delivery system
├── moonshot_client.py        # Moonshot AI API client
├── test_local.py             # Local testing script
└── tests/                    # Test suite
    └── test_basic.py          # Basic functionality tests
└── templates/                # HTML templates
    ├── base.html              # Base template
    ├── index.html             # Landing page
    ├── question.html          # Question page
    ├── complete.html          # Completion page
    ├── report.html            # Report display
    ├── 404.html               # Not found error
    └── 500.html               # Server error
```

## Quick Start After Cloning

### 1. Clone the Repository

```bash
git clone https://github.com/Nasairwhite/lawyer-practice-optimizer.git
cd lawyer-practice-optimizer
```

### 2. Set Up Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.template .env
# Edit .env with your API keys and credentials
```

### 5. Run the Application

For local testing:
```bash
python app.py
# Open http://localhost:5000 in your browser
```

To send a diagnostic to a lawyer:
```bash
python demo.py
```

### 6. Run Tests

```bash
pytest tests/ -v
# Or: python -m pytest tests/test_basic.py -v
```

## What the System Does

1. **Email Delivery**: Sends secure, one-time links to lawyers
2. **AI-Guided Assessment**: 20 questions with intelligent guidance
3. **Automatic Analysis**: Moonshot AI analyzes responses
4. **Report Generation**: Personalized optimization report
5. **Time Savings**: Quantifies hours saved per week
6. **Action Roadmap**: Prioritized recommendations (Quick wins, 30/60/90 days)

## Viewing Visual Documentation

### Mermaid Diagrams
To view the flowchart diagrams in `USER_JOURNEY_DIAGRAMS.md`:
- Open on GitHub (renders automatically)
- Or use: https://mermaid.live/
- Or install VS Code extension: "Markdown Preview Mermaid Support"

### Visual Mockups
See `LAWYER_EXPERIENCE_VISUAL.md` for ASCII representations of what lawyers see at each step.

## Configuration Required

Before running, you need to configure:

1. **MOONSHOT_API_KEY**: Get from https://platform.moonshot.cn
2. **SMTP Credentials**: For email delivery
   - For Gmail: Enable 2FA and create App Password
3. **FLASK_SECRET_KEY**: Generate a random string

## Security Features

- One-time use diagnostic links
- 7-day link expiration
- Session-based responses (stored in memory)
- No sensitive data stored permanently (by default)

## Next Steps

1. Configure your `.env` file
2. Test locally: `python test_local.py`
3. Send your first diagnostic: `python demo.py`
4. Review the visual documentation to understand the full flow

## Making Changes

1. Create a new branch: `git checkout -b feature-name`
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Commit: `git commit -m "Description of changes"`
5. Push: `git push origin feature-name`
6. Create a pull request on GitHub

## Documentation

- **README.md**: Full usage instructions and API docs
- **USER_JOURNEY_DIAGRAMS.md**: Visual flowcharts
- **LAWYER_EXPERIENCE_VISUAL.md**: Screen-by-screen mockups
- **Code comments**: Detailed docstrings in all modules

## Support

For issues or questions:
1. Check README.md troubleshooting section
2. Review test files for usage examples
3. Check GitHub Issues tab
4. Review commit history for recent changes

## License

This is a professional consultation tool. Use according to your business needs.
