import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.database import db
from app.models import User, Resume, ResumeAnalysis, JobDescription, Skill, AnalysisHistory, ResumeTemplate
from app.forms import ResumeUploadForm, JobMatchForm, AIRewriteForm
from app.resume_parser import extract_text, parse_resume
from app.analysis import perform_full_analysis, generate_pdf_report
from app.ai_service import AIService
from app.resume_builder import build_resume_pdf

main_bp = Blueprint('routes', __name__)


# -------------------------------------------------------------
# Home & Public Routes
# -------------------------------------------------------------
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    return render_template('index.html')


# -------------------------------------------------------------
# Dashboard
# -------------------------------------------------------------
@main_bp.route('/dashboard')
@login_required
def dashboard():
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).all()
    analyses = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.created_at.desc()).all()

    total_resumes = len(resumes)
    total_analyses = len(analyses)
    
    latest_analysis = analyses[0] if analyses else None
    latest_score = latest_analysis.ats_score if latest_analysis else 0.0

    avg_score = round(sum(a.ats_score for a in analyses) / total_analyses, 1) if total_analyses > 0 else 0.0

    # Collect skill distribution for Chart.js
    skill_categories_count = {}
    if latest_analysis and latest_analysis.resume:
        parsed = latest_analysis.resume.parsed
        cats = parsed.get('skills', {}).get('categorized', {})
        for cat, slist in cats.items():
            skill_categories_count[cat] = len(slist)

    # Recent 5 analyses for the dashboard table
    recent_analyses = analyses[:5]

    return render_template(
        'dashboard.html',
        total_resumes=total_resumes,
        total_analyses=total_analyses,
        latest_score=latest_score,
        avg_score=avg_score,
        latest_analysis=latest_analysis,
        recent_analyses=recent_analyses,
        skill_categories_count=skill_categories_count,
        resumes=resumes
    )


