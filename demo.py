import asyncio
import json
from datetime import datetime
from pathlib import Path

print("=" * 60)
print("LinkedIn Job Application AI Agent - WORKING DEMO")
print("=" * 60)

# Create directories
Path("templates").mkdir(exist_ok=True)
Path("output").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# Create sample CV if not exists
cv_path = Path("templates/base_cv.md")
if not cv_path.exists():
    cv_content = """# Your Name

**Software Engineer | Machine Learning Enthusiast**

Munich, Germany | your.email@example.com | +49 123 456789

## Summary
Software engineer with 3+ years experience in Python and ML.

## Skills
Python, TensorFlow, React, Node.js, Docker, AWS, Machine Learning

## Experience
- Built ML pipelines at TechCorp (2023-Present)
- Developed web applications at StartupXYZ (2021-2023)

## Education
B.Sc. Computer Science, Deggendorf Institute of Technology
"""
    cv_path.write_text(cv_content, encoding='utf-8')
    print("Created: templates/base_cv.md")

# Mock jobs
jobs = [
    {
        "title": "Software Engineer - AI/ML",
        "company": "TechCorp GmbH",
        "location": "Munich, Germany",
        "description": "Python, Machine Learning, TensorFlow, AWS, Docker"
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Solutions AG", 
        "location": "Berlin, Germany",
        "description": "Python, Deep Learning, MLOps, Kubernetes, CI/CD"
    }
]

# Generate tailored applications
base_cv = cv_path.read_text(encoding='utf-8')

for i, job in enumerate(jobs, 1):
    print(f"\nProcessing job {i}: {job['title']} at {job['company']}")
    
    # Simple CV customization (keyword matching)
    tailored_cv = base_cv.replace(
        "## Skills",
        f"## Skills\n{job['description']}, Agile, Scrum"
    )
    
    # Generate cover letter
    cover_letter = f"""Your Name
your.email@example.com
+49 123 456789

{datetime.now().strftime("%B %d, %Y")}

Hiring Manager
{job['company']}
{job['location']}

Dear Hiring Manager,

I am excited to apply for the {job['title']} position at {job['company']}. 
My background in software engineering and machine learning aligns perfectly 
with your requirements in {job['description']}.

Throughout my career, I have developed production-ready ML systems and 
scalable web applications. I am particularly drawn to {job['company']} 
because of your innovative work in AI.

Thank you for considering my application.

Sincerely,
Your Name
"""
    
    # Calculate mock ATS score
    ats_score = 0.85 + (i * 0.05)  # 85%, 90%
    
    # Save to output
    job_dir = Path(f"output/application_{i}_{job['company'].replace(' ', '_')}")
    job_dir.mkdir(parents=True, exist_ok=True)
    
    (job_dir / "cv.md").write_text(tailored_cv, encoding='utf-8')
    (job_dir / "cover_letter.md").write_text(cover_letter, encoding='utf-8')
    (job_dir / "ats_report.json").write_text(
        json.dumps({"score": ats_score, "keywords": {"Python": 0.95, "ML": 0.90}}, indent=2),
        encoding='utf-8'
    )
    
    print(f"  ✓ Saved to: {job_dir} (ATS: {ats_score:.0%})")

# Generate report
report = f"""# Application Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

- Total Applications: {len(jobs)}
- Average ATS Score: 87.5%
- Jobs: {', '.join([j['title'] for j in jobs])}
"""
report_path = Path("output/report.md")
report_path.write_text(report, encoding='utf-8')

print(f"\n{'=' * 60}")
print(f"✓ Report: {report_path}")
print(f"✓ All files in: output/")
print(f"{'=' * 60}")
print("\nDEMO COMPLETE - This generated real files without API keys!")
