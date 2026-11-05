import re
import os
import pymupdf  # PyMuPDF
import docx

# Action verbs commonly recognized in ATS algorithms
ACTION_VERBS = {
    'managed', 'led', 'developed', 'designed', 'architected', 'implemented',
    'engineered', 'created', 'built', 'spearheaded', 'orchestrated', 'optimized',
    'increased', 'decreased', 'reduced', 'improved', 'scaled', 'delivered',
    'collaborated', 'accelerated', 'transformed', 'automated', 'streamlined',
    'analyzed', 'generated', 'initiated', 'achieved', 'conducted', 'directed',
    'formulated', 'mentored', 'established', 'executed', 'produced', 'resolved',
    'negotiated', 'deployed', 'programmed', 'standardized', 'consolidated'
}

# Standard section keywords
SECTION_KEYWORDS = {
    'summary': ['professional summary', 'summary', 'profile', 'about me', 'objective', 'executive summary'],
    'skills': ['technical skills', 'skills', 'technologies', 'core competencies', 'expertise', 'proficiencies', 'tools'],
    'experience': ['work experience', 'experience', 'professional experience', 'employment history', 'work history'],
    'education': ['education', 'academic background', 'educational qualifications', 'academics', 'degrees'],
    'projects': ['projects', 'key projects', 'personal projects', 'academic projects'],
    'certifications': ['certifications', 'licenses', 'credentials', 'certified'],
    'achievements': ['achievements', 'awards', 'honors', 'publications', 'accomplishments']
}