# -------------------------------------------------------------
# Resume Management (Upload, List, Delete)
# -------------------------------------------------------------
@main_bp.route('/resume/upload', methods=['GET', 'POST'])
@login_required
def upload_resume():
    form = ResumeUploadForm()
    if form.validate_on_submit():
        file = form.resume_file.data
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if ext not in current_app.config['ALLOWED_EXTENSIONS']:
            flash('Invalid file format. Please upload a PDF or DOCX file.', 'danger')
            return redirect(request.url)

        # Unique file naming
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        try:
            # Extract and parse
            raw_text = extract_text(file_path)
            if not raw_text.strip():
                flash('The uploaded resume appears to be empty or unscannable. Please check the document.', 'warning')
                return redirect(request.url)

            parsed_data = parse_resume(raw_text)

            # Create Resume record
            resume = Resume(
                user_id=current_user.id,
                title=form.title.data.strip(),
                filename=filename,
                file_path=file_path,
                file_type=ext,
                file_size=file_size,
                raw_text=raw_text
            )
            resume.parsed = parsed_data
            db.session.add(resume)
            db.session.flush()

            # Automatically run ATS analysis
            analysis_data = perform_full_analysis(
                raw_text=raw_text,
                parsed_data=parsed_data,
                gemini_api_key=current_app.config.get('GEMINI_API_KEY')
            )
            scores = analysis_data['scores']

            analysis = ResumeAnalysis(
                resume_id=resume.id,
                user_id=current_user.id,
                ats_score=scores['ats_score'],
                skills_score=scores['skills_score'],
                formatting_score=scores['formatting_score'],
                keyword_score=scores['keyword_score'],
                content_quality_score=scores['content_quality_score'],
                completeness_score=scores['completeness_score'],
                detailed_feedback=json.dumps(scores),
                recommendations=json.dumps(analysis_data['recommendations']),
                strengths=json.dumps(analysis_data['strengths']),
                weaknesses=json.dumps(analysis_data['weaknesses']),
                action_verbs_found=json.dumps(analysis_data['action_verbs_found'])
            )
            db.session.add(analysis)
            db.session.flush()

            # Record in Analysis History
            history = AnalysisHistory(
                user_id=current_user.id,
                resume_id=resume.id,
                analysis_id=analysis.id,
                action_type='full_analysis',
                ats_score=scores['ats_score'],
                summary=f"Analyzed {resume.title}: ATS Score {scores['ats_score']}/100"
            )
            db.session.add(history)
            db.session.commit()

            flash('Resume uploaded and analyzed successfully!', 'success')
            return redirect(url_for('routes.view_analysis', id=analysis.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error("Error processing resume upload: %s", e)
            flash(f'An error occurred while parsing the resume: {str(e)}', 'danger')
            return redirect(request.url)

    return render_template('upload_resume.html', form=form)


@main_bp.route('/resume/list')
@login_required
def list_resumes():
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).all()
    return render_template('resume_list.html', resumes=resumes)


@main_bp.route('/resume/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_resume(id):
    resume = Resume.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
    except Exception as e:
        current_app.logger.warning("Could not delete file %s: %s", resume.file_path, e)

    db.session.delete(resume)
    db.session.commit()
    flash('Resume and associated analysis data deleted successfully.', 'info')
    return redirect(url_for('routes.dashboard'))


# -------------------------------------------------------------
# Analysis Routes
# -------------------------------------------------------------
@main_bp.route('/analysis')
@login_required
def analysis_overview():
    latest = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.created_at.desc()).first()
    if latest:
        return redirect(url_for('routes.view_analysis', id=latest.id))
    flash('No resumes analyzed yet. Please upload a resume to start analysis.', 'info')
    return redirect(url_for('routes.upload_resume'))


@main_bp.route('/analysis/<int:id>')
@login_required
def view_analysis(id):
    analysis = ResumeAnalysis.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    parsed = analysis.resume.parsed if analysis.resume else {}

    return render_template(
        'analysis.html',
        analysis=analysis,
        parsed=parsed,
        feedback=analysis.get_feedback(),
        strengths=analysis.get_strengths(),
        weaknesses=analysis.get_weaknesses(),
        recommendations=analysis.get_recommendations(),
        action_verbs=analysis.get_action_verbs()
    )


@main_bp.route('/analysis/job-match', methods=['GET', 'POST'])
@login_required
def job_match():
    user_resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).all()
    if not user_resumes:
        flash('Please upload a resume first before running job description matching.', 'warning')
        return redirect(url_for('routes.upload_resume'))

    form = JobMatchForm()
    form.resume_id.choices = [(r.id, f"{r.title} ({r.filename})") for r in user_resumes]

    match_result = None

    if form.validate_on_submit():
        selected_resume = Resume.query.filter_by(id=form.resume_id.data, user_id=current_user.id).first_or_404()
        parsed = selected_resume.parsed
        resume_skills = parsed.get('skills', {}).get('all', [])

        ai_service = AIService(api_key=current_app.config.get('GEMINI_API_KEY'))
        match_result = ai_service.match_job_description(
            resume_text=selected_resume.raw_text,
            resume_skills=resume_skills,
            job_text=form.job_description.data
        )

        # Save record in database
        job_record = JobDescription(
            user_id=current_user.id,
            resume_id=selected_resume.id,
            title=form.title.data.strip(),
            company=form.company.data.strip() if form.company.data else None,
            raw_text=form.job_description.data.strip(),
            required_skills=json.dumps(match_result['required_skills']),
            matching_skills=json.dumps(match_result['matching_skills']),
            missing_skills=json.dumps(match_result['missing_skills']),
            compatibility_score=match_result['compatibility_score'],
            recommendations=json.dumps(match_result['recommendations'])
        )
        db.session.add(job_record)

        # Also log to history
        history = AnalysisHistory(
            user_id=current_user.id,
            resume_id=selected_resume.id,
            action_type='job_match',
            ats_score=match_result['compatibility_score'],
            summary=f"Matched against '{form.title.data}': {match_result['compatibility_score']}% compatibility"
        )
        db.session.add(history)
        db.session.commit()

        flash(f"Job match completed! Compatibility Score: {match_result['compatibility_score']}%", 'success')

    return render_template('job_match.html', form=form, match_result=match_result, resumes=user_resumes)


@main_bp.route('/analysis/improve', methods=['GET', 'POST'])
@login_required
def improve_resume():
    form = AIRewriteForm()
    rewrite_result = None

    if form.validate_on_submit():
        ai_service = AIService(api_key=current_app.config.get('GEMINI_API_KEY'))
        rewrite_result = ai_service.rewrite_content(
            section_type=form.section_type.data,
            content=form.content.data,
            target_role=form.target_role.data
        )

    return render_template('improvement.html', form=form, rewrite_result=rewrite_result)


