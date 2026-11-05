import os
import json
import re
import logging
from app.resume_parser import ACTION_VERBS, COMMON_SKILLS

logger = logging.getLogger(__name__)

# Try importing google.generativeai
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class AIService:
    """
    AI Service powered by Google Gemini API for deep resume analysis,
    section rewriting, grammar enhancement, and job description matching.
    Includes rule-based NLP fallbacks for offline testing or when API key is unconfigured.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY', '')
        self.client = None
        if GENAI_AVAILABLE and self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-1.5-flash or gemini-2.0-flash / gemini-pro
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.client = True
                logger.info("Google Gemini API client successfully initialized.")
            except Exception as e:
                logger.warning("Failed to initialize Google Gemini client: %s", e)
                self.client = None
        else:
            self.model = None

    def is_ai_available(self) -> bool:
        return self.client is not None and self.model is not None

    def analyze_resume_deep(self, resume_text: str, parsed_data: dict) -> dict:
        """
        Generates qualitative critique, strengths, weaknesses, and actionable recommendations.
        Uses Gemini when available, otherwise uses deterministic NLP analysis.
        """
        if self.is_ai_available():
            try:
                prompt = f"""
                You are an expert Senior ATS and Technical Recruiter.
                Analyze the following resume text and provide a structured JSON response.
                Resume Content:
                \"\"\"{resume_text[:4000]}\"\"\"

                Return ONLY valid JSON with keys:
                - "strengths": list of 3-5 specific strengths found in the resume.
                - "weaknesses": list of 3-5 specific weaknesses or missing elements.
                - "recommendations": list of 4-6 high-impact actionable improvements.
                - "summary_critique": 2-3 sentences evaluating the summary/headline.
                - "formatting_critique": 2-3 sentences evaluating layout, readability, and ATS compliance.
                - "suggested_action_verbs": list of 5-8 strong verbs that could strengthen the descriptions.

                Do NOT invent false experience. Strictly base analysis on the provided resume text.
                """
                response = self.model.generate_content(prompt)
                raw_json = response.text.strip()
                # Clean markdown blocks if present
                if raw_json.startswith("```"):
                    raw_json = re.sub(r"^```(?:json)?\n", "", raw_json)
                    raw_json = re.sub(r"\n```$", "", raw_json)
                return json.loads(raw_json)
            except Exception as ex:
                logger.warning("Gemini deep analysis failed or rate-limited: %s. Using heuristic analysis.", ex)

        # High-quality deterministic heuristic analysis fallback
        strengths = []
        weaknesses = []
        recommendations = []

        # Evaluate skills
        skills_count = parsed_data.get('skills', {}).get('total_count', 0)
        if skills_count >= 8:
            strengths.append(f"Strong technical breadth with {skills_count} industry-recognized technologies identified.")
        else:
            weaknesses.append("Limited technical keywords and tools explicitly listed in the skills section.")
            recommendations.append("Expand your Technical Skills section to include relevant languages, frameworks, and databases.")

        # Evaluate Action Verbs
        verbs = parsed_data.get('action_verbs', [])
        if len(verbs) >= 5:
            strengths.append(f"Good use of action-driven language ({', '.join(verbs[:4])}).")
        else:
            weaknesses.append("Bullet points lack impactful action verbs (e.g. Spearheaded, Engineered, Optimized).")
            recommendations.append("Begin every work experience and project bullet point with a past-tense action verb.")

        # Check for metrics / quantification
        metrics = re.findall(r'\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?|\b\d+\+\b|\b\d+x\b', resume_text)
        if len(metrics) >= 3:
            strengths.append("Contains measurable business outcomes and quantifiable impact metrics.")
        else:
            weaknesses.append("Achievements lack measurable metrics (percentages, dollar amounts, time saved).")
            recommendations.append("Quantify your achievements using the formula: Accomplished [X], as measured by [Y], by doing [Z].")

        # Check missing sections
        missing = parsed_data.get('missing_sections', [])
        if missing:
            weaknesses.append(f"Missing or poorly labeled sections: {', '.join([m.title() for m in missing[:3]])}.")
            recommendations.append(f"Add dedicated headings for: {', '.join([m.title() for m in missing])}.")
        else:
            strengths.append("Complete resume architecture with all standard ATS sections present.")

        suggested_verbs = [v.title() for v in list(ACTION_VERBS)[:6] if v not in [x.lower() for x in verbs]]

        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations,
            'summary_critique': "Ensure your professional summary is 3-4 lines focusing on target role, years of experience, and signature achievements.",
            'formatting_critique': "Standard single-column layouts with standard font sizes (10-12pt) and standard headings yield the highest ATS parse rates.",
            'suggested_action_verbs': suggested_verbs
        }

    def rewrite_content(self, section_type: str, content: str, target_role: str = "") -> dict:
        """
        Rewrites a summary, project, or experience bullets for impact, grammar, and ATS punch.
        Never invents qualifications.
        """
        if not content.strip():
            return {'error': 'Content cannot be empty'}

        if self.is_ai_available():
            try:
                prompt = f"""
                You are an elite career coach and resume editor.
                Rewrite and significantly improve the following resume section: '{section_type}'.
                Target Role: {target_role or 'Software Professional'}
                Original Content:
                \"\"\"{content}\"\"\"

                Rules:
                1. Fix all grammar, punctuation, and phrasing issues.
                2. Use strong, past-tense action verbs.
                3. Elevate professionalism and ATS keyword alignment.
                4. DO NOT invent false achievements, jobs, degrees, or metrics that the user did not supply.
                5. Provide:
                   - "improved_content": the rewritten text formatted ready for resume insertion.
                   - "key_changes": bullet points explaining what was enhanced.
                   - "action_verbs_used": list of action verbs integrated.

                Return ONLY valid JSON with keys: "improved_content", "key_changes", "action_verbs_used".
                """
                response = self.model.generate_content(prompt)
                raw_json = response.text.strip()
                if raw_json.startswith("```"):
                    raw_json = re.sub(r"^```(?:json)?\n", "", raw_json)
                    raw_json = re.sub(r"\n```$", "", raw_json)
                return json.loads(raw_json)
            except Exception as e:
                logger.warning("Gemini rewrite failed: %s. Using heuristic fallback.", e)

        # High quality heuristic rewrite fallback
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        improved_lines = []
        action_verbs_used = []
        action_verbs_pool = ['Spearheaded', 'Architected', 'Engineered', 'Optimized', 'Streamlined', 'Delivered']

        for i, line in enumerate(lines):
            clean = line.lstrip('•-* \t')
            verb = action_verbs_pool[i % len(action_verbs_pool)]
            action_verbs_used.append(verb)
            # Remove weak starting verbs like "Responsible for" or "Worked on"
            clean = re.sub(r'^(?:responsible for|worked on|helped with|participated in)\s+', '', clean, flags=re.IGNORECASE)
            clean = clean[0].lower() + clean[1:] if len(clean) > 1 else clean
            improved_lines.append(f"• {verb} {clean}")

        return {
            'improved_content': "\n".join(improved_lines) if improved_lines else content,
            'key_changes': [
                "Replaced passive duty phrases with active leadership verbs.",
                "Standardized bullet formatting for clean ATS parsing.",
                "Enhanced tone for senior and enterprise ATS systems."
            ],
            'action_verbs_used': action_verbs_used
        }

    def match_job_description(self, resume_text: str, resume_skills: list, job_text: str) -> dict:
        """
        Compares resume against a job description.
        Extracts required skills, compares overlap, identifies gaps, and calculates compatibility.
        """
        job_lower = job_text.lower()
        
        # 1. Extract required skills from job description
        job_skills = set()
        for cat, skills_list in COMMON_SKILLS.items():
            for s in skills_list:
                pattern = r'\b' + re.escape(s) + r'\b'
                if re.search(pattern, job_lower):
                    job_skills.add(s)

        # Normalize resume skills set
        resume_skills_lower = {s.lower() for s in resume_skills}
        # Also check raw text directly in case parsing missed any
        for js in job_skills:
            if re.search(r'\b' + re.escape(js) + r'\b', resume_text.lower()):
                resume_skills_lower.add(js)

        matching_skills = sorted(list(job_skills.intersection(resume_skills_lower)))
        missing_skills = sorted(list(job_skills.difference(resume_skills_lower)))

        total_req = len(job_skills)
        if total_req > 0:
            match_ratio = len(matching_skills) / total_req
            compatibility_score = round(match_ratio * 100, 1)
        else:
            compatibility_score = 50.0  # neutral if no specific skills found

        # Learning recommendations
        recommendations = []
        if missing_skills:
            top_missing = missing_skills[:5]
            recommendations.append(f"Consider acquiring hands-on project experience with key requirements: {', '.join([s.title() for s in top_missing])}.")
            recommendations.append("Incorporate these missing keywords into your resume's Skills and Experience sections where you have prior exposure.")
        else:
            recommendations.append("Excellent match! Your resume covers all primary technical requirements identified in the job posting.")
        
        recommendations.append("Align the exact job title and terminology from the job description in your professional headline.")

        return {
            'compatibility_score': compatibility_score,
            'required_skills': sorted([s.title() for s in job_skills]),
            'matching_skills': [s.title() for s in matching_skills],
            'missing_skills': [s.title() for s in missing_skills],
            'recommendations': recommendations
        }