# Common technical skills dictionary for fast tagging & alias resolution
COMMON_SKILLS = {
    'Languages': ['python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'c', 'ruby', 'go', 'golang', 'php', 'swift', 'kotlin', 'rust', 'r', 'scala', 'sql', 'html', 'html5', 'css', 'css3', 'bash', 'shell'],
    'Frameworks & Libraries': ['flask', 'django', 'fastapi', 'react', 'react.js', 'angular', 'vue', 'vue.js', 'node.js', 'express', 'express.js', 'spring', 'spring boot', 'next.js', 'bootstrap', 'tailwind', 'jquery', 'pandas', 'numpy', 'scipy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras'],
    'Databases': ['mysql', 'postgresql', 'postgres', 'mongodb', 'sqlite', 'redis', 'oracle', 'mariadb', 'cassandra', 'dynamodb', 'elasticsearch'],
    'Cloud & DevOps': ['aws', 'amazon web services', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ci/cd', 'terraform', 'ansible', 'linux', 'nginx'],
    'Tools & Methodologies': ['jira', 'agile', 'scrum', 'kanban', 'rest', 'restful api', 'graphql', 'postman', 'microservices', 'unit testing', 'pytest', 'selenium']
}


def extract_text_from_pdf(file_path: str) -> str:
    """Extracts raw text from a PDF file using PyMuPDF."""
    text_content = []
    doc = pymupdf.open(file_path)
    for page in doc:
        text_content.append(page.get_text())
    doc.close()
    return "\n".join(text_content).strip()


def extract_text_from_docx(file_path: str) -> str:
    """Extracts raw text from a DOCX file using python-docx."""
    doc = docx.Document(file_path)
    text_content = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            text_content.append(paragraph.text)
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                text_content.append(" | ".join(row_text))
    return "\n".join(text_content).strip()


def extract_text(file_path: str) -> str:
    """Dispatcher to extract text based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ('.docx', '.doc'):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def extract_contact_info(text: str) -> dict:
    """Extracts email, phone, links, and suspected name from resume text."""
    # Email
    email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(email_regex, text)
    email = emails[0] if emails else None

    # Phone numbers (various international and domestic formats)
    phone_regex = r'(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{3,5}'
    phones = [p.strip() for p in re.findall(phone_regex, text) if len(re.sub(r'\D', '', p)) >= 10]
    phone = phones[0] if phones else None

    # URLs (LinkedIn, GitHub, Portfolios)
    linkedin_match = re.search(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    linkedin = linkedin_match.group(0) if linkedin_match else None

    github_match = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    github = github_match.group(0) if github_match else None

    portfolio_match = re.search(r'(?:https?:\/\/)?(?:[a-zA-Z0-9-]+\.)+(?:com|io|me|dev|net|org)(?:\/[^\s]*)?', text, re.IGNORECASE)
    portfolio = None
    if portfolio_match:
        found_url = portfolio_match.group(0)
        if not ('linkedin' in found_url.lower() or 'github' in found_url.lower()):
            portfolio = found_url

    # Name extraction heuristic (first non-empty line with 2-4 capitalized words)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    candidate_name = None
    for line in lines[:5]:
        # Filter out common labels
        if any(keyword in line.lower() for keyword in ['curriculum', 'resume', 'cv', 'page', 'email', 'phone', '@']):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() or w in ['de', 'van', 'von'] for w in words if w.isalpha()):
            candidate_name = line
            break

    return {
        'name': candidate_name,
        'email': email,
        'phone': phone,
        'linkedin': linkedin,
        'github': github,
        'portfolio': portfolio
    }


def split_into_sections(text: str) -> dict:
    """
    Identifies and partitions resume into standard sections.
    """
    lines = text.split('\n')
    sections = {
        'contact': '',
        'summary': '',
        'skills': '',
        'experience': '',
        'education': '',
        'projects': '',
        'certifications': '',
        'achievements': '',
        'other': ''
    }

    current_section = 'contact'
    
    for line in lines:
        cleaned_line = line.strip().lower()
        if not cleaned_line:
            continue

        matched_section = None
        # Check if line matches a known section header
        if len(cleaned_line) < 40:
            clean_hdr = re.sub(r'[^a-z\s]', '', cleaned_line).strip()
            for sec, keywords in SECTION_KEYWORDS.items():
                if any(clean_hdr == kw or clean_hdr.startswith(kw + ':') for kw in keywords):
                    matched_section = sec
                    break

        if matched_section:
            current_section = matched_section
        else:
            sections[current_section] += line + '\n'

    return sections


def extract_skills(text: str) -> dict:
    """
    Extracts technical and soft skills present in the text, categorized.
    """
    lower_text = text.lower()
    # Normalize punctuation for tokenizing
    words_and_phrases = set(re.findall(r'[a-zA-Z0-9#+.]+', lower_text))
    
    found_by_category = {}
    all_found_skills = set()

    for category, skill_list in COMMON_SKILLS.items():
        matched = []
        for skill in skill_list:
            # Word boundary matching for exact phrases
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, lower_text):
                matched.append(skill.title() if not skill.isupper() else skill)
                all_found_skills.add(skill.lower())
        if matched:
            found_by_category[category] = matched

    return {
        'categorized': found_by_category,
        'all': sorted(list(all_found_skills)),
        'total_count': len(all_found_skills)
    }


def find_action_verbs(text: str) -> list:
    """Extracts strong action verbs found in bullet points or work descriptions."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    found = [word for word in set(words) if word in ACTION_VERBS]
    return sorted(found)


def parse_resume(raw_text: str) -> dict:
    """
    Complete parser that returns structured metadata from resume text.
    """
    contact = extract_contact_info(raw_text)
    sections = split_into_sections(raw_text)
    skills = extract_skills(raw_text)
    action_verbs = find_action_verbs(raw_text)

    # Detect present and missing sections
    present_sections = []
    missing_sections = []
    
    for sec_name, sec_keywords in SECTION_KEYWORDS.items():
        sec_content = sections.get(sec_name, '').strip()
        if len(sec_content) > 20:
            present_sections.append(sec_name)
        else:
            missing_sections.append(sec_name)

    word_count = len(raw_text.split())

    return {
        'contact': contact,
        'sections': sections,
        'skills': skills,
        'action_verbs': action_verbs,
        'present_sections': present_sections,
        'missing_sections': missing_sections,
        'word_count': word_count
    }
