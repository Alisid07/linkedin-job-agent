"""
LinkedIn Job Application AI Agent
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from llm_engine import LLMEngine
from scraper import LinkedInScraper, JobListing
from document_generator import DocumentGenerator
from ats_optimizer import ATSOptimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ApplicationPackage:
    job_id: str
    tailored_cv: str
    cover_letter: str
    ats_score: float
    keyword_matches: Dict[str, float]
    generated_at: datetime


class JobApplicationAgent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.llm = LLMEngine(self.config.get('llm', {}))
        self.scraper = LinkedInScraper(self.config)
        self.doc_gen = DocumentGenerator(self.llm)
        self.ats = ATSOptimizer()
        self.history_file = Path("data/application_history.json")
        self.history_file.parent.mkdir(exist_ok=True)
        
    def _load_config(self, path: str) -> Dict:
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {path} not found, using defaults")
            return self._default_config()
        except ImportError:
            logger.warning("PyYAML not installed, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        return {
            'llm': {
                'primary': 'openai',
                'fallback': 'anthropic',
                'max_concurrent': 3
            },
            'user_profile': {
                'name': 'Your Name',
                'email': 'email@example.com',
                'phone': '+49 123 456789',
                'location': 'Munich, Germany',
                'summary': 'Software engineering student with focus on AI/ML. 3+ years Python experience.',
                'experience': '- Developed ML pipelines using Python and TensorFlow\n- Built web applications with React and Node.js\n- Experience with cloud platforms (AWS, GCP)',
                'skills': ['Python', 'Machine Learning', 'TensorFlow', 'React', 'Node.js', 'Docker']
            }
        }
    
    async def run_job_search(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobListing]:
        logger.info(f"Searching for {keywords} in {location}")
        
        raw_jobs = await self.scraper.search_jobs(keywords=keywords, location=location, max_results=max_results)
        
        jobs = []
        for job_data in raw_jobs:
            structured = await self._extract_job_structure(job_data)
            jobs.append(structured)
            
        logger.info(f"Found {len(jobs)} jobs")
        return jobs
    
    async def _extract_job_structure(self, job: Dict) -> JobListing:
        prompt = f"""
        Extract structured data from this job posting as JSON:
        
        Title: {job.get('title')}
        Company: {job.get('company')}
        Description: {job.get('description', '')}
        
        Return format:
        {{
            "requirements": ["req1", "req2", ...],
            "skills": ["skill1", "skill2", ...],
            "salary_range": "salary or null"
        }}
        """
        
        try:
            extracted = await self.llm.generate_json(prompt)
        except Exception as e:
            logger.error(f"Failed to extract structure: {e}")
            # Parse manually from description
            desc = job.get('description', '')
            requirements = [line.strip('- ') for line in desc.split('\n') if line.strip().startswith('-')]
            skills = []
            extracted = {'requirements': requirements, 'skills': skills, 'salary_range': job.get('salary')}
        
        return JobListing(
            id=job['id'],
            title=job['title'],
            company=job['company'],
            location=job.get('location', 'Remote'),
            description=job.get('description', ''),
            url=job.get('url', ''),
            posted_date=job.get('date', 'Unknown'),
            salary_range=extracted.get('salary_range') or job.get('salary'),
            requirements=extracted.get('requirements', []),
            skills=extracted.get('skills', [])
        )
    
    async def generate_application(self, job: JobListing, base_cv: str, base_cover_letter: str) -> ApplicationPackage:
        logger.info(f"Generating application for {job.title} at {job.company}")
        
        tailored_cv = await self.doc_gen.customize_cv(
            base_cv=base_cv,
            job_description=job.description,
            target_skills=job.skills,
            requirements=job.requirements
        )
        
        cover_letter = await self.doc_gen.generate_cover_letter(
            base_template=base_cover_letter,
            job=job,
            user_profile=self.config.get('user_profile', {})
        )
        
        ats_result = self.ats.analyze(cv_content=tailored_cv, job_description=job.description)
        
        if ats_result['score'] < 0.85:
            logger.info(f"Improving CV for ATS (current score: {ats_result['score']:.0%})")
            tailored_cv = await self._improve_for_ats(tailored_cv, job.description, ats_result['missing_keywords'])
            ats_result = self.ats.analyze(tailored_cv, job.description)
        
        package = ApplicationPackage(
            job_id=job.id,
            tailored_cv=tailored_cv,
            cover_letter=cover_letter,
            ats_score=ats_result['score'],
            keyword_matches=ats_result['keyword_matches'],
            generated_at=datetime.now()
        )
        
        self._save_to_history(package, job)
        return package
    
    async def _improve_for_ats(self, cv: str, job_desc: str, missing_keywords: List[str]) -> str:
        if not missing_keywords:
            return cv
            
        prompt = f"""
        Revise this CV to naturally incorporate these keywords: {missing_keywords[:5]}
        
        Original CV:
        {cv}
        
        Rules:
        - Maintain professional tone
        - Only add keywords where factually accurate
        - Don't stuff keywords unnaturally
        """
        
        return await self.llm.generate(prompt, temperature=0.3)
    
    def _save_to_history(self, package: ApplicationPackage, job: JobListing):
        entry = {
            'timestamp': package.generated_at.isoformat(),
            'job': {
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location
            },
            'ats_score': package.ats_score,
            'keyword_matches': package.keyword_matches
        }
        
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []
        
        history.append(entry)
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    
    async def batch_process(self, jobs: List[JobListing], base_cv: str, base_cover_letter: str) -> List[ApplicationPackage]:
        semaphore = asyncio.Semaphore(2)  # Limit concurrent API calls
        
        async def process_with_limit(job):
            async with semaphore:
                return await self.generate_application(job, base_cv, base_cover_letter)
        
        tasks = [process_with_limit(job) for job in jobs]
        return await asyncio.gather(*tasks)
    
    def generate_report(self) -> str:
        if not self.history_file.exists():
            return "No application history found."
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return "No valid application history."
        
        total_apps = len(history)
        if total_apps == 0:
            return "No applications in history."
            
        avg_ats = sum(h.get('ats_score', 0) for h in history) / total_apps
        
        report = f"""# Job Application Analytics Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary
- Total Applications: {total_apps}
- Average ATS Score: {avg_ats:.1%}

## Recent Applications
"""
        
        for entry in history[-5:]:
            job = entry.get('job', {})
            report += f"\n- **{job.get('title', 'Unknown')}** at {job.get('company', 'Unknown')} (ATS: {entry.get('ats_score', 0):.0%})"
        
        return report


def create_sample_files():
    """Create sample input files if they don't exist"""
    
    # Config
    if not Path("config.yaml").exists():
        config_content = '''user_profile:
  name: "Your Name"
  email: "your.email@example.com"
  phone: "+49 123 456789"
  location: "Munich, Germany"
  summary: "Software engineering student with focus on AI/ML. 3+ years Python experience."
  experience: |
    - Developed machine learning pipelines using Python and TensorFlow
    - Built web applications with React and Node.js
    - Experience with cloud platforms (AWS, GCP)
  skills:
    - Python
    - Machine Learning
    - TensorFlow
    - React
    - Node.js
    - Docker

llm:
  primary: "openai"
  fallback: "anthropic"
  max_concurrent: 2
'''
        with open("config.yaml", "w", encoding='utf-8') as f:
            f.write(config_content)
        print("Created config.yaml - please update with your details")
    
    # Base CV template
    if not Path("templates/base_cv.md").exists():
        cv_content = '''# Your Name

**Software Engineer | Machine Learning Enthusiast**

Munich, Germany | your.email@example.com | +49 123 456789

## Summary
Software engineer with 3+ years of experience in Python development and machine learning. Passionate about building scalable AI solutions.

## Technical Skills
- **Languages:** Python, JavaScript, TypeScript
- **ML/AI:** TensorFlow, PyTorch, scikit-learn
- **Web:** React, Node.js, FastAPI
- **Cloud:** AWS, GCP, Docker, Kubernetes

## Experience

### Software Developer | TechCorp (2023-Present)
- Developed and deployed machine learning models for production use
- Built RESTful APIs serving 10,000+ daily requests
- Implemented CI/CD pipelines reducing deployment time by 40%

### Junior Developer | StartupXYZ (2021-2023)
- Created data processing pipelines handling 1TB+ daily
- Collaborated on frontend applications using React

## Education
**B.Sc. Computer Science** | Deggendorf Institute of Technology (2021-2025)
- Focus: Artificial Intelligence and Software Engineering
'''
        Path("templates").mkdir(exist_ok=True)
        with open("templates/base_cv.md", "w", encoding='utf-8') as f:
            f.write(cv_content)
        print("Created templates/base_cv.md")
    
    # Base cover letter template
    if not Path("templates/base_cover.md").exists():
        cover_content = '''Dear Hiring Manager,

I am writing to express my strong interest in the [Position] at [Company]. With my background in software engineering and machine learning, I am excited about the opportunity to contribute to your team.

In my current role, I have developed production-ready machine learning systems and scalable web applications. My experience with Python, TensorFlow, and cloud platforms aligns well with the requirements of this position.

I am particularly drawn to [Company] because of their innovative work in AI. I believe my technical skills and passion for innovation would make me a valuable addition.

Thank you for considering my application. I look forward to discussing how I can contribute.

Sincerely,
Your Name
'''
        with open("templates/base_cover.md", "w", encoding='utf-8') as f:
            f.write(cover_content)
        print("Created templates/base_cover.md")