# -------------------------------------------------------------
# Resume Builder
# -------------------------------------------------------------
@main_bp.route('/resume-builder')
@login_required
def resume_builder():
    templates = ResumeTemplate.query.filter_by(is_active=True).all()
    # Provide default templates if table is empty
    if not templates:
        t1 = ResumeTemplate(name='Classic ATS', slug='classic-ats', description='Single column, highly readable font hierarchy, timeless ATS standard.')
        t2 = ResumeTemplate(name='Modern Tech', slug='modern-tech', description='Indigo accent bars, clean developer skill blocks, optimized for engineering.')
        t3 = ResumeTemplate(name='Minimalist Executive', slug='minimalist-executive', description='Streamlined slate design, refined dividers, high executive impact.')
        db.session.add_all([t1, t2, t3])
        db.session.commit()
        templates = [t1, t2, t3]

    return render_template('resume_builder.html', templates=templates, user=current_user)


@main_bp.route('/resume-builder/create', methods=['POST'])
@login_required
def create_builder_resume():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Parse nested structure if submitted from JSON
        if request.is_json:
            resume_data = data
        else:
            # Reconstruct form fields
            resume_data = {
                'full_name': request.form.get('full_name', current_user.name),
                'email': request.form.get('email', current_user.email),
                'phone': request.form.get('phone', ''),
                'location': request.form.get('location', ''),
                'linkedin': request.form.get('linkedin', ''),
                'github': request.form.get('github', ''),
                'portfolio': request.form.get('portfolio', ''),
                'summary': request.form.get('summary', ''),
                'skills': request.form.get('skills', ''),
                'experiences': [],
                'projects': [],
                'education': [],
                'certifications': request.form.get('certifications', ''),
                'template': request.form.get('template', 'classic-ats')
            }

            # Gather dynamic experiences
            exp_roles = request.form.getlist('exp_role[]')
            exp_companies = request.form.getlist('exp_company[]')
            exp_durations = request.form.getlist('exp_duration[]')
            exp_locations = request.form.getlist('exp_location[]')
            exp_descriptions = request.form.getlist('exp_description[]')
            for i in range(len(exp_roles)):
                if exp_roles[i].strip():
                    resume_data['experiences'].append({
                        'role': exp_roles[i],
                        'company': exp_companies[i] if i < len(exp_companies) else '',
                        'duration': exp_durations[i] if i < len(exp_durations) else '',
                        'location': exp_locations[i] if i < len(exp_locations) else '',
                        'description': exp_descriptions[i] if i < len(exp_descriptions) else ''
                    })

            # Gather dynamic projects
            proj_titles = request.form.getlist('proj_title[]')
            proj_techs = request.form.getlist('proj_tech[]')
            proj_links = request.form.getlist('proj_link[]')
            proj_descriptions = request.form.getlist('proj_description[]')
            for i in range(len(proj_titles)):
                if proj_titles[i].strip():
                    resume_data['projects'].append({
                        'title': proj_titles[i],
                        'technologies': proj_techs[i] if i < len(proj_techs) else '',
                        'link': proj_links[i] if i < len(proj_links) else '',
                        'description': proj_descriptions[i] if i < len(proj_descriptions) else ''
                    })

            # Gather dynamic education
            edu_degrees = request.form.getlist('edu_degree[]')
            edu_schools = request.form.getlist('edu_school[]')
            edu_years = request.form.getlist('edu_year[]')
            edu_scores = request.form.getlist('edu_score[]')
            for i in range(len(edu_degrees)):
                if edu_degrees[i].strip():
                    resume_data['education'].append({
                        'degree': edu_degrees[i],
                        'institution': edu_schools[i] if i < len(edu_schools) else '',
                        'year': edu_years[i] if i < len(edu_years) else '',
                        'score': edu_scores[i] if i < len(edu_scores) else ''
                    })

        # Generate PDF
        reports_dir = current_app.config['REPORT_FOLDER']
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"built_resume_{uuid.uuid4().hex[:8]}.pdf"
        output_path = os.path.join(reports_dir, filename)

        build_resume_pdf(resume_data, output_path, template=resume_data.get('template', 'classic-ats'))

        # Also store as an uploaded Resume entity so the user can immediately analyze it
        raw_text = extract_text(output_path)
        parsed_data = parse_resume(raw_text)

        new_resume = Resume(
            user_id=current_user.id,
            title=f"Built Resume - {resume_data.get('full_name', 'Custom')}",
            filename=filename,
            file_path=output_path,
            file_type='pdf',
            file_size=os.path.getsize(output_path),
            raw_text=raw_text
        )
        new_resume.parsed = parsed_data
        db.session.add(new_resume)
        db.session.commit()

        if request.is_json:
            return jsonify({
                'success': True,
                'resume_id': new_resume.id,
                'download_url': url_for('routes.download_built_resume', id=new_resume.id)
            })

        flash('Resume built and compiled successfully! You can download it below or review its ATS score.', 'success')
        return redirect(url_for('routes.download_built_resume', id=new_resume.id))

    except Exception as e:
        current_app.logger.error("Error generating resume PDF: %s", e)
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f"Failed to generate resume: {str(e)}", 'danger')
        return redirect(url_for('routes.resume_builder'))


