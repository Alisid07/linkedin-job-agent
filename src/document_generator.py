"""
AI-powered document generation and customization engine.
"""

from typing import List, Dict, Any
import re


class DocumentGenerator:
    def __init__(self, llm_engine):
        self.llm = llm_engine
        
    async def customize_cv(self, base_cv: str, job_description: str, target_skills: List[str], requirements: List[str]) -> str:
        analysis_prompt = f"""
        Analyze how this CV aligns with the job requirements.
        
        CV:
        {base_cv}
        
        Job Requirements:
        {requirements}
        
        Target Skills:
        {target_skills}
        
        Identify strong matches, transferable skills, and gaps.
        """
        
        analysis = await self.llm.generate(analysis_prompt, temperature=0.3)
        
        cv_prompt = f"""
        Rewrite this CV to emphasize relevance for the target job.
        
        Original CV:
        {base_cv}
        
        Job Description:
        {job_description}
        
        Alignment Analysis:
        {analysis}
        
        Instructions:
        1. Reorder experiences to put most relevant first
        2. Rewrite bullet points to mirror job description language
        3. Quantify achievements where possible
        4. Include keywords: {', '.join(target_skills)}
        5. Keep to 1-2 pages maximum
        6. Use professional markdown formatting
        
        Return the complete tailored CV.
        """
        
        tailored_cv = await self.llm.generate(cv_prompt, temperature=0.5)
        return self._clean_formatting(tailored_cv)
    
    async def generate_cover_letter(self, base_template: str, job: Any, user_profile: Dict[str, Any]) -> str:
        hook_prompt = f"""
        Create an engaging opening paragraph for a cover letter to {job.company}.
        
        Job: {job.title}
        Company: {job.company}
        Key Requirements: {job.requirements[:3] if job.requirements else ['Software development']}
        
        Candidate background:
        {user_profile.get('summary', '')}
        
        Write 2-3 sentences showing genuine interest and connecting experience to their needs.
        Return only the hook paragraph.
        """
        
        hook = await self.llm.generate(hook_prompt, temperature=0.7)
        
        body_prompt = f"""
        Write body paragraphs for this cover letter:
        
        Job: {job.title} at {job.company}
        Requirements: {job.requirements if job.requirements else ['Software development']}
        
        Candidate Experience:
        {user_profile.get('experience', '')}
        
        Structure: 2-3 paragraphs connecting achievements to requirements.
        Opening hook to continue from: {hook}
        
        Return body paragraphs only.
        """
        
        body = await self.llm.generate(body_prompt, temperature=0.6)
        closing = self._generate_closing(job.company)
        
        full_letter = f"""
{user_profile.get('name', '[Your Name]')}
{user_profile.get('email', '[Email]')}
{user_profile.get('phone', '[Phone]')}

{self._current_date()}

Hiring Manager
{job.company}
{job.location}

Dear Hiring Manager,

{hook.strip()}

{body.strip()}

{closing}

Sincerely,
{user_profile.get('name', '[Your Name]')}
        """.strip()
        
        return full_letter
    
    def _generate_closing(self, company: str) -> str:
        return f"""I am excited about the opportunity to bring my skills to {company} and would welcome the chance to discuss how my background aligns with your team's needs. Thank you for considering my application. I look forward to the possibility of contributing to your continued success."""
    
    def _current_date(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")
    
    def _clean_formatting(self, text: str) -> str:
        text = re.sub(r'```markdown\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