async def main():
    """Demo the agent capabilities"""
    
    # Create sample files
    create_sample_files()
    
    # Check for API keys
    import os
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    
    if not has_openai and not has_anthropic:
        print("\n" + "="*60)
        print("WARNING: No API keys found!")
        print("Set them first with:")
        print('$env:OPENAI_API_KEY = "sk-your-key"')
        print('$env:ANTHROPIC_API_KEY = "sk-ant-your-key"')
        print("="*60 + "\n")
        print("Running in DEMO mode with limited functionality...\n")
    
    # Initialize agent
    try:
        agent = JobApplicationAgent("config.yaml")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return
    
    # Search for jobs
    print("Searching for jobs...")
    jobs = await agent.run_job_search(
        keywords=["Software Engineer", "Machine Learning"],
        location="Munich, Germany",
        max_results=2
    )
    
    print(f"\nFound {len(jobs)} relevant jobs\n")
    
    # Load base documents
    try:
        with open("templates/base_cv.md", "r", encoding='utf-8') as f:
            base_cv = f.read()
    except FileNotFoundError:
        base_cv = "# Your Name\n\nSoftware Engineer with Python experience."
    
    try:
        with open("templates/base_cover.md", "r", encoding='utf-8') as f:
            base_cover = f.read()
    except FileNotFoundError:
        base_cover = "Dear Hiring Manager,\n\nI am writing to apply..."
    
    # Generate applications
    if has_openai or has_anthropic:
        print("Generating tailored applications...")
        applications = await agent.batch_process(jobs, base_cv, base_cover)
        
        # Save outputs
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        for i, app in enumerate(applications):
            job_dir = output_dir / f"application_{i+1}_{jobs[i].company.replace(' ', '_')}"
            job_dir.mkdir(exist_ok=True)
            
            with open(job_dir / "cv.md", "w", encoding='utf-8') as f:
                f.write(app.tailored_cv)
            
            with open(job_dir / "cover_letter.md", "w", encoding='utf-8') as f:
                f.write(app.cover_letter)
            
            with open(job_dir / "ats_report.json", "w", encoding='utf-8') as f:
                json.dump({
                    "score": app.ats_score,
                    "keywords": app.keyword_matches
                }, f, indent=2)
            
            print(f"Saved application {i+1} to {job_dir}")
        
        # Generate analytics
        report = agent.generate_report()
        report_path = output_dir / "report.md"
        with open(report_path, "w", encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nAnalytics report saved to {report_path}")
    else:
        print("Skipping application generation (no API keys)")
        print("Job listings found:")
        for job in jobs:
            print(f"  - {job.title} at {job.company}")
    
    print("\nDone! Check the output folder.")


if __name__ == "__main__":
    asyncio.run(main())
