from datetime import datetime

from flask import Blueprint, request, flash, redirect, url_for, jsonify,current_app
from flask_login import login_required, current_user
# local
from app.utils.file_handler import save_resume
from app import db
from app.extensions import limiter
from app.models import  Company, Person, Job, JobApplication
from .notifications import create_notification
from app.utils.validate_data import is_form_empty,validate_job_data,validate_job_update_data

jobs_bp = Blueprint("jobs", __name__)

# Create a new job
@jobs_bp.route("/job/create", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def create_job():
    try:
        if is_form_empty(request.form):
            flash("No data provided in the form.", "warning")
            return redirect(request.referrer or url_for('frontend.jobs'))
        # check the data received - if valid
        errors = validate_job_data(request.form)
        if errors:
            for error in errors:
                flash(error, "warning")
            return redirect(request.referrer or url_for('frontend.jobs'))
        # Check if current user is a company using the new model structure
        if not isinstance(current_user, Company) or not current_user.can_create_job():
            flash("Only companies can create a job", "danger")
            return redirect(request.referrer or url_for('frontend.jobs'))
        
        current_app.logger.info(f"Description Length: {len(request.form.get('description'))}")
        # Create new job with company_id
        new_job = Job(
            title=request.form.get('jobtitle'),
            description=request.form.get('description'),
            location=request.form.get('joblocation'),
            salary=request.form.get('jobsalary'),
            company_id=current_user.id  # Now using the unified ID from User table
        )

        # Add and commit to database
        db.session.add(new_job)
        db.session.commit()
        current_app.logger.info(f"User: {current_user.name} created a job successfully")
        flash("Job created successfully", "success")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error creating job:", str(e))
        flash("Error creating job", "danger")

    return redirect(request.referrer or url_for('frontend.jobs'))

# job detail
@jobs_bp.route("/job/info/<int:job_id>", methods=["GET"])
@login_required
def job_detail(job_id):
    job = Job.query.filter_by(id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"})

    current_app.logger.info(f"Returning details for job is: {job_id}")

    return jsonify({
        "job_id": job.id,
        "title": job.title,
        "description": job.description,
        "location": job.location,
        "salary": job.salary,
        "company_id": job.company_id,
        "created_at": job.created_at,
        "updated_at": job.updated_at
    })

# Update job
@jobs_bp.route("/job/update/", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def update_job():
    # Check if current user is a company
    if not isinstance(current_user, Company) or not current_user.can_create_job():
        flash("Only companies can update jobs", "danger")
        return redirect(request.referrer or url_for('frontend.jobs'))

    job_id = request.form.get('editJobId')
    if not job_id:
        flash("An unexpected error occurred", "warning")
        return redirect(url_for('frontend.index'))

    # make sure job exists and belongs to the current company
    job = Job.query.filter_by(company_id=current_user.id, id=job_id).first()
    if not job:
        flash("Can not update this job - either not under this company or does not exist", "danger")
        return redirect(request.referrer or url_for('frontend.jobs'))

    try:
        # Validate update data
        errors = validate_job_update_data(request.form)
        if errors:
            for error in errors:
                flash(error, "warning")
            return redirect(request.referrer or url_for('frontend.jobs'))

        # Update with validated and sanitized data
        job.title = request.form.get('editJobTitle').strip()
        job.description = request.form.get('editJobDescription').strip()
        job.location = request.form.get('editJobLocation').strip()
        job.salary = request.form.get('editJobSalary').strip()
        job.updated_at = datetime.now()

        db.session.commit()
        current_app.logger.info(f"Job: {job.title} updated successfully")

        flash("Job updated successfully", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error updating job:", str(e))
        flash("Error updating job", "danger")

    return redirect(request.referrer or url_for('frontend.jobs'))


# deactivate job
@jobs_bp.route("/job/deactivate/<int:job_id>", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def deactivate_job(job_id):
    # Check if current user is a company
    if not isinstance(current_user, Company) or not current_user.can_create_job():
        return jsonify({"error": "Only companies can update jobs"}), 403

    # make sure job exists and belongs to the current company
    job = Job.query.filter_by(company_id=current_user.id, id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found or unauthorized"}), 404
    
    try:
        # Get new status from form data (active=true or active=false)
        active = request.form.get('active', 'false').lower() == 'true'
        
        # Update job status
        job.is_active = active
        job.updated_at = datetime.now()
        db.session.commit()
        # log
        current_app.logger.warning(f"Deactivating job: {job_id}")
        status_text = "activated" if active else "deactivated"
        return jsonify({
            "success": True,
            "message": f"Job {status_text} successfully",
            "is_active": job.is_active
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error updating job status:", str(e))
        return jsonify({"error": "Error updating job status"}), 500


# delete job
@jobs_bp.route("/job/delete/", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def delete_job():
    job_id = request.form.get("jobId")
    if not job_id:
        flash("An unexpected error occurred", "warning")
        return redirect(url_for('frontend.index'))

    # make sure job exists and belongs to the current company
    job = Job.query.filter_by(company_id=current_user.id, id=job_id).first()
    if not job:
        flash("Can not delete this job - either not under this company or does not exist", "danger")
        return redirect(url_for('frontend.jobs'))

    try:
        db.session.delete(job)
        db.session.commit()
        current_app.logger.warning(f"Job: {job.title} deleted successfully")
        flash("Job deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error deleting job:", str(e))
        flash("Error deleting job", "danger")

    return redirect(request.referrer or url_for('frontend.jobs'))

# Apply for a job
@jobs_bp.route("/job/apply/<int:job_id>", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def apply_job(job_id):
    # Check if job exists
    job = Job.query.filter_by(id=job_id, is_active=True).first()
    if not job:
        return jsonify({"error": "Job not found or inactive"}), 404
    
    # Check if the user is a Person and can apply
    if not isinstance(current_user, Person) or not current_user.can_apply_to_job():
        return jsonify({"error": "Only Professionals can apply for jobs."}), 409

    #check if a file is provided in the request object
    if 'resume' not in request.files:
            return jsonify({"error": "Resume file not provided"}), 500
    
    # Check if already applied
    already_applied = JobApplication.query.filter_by(
        job_id=job.id,
        applicant_id=current_user.id,
    ).first()

    if already_applied is not None:
        return jsonify({"error": "You have already applied for this job"}), 409
    
    try:
        # Add application with timestamp
        application = JobApplication(
            applicant_id=current_user.id,
            job_id=job_id,
            applied_at=datetime.now()
        )
        
        unique_filename = save_resume(request.files.get('resume'))
        if unique_filename:
            application.resume_filename = unique_filename
    
        db.session.add(application)
        db.session.commit()
        current_app.logger.info(f"{current_user.name} {current_user.surname} applied for job: {job.title} successfully")
        # Create a notification for the company receiving the application
        notification_message = f"{current_user.name} {current_user.surname} applied for your job '{job.title}'"
        create_notification(job.company_id, notification_message, emit_notification=True)

        return jsonify({"message": "Application submitted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error applying for job:", str(e))
        return jsonify({"error": "Error applying for job"}), 500

    