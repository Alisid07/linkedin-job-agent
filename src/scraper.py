"""
LinkedIn job scraper with mock data for testing.
"""

import asyncio
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import aiohttp


@dataclass
class JobListing:
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    posted_date: str
    salary_range: Optional[str] = None
    requirements: list = None
    skills: list = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.skills is None:
            self.skills = []


class LinkedInScraper:
    def __init__(self, config: Dict):
        self.config = config
        self.proxy_url = config.get('proxy_service')
        
    async def search_jobs(self, keywords: List[str], location: str, max_results: int = 25, job_type: Optional[str] = None, experience_level: Optional[str] = None) -> List[Dict]:
        # Return mock data for testing without API
        return self._get_mock_jobs()
    
    def _get_mock_jobs(self) -> List[Dict]:
        return [
            {
                'id': 'job_001',
                'title': 'Software Engineer',
                'company': 'TechCorp GmbH',
                'location': 'Munich, Germany',
                'description': """
                We are looking for a Software Engineer with experience in Python and Machine Learning.
                Requirements:
                - 3+ years Python development
                - Experience with TensorFlow or PyTorch
                - Knowledge of cloud platforms (AWS/GCP)
                - Bachelor's degree in Computer Science
                Skills: Python, Machine Learning, TensorFlow, AWS, Docker
                """,
                'url': 'https://linkedin.com/jobs/001',
                'date': '2026-04-01',
                'salary': 'EUR 60,000 - 80,000'
            },
            {
                'id': 'job_002',
                'title': 'Machine Learning Engineer',
                'company': 'AI Solutions AG',
                'location': 'Berlin, Germany',
                'description': """
                Join our ML team to build cutting-edge AI products.
                Requirements:
                - Strong Python skills
                - Deep learning framework experience
                - MLOps and deployment knowledge
                - Fluent in English and German
                Skills: Python, PyTorch, Kubernetes, MLOps, CI/CD
                """,
                'url': 'https://linkedin.com/jobs/002',
                'date': '2026-04-01',
                'salary': 'EUR 70,000 - 90,000'
            }
        ]
