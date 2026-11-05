from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=64)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Create Account')


class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    target_role = StringField('Target Job Role (e.g., Senior Full Stack Developer)', validators=[Optional(), Length(max=120)])
    bio = TextAreaField('Professional Headline & Bio', validators=[Optional(), Length(max=500)])
    new_password = PasswordField('New Password (leave blank to keep current)', validators=[Optional(), Length(min=6)])
    submit = SubmitField('Update Profile')


class ResumeUploadForm(FlaskForm):
    title = StringField('Resume Title (e.g., Software Engineer 2026)', validators=[DataRequired(), Length(max=200)])
    resume_file = FileField('Upload Resume (PDF or DOCX)', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'docx'], 'Only PDF and DOCX files are allowed.')
    ])
    submit = SubmitField('Upload and Analyze')


class JobMatchForm(FlaskForm):
    resume_id = SelectField('Select Resume', coerce=int, validators=[DataRequired()])
    title = StringField('Job Title (e.g., Backend Python Engineer)', validators=[DataRequired(), Length(max=200)])
    company = StringField('Company Name (Optional)', validators=[Optional(), Length(max=200)])
    job_description = TextAreaField('Job Description Text', validators=[DataRequired(), Length(min=30)])
    submit = SubmitField('Compare & Match ATS Skills')


class AIRewriteForm(FlaskForm):
    section_type = SelectField('Section to Improve', choices=[
        ('Professional Summary', 'Professional Summary'),
        ('Work Experience Bullet Points', 'Work Experience Bullet Points'),
        ('Project Descriptions', 'Project Descriptions')
    ], validators=[DataRequired()])
    target_role = StringField('Target Role / Specialization', validators=[Optional()])
    content = TextAreaField('Original Content', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('AI Enhance & Polish')
