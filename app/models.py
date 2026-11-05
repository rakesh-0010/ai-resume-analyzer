import json
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    profile_picture = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    target_role = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resumes = db.relationship('Resume', back_populates='user', cascade='all, delete-orphan')
    analyses = db.relationship('ResumeAnalysis', back_populates='user', cascade='all, delete-orphan')
    job_descriptions = db.relationship('JobDescription', back_populates='user', cascade='all, delete-orphan')
    history_records = db.relationship('AnalysisHistory', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'target_role': self.target_role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Resume(db.Model):
    __tablename__ = 'resumes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'pdf' or 'docx'
    file_size = db.Column(db.Integer, nullable=False)      # in bytes
    raw_text = db.Column(db.Text, nullable=False)
    parsed_data = db.Column(db.Text, nullable=True)        # stored as JSON string
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='resumes')
    analyses = db.relationship('ResumeAnalysis', back_populates='resume', cascade='all, delete-orphan')
    history_records = db.relationship('AnalysisHistory', back_populates='resume', cascade='all, delete-orphan')

    @property
    def parsed(self):
        if self.parsed_data:
            try:
                return json.loads(self.parsed_data)
            except Exception:
                return {}
        return {}

    @parsed.setter
    def parsed(self, value):
        self.parsed_data = json.dumps(value) if value else "{}"

    @property
    def latest_analysis(self):
        if self.analyses:
            return sorted(self.analyses, key=lambda a: a.created_at, reverse=True)[0]
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M') if self.uploaded_at else ''
        }


class ResumeAnalysis(db.Model):
    __tablename__ = 'resume_analyses'

    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # ATS Scoring breakdown (0 to 100)
    ats_score = db.Column(db.Float, nullable=False, default=0.0)
    skills_score = db.Column(db.Float, nullable=False, default=0.0)
    formatting_score = db.Column(db.Float, nullable=False, default=0.0)
    keyword_score = db.Column(db.Float, nullable=False, default=0.0)
    content_quality_score = db.Column(db.Float, nullable=False, default=0.0)
    completeness_score = db.Column(db.Float, nullable=False, default=0.0)

    # Analysis details (stored as JSON)
    detailed_feedback = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    strengths = db.Column(db.Text, nullable=True)
    weaknesses = db.Column(db.Text, nullable=True)
    action_verbs_found = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    resume = db.relationship('Resume', back_populates='analyses')
    user = db.relationship('User', back_populates='analyses')
    history_entries = db.relationship('AnalysisHistory', back_populates='analysis', cascade='all, delete-orphan')

    def get_feedback(self):
        try:
            return json.loads(self.detailed_feedback) if self.detailed_feedback else {}
        except Exception:
            return {}

    def get_recommendations(self):
        try:
            return json.loads(self.recommendations) if self.recommendations else []
        except Exception:
            return []

    def get_strengths(self):
        try:
            return json.loads(self.strengths) if self.strengths else []
        except Exception:
            return []

    def get_weaknesses(self):
        try:
            return json.loads(self.weaknesses) if self.weaknesses else []
        except Exception:
            return []

    def get_action_verbs(self):
        try:
            return json.loads(self.action_verbs_found) if self.action_verbs_found else []
        except Exception:
            return []


class JobDescription(db.Model):
    __tablename__ = 'job_descriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=True)
    raw_text = db.Column(db.Text, nullable=False)
    
    # Matching breakdown
    required_skills = db.Column(db.Text, nullable=True)    # JSON list
    matching_skills = db.Column(db.Text, nullable=True)    # JSON list
    missing_skills = db.Column(db.Text, nullable=True)     # JSON list
    compatibility_score = db.Column(db.Float, default=0.0)
    recommendations = db.Column(db.Text, nullable=True)    # JSON list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='job_descriptions')
    resume = db.relationship('Resume')

    def get_required_skills(self):
        try:
            return json.loads(self.required_skills) if self.required_skills else []
        except Exception:
            return []

    def get_matching_skills(self):
        try:
            return json.loads(self.matching_skills) if self.matching_skills else []
        except Exception:
            return []

    def get_missing_skills(self):
        try:
            return json.loads(self.missing_skills) if self.missing_skills else []
        except Exception:
            return []

    def get_recommendations(self):
        try:
            return json.loads(self.recommendations) if self.recommendations else []
        except Exception:
            return []


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default='Technical')
    aliases = db.Column(db.Text, nullable=True)  # comma separated aliases

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'aliases': self.aliases
        }


class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    analysis_id = db.Column(db.Integer, db.ForeignKey('resume_analyses.id', ondelete='SET NULL'), nullable=True)
    action_type = db.Column(db.String(50), default='full_analysis')
    ats_score = db.Column(db.Float, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    pdf_report_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='history_records')
    resume = db.relationship('Resume', back_populates='history_records')
    analysis = db.relationship('ResumeAnalysis', back_populates='history_entries')


class ResumeTemplate(db.Model):
    __tablename__ = 'resume_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