@main_bp.route('/resume-builder/download/<int:id>')
@login_required
def download_built_resume(id):
    resume = Resume.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if not os.path.exists(resume.file_path):
        flash('Resume file not found.', 'danger')
        return redirect(url_for('routes.resume_builder'))

    return send_file(
        resume.file_path,
        as_attachment=True,
        download_name=f"{secure_filename(resume.title)}.pdf",
        mimetype='application/pdf'
    )


# -------------------------------------------------------------
# History Routes
# -------------------------------------------------------------
@main_bp.route('/history')
@login_required
def history():
    history_records = AnalysisHistory.query.filter_by(user_id=current_user.id).order_by(AnalysisHistory.created_at.desc()).all()
    return render_template('history.html', history_records=history_records)


@main_bp.route('/history/download/<int:id>')
@login_required
def download_report(id):
    analysis = ResumeAnalysis.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    reports_dir = current_app.config['REPORT_FOLDER']
    os.makedirs(reports_dir, exist_ok=True)
    report_file = os.path.join(reports_dir, f"ATS_Report_{analysis.id}.pdf")

    # Generate if not exists
    generate_pdf_report(analysis, report_file)

    return send_file(
        report_file,
        as_attachment=True,
        download_name=f"ATS_Report_{secure_filename(analysis.resume.title if analysis.resume else 'Resume')}.pdf",
        mimetype='application/pdf'
    )


@main_bp.route('/history/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_history(id):
    rec = AnalysisHistory.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(rec)
    db.session.commit()
    flash('Analysis history record deleted successfully.', 'info')
    return redirect(url_for('routes.history'))


# -------------------------------------------------------------
# Admin Dashboard & User Management
# -------------------------------------------------------------
@main_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access restricted to administrators.', 'danger')
        return redirect(url_for('routes.dashboard'))

    total_users = User.query.count()
    total_resumes = Resume.query.count()
    total_analyses = ResumeAnalysis.query.count()
    total_jobs = JobDescription.query.count()

    users = User.query.order_by(User.created_at.desc()).all()
    latest_resumes = Resume.query.order_by(Resume.uploaded_at.desc()).limit(10).all()

    # System-wide average ATS score
    all_scores = [a.ats_score for a in ResumeAnalysis.query.all()]
    system_avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_resumes=total_resumes,
        total_analyses=total_analyses,
        total_jobs=total_jobs,
        system_avg_score=system_avg_score,
        users=users,
        latest_resumes=latest_resumes
    )


@main_bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access restricted to administrators.', 'danger')
        return redirect(url_for('routes.dashboard'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)


@main_bp.route('/admin/users/toggle/<int:id>', methods=['POST'])
@login_required
def toggle_user_role(id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot demote yourself.', 'warning')
        return redirect(url_for('routes.admin_users'))

    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f"User {user.name}'s role updated to {user.role.upper()}.", 'success')
    return redirect(url_for('routes.admin_users'))


@main_bp.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('routes.admin_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.name} has been permanently deleted.", 'info')
    return redirect(url_for('routes.admin_users'))
