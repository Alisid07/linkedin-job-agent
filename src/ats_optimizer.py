"""
ATS (Applicant Tracking System) optimization engine.
"""

import re
from typing import List, Dict, Any
from collections import Counter


class ATSOptimizer:
    def __init__(self):
        self.common_stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        self.section_headers = {'experience', 'education', 'skills', 'summary', 'objective', 'projects', 'certifications'}
        
    def analyze(self, cv_content: str, job_description: str) -> Dict[str, Any]:
        job_keywords = self._extract_keywords(job_description)
        cv_keywords = self._extract_keywords(cv_content)
        
        matches = {}
        for keyword, importance in job_keywords.items():
            if keyword in cv_keywords:
                match_score = min(cv_keywords[keyword] / importance, 1.0)
                matches[keyword] = round(match_score, 2)
        
        missing = [kw for kw in job_keywords if kw not in cv_keywords and job_keywords[kw] > 1]
        format_issues = self._check_formatting(cv_content)
        
        if len(job_keywords) > 0:
            coverage = len(matches) / len(job_keywords)
            quality = sum(matches.values()) / len(matches) if matches else 0
            score = (coverage * 0.6 + quality * 0.4)
        else:
            score = 0
        
        if format_issues.get('has_tables') or format_issues.get('has_images'):
            score *= 0.8
        
        return {
            'score': round(score, 2),
            'keyword_matches': matches,
            'missing_keywords': missing[:10],
            'job_keywords_total': len(job_keywords),
            'matched_keywords': len(matches),
            'format_issues': format_issues,
            'recommendations': self._generate_recommendations(missing, format_issues)
        }
    
    def _extract_keywords(self, text: str) -> Dict[str, int]:
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        filtered = [w for w in words if len(w) > 2 and w not in self.common_stopwords]
        counts = Counter(filtered)
        
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) if i < len(filtered)-1]
        bigram_counts = Counter(bigrams)
        
        keywords = dict(counts)
        for bg, count in bigram_counts.items():
            if count > 1:
                keywords[bg] = count * 2
        return keywords
    
    def _check_formatting(self, cv: str) -> Dict[str, bool]:
        return {
            'has_tables': bool(re.search(r'\|.*\|.*\|', cv)),
            'has_images': '![' in cv or 'data:image' in cv,
            'has_special_chars': bool(re.search(r'[^\w\s\-\.\,\(\)\/\@]', cv)),
            'missing_sections': not any(h in cv.lower() for h in self.section_headers),
            'too_long': len(cv.split()) > 1000,
            'headers_unclear': not bool(re.search(r'^#{1,2}\s+\w+|^\w+[\s\-]+\w*\n[=\-]+', cv, re.MULTILINE))
        }
    
    def _generate_recommendations(self, missing: List[str], issues: Dict[str, bool]) -> List[str]:
        recs = []
        if missing:
            recs.append(f"Add missing keywords: {', '.join(missing[:5])}")
        if issues.get('has_tables'):
            recs.append("Remove tables - use bullet points instead")
        if issues.get('missing_sections'):
            recs.append("Add clear section headers (## Experience, ## Skills)")
        if issues.get('too_long'):
            recs.append("Reduce length to under 1000 words")
        return recs
