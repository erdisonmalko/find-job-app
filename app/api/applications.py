from datetime import datetime

from flask import (
    Blueprint, request, flash, redirect, url_for, 
    jsonify,send_from_directory,render_template,current_app
    )
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
# local
from app.utils.file_handler import allowed_file
from app import db
from app.extensions import limiter
from app.models import Person, Company, Job, JobApplication
from .notifications import create_notification


applications_bp = Blueprint("applications", __name__)

# here will create the api to crud applications

@applications_bp.route("/application/delete/", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def delete_application():
    application_id = request.form.get('applicationId')
    if not application_id:
        flash("An unexpected error occurred", "warning")
        return redirect(url_for('frontend.index'))
    
    # find the application and delete it - now using the unified User model
    find_application = JobApplication.query.filter_by(
        id=application_id,
        applicant_id=current_user.id
    ).first()
    
    if not find_application:
        flash("Application not found", "warning")
        return redirect(url_for('frontend.applications_page'))

    try:
        db.session.delete(find_application)
        db.session.commit()
        # log
        current_app.logger.critical(f"Deleting application {find_application.id} for user: {current_user.name}")
        # return for client
        flash("Application deleted successfully", "success")
        return redirect(url_for('frontend.applications_page'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error deleting application:", str(e))
        flash("Error deleting application", "danger")

    return redirect(url_for('frontend.applications_page'))




@applications_bp.route("/application/<int:application_id>/download_resume/<string:file_name>", methods=["GET"])
@limiter.limit("5 per minute")
@login_required
def download_resume(application_id, file_name):
    # Check if the application exists and belongs to the current user ONLY FOR PERSON
    application = JobApplication.query.filter_by(id=application_id, applicant_id=current_user.id).first()
    if not application:
        return render_template("errors/404.html"), 404
    if file_name and allowed_file(file_name):
        original_filename = secure_filename(file_name)
        current_app.logger.info(f"Downloading resume: {original_filename} for user: {current_user.name}...")
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], original_filename, as_attachment=True)

    return render_template("errors/404.html"), 404


@applications_bp.route("/application/list/<int:job_id>", methods=["GET"])
@limiter.limit("5 per minute")
@login_required
def list_applications(job_id):
    # Check if user is a Company and owns the job
    if not isinstance(current_user, Company):
        return jsonify({"error": "Unauthorized access"}), 403

    job = Job.query.filter_by(id=job_id, company_id=current_user.id).first()
    if not job:
        return jsonify({"error": "Job not found or unauthorized"}), 404

    try:
        # Get all applications for this job with applicant details
        applications = JobApplication.query\
            .filter_by(job_id=job_id)\
            .join(Person, JobApplication.applicant_id == Person.id)\
            .all()

        applications_list = []
        for app in applications:
            applications_list.append({
                "id": app.id,
                "applicant_name": app.applicant.name,
                "applicant_email": app.applicant.email,
                "resume": app.resume_filename if hasattr(app, 'resume_filename') else None,
                "applied_at": app.applied_at.strftime("%Y-%m-%d %H:%M:%S") if app.applied_at else None,
                "updated_at": app.updated_at.strftime("%Y-%m-%d %H:%M:%S") if app.updated_at else None
            })

        return jsonify({
            "applications": applications_list,
            "total": len(applications_list)
        })

    except Exception as e:
        current_app.logger.error("Error fetching applications:", str(e))
        return jsonify({"error": "Error fetching applications"}), 500




@applications_bp.route("/application/detail/<int:application_id>", methods=["GET"])
@limiter.limit("5 per minute")
@login_required
def application_detail(application_id):
    try:
        # For Person: get their own application
        # For Company: get application for their job
        if isinstance(current_user, Person):
            application = JobApplication.query\
                .filter_by(id=application_id, applicant_id=current_user.id)\
                .join(Job)\
                .join(Company, Job.company_id == Company.id)\
                .first()
        elif isinstance(current_user, Company):
            application = JobApplication.query\
                .join(Job)\
                .filter(
                    JobApplication.id == application_id,
                    Job.company_id == current_user.id
                )\
                .first()
        else:
            return jsonify({"error": "Unauthorized access"}), 403

        if not application:
            return jsonify({"error": "Application not found or unauthorized"}), 404

        # Count total applicants for this job
        total_applicants = JobApplication.query.filter_by(job_id=application.job_id).count()
        
        current_app.logger.info(f"Returning application details for application id: {application_id}")

        # Get application data with expanded details
        return jsonify({
            "id": application.id,
            "job_id": application.job_id,
            "job_title": application.job.title,
            "job_description": application.job.description,
            "job_location": application.job.location,
            "job_salary": application.job.salary,
            "job_created_at": application.job.created_at.strftime("%Y-%m-%d %H:%M:%S") if application.job.created_at else None,
            "job_is_active": application.job.is_active,
            "company_id": application.job.company_id,
            "company_name": application.job.company.name,
            "company_location": application.job.company.location,
            "applicant_id": application.applicant_id,
            "applicant_name": application.applicant.name,
            "applicant_email": application.applicant.email,
            "status": application.status,
            "resume_filename": application.resume_filename,
            # "resume_url": f"/static/resume_upload/{application.resume_filename}" if application.resume_filename else None,
            "applied_at": application.applied_at.strftime("%Y-%m-%d %H:%M:%S") if application.applied_at else None,
            "updated_at": application.updated_at.strftime("%Y-%m-%d %H:%M:%S") if application.updated_at else None,
            "total_applicants": total_applicants
        })

    except Exception as e:
        current_app.logger.error("Error fetching application details:", str(e))
        return jsonify({"error": "Error fetching application details"}), 500


# Update a job application status(ONLY FOR COMPANIES)
@applications_bp.route("/application/update_status", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def update_status():
    # Verify the current user is a Company
    if not isinstance(current_user, Company):
        flash("Only Companies can update application status", "danger")
        return redirect(url_for('frontend.jobs'))
    
    # Get form data
    application_id = request.form.get('applicationId')
    new_status = request.form.get('status')
    
    # Validate inputs
    if not application_id or not new_status:
        flash("Missing required information", "warning")
        return redirect(url_for('frontend.applicants'))
    
    # Valid status values
    valid_statuses = ['pending', 'accepted', 'rejected', 'under_review']
    if new_status not in valid_statuses:
        flash("Invalid status value", "warning")
        return redirect(url_for('frontend.applicants'))
    
    try:
        # Find the application, ensuring it belongs to a job owned by the current company
        application = JobApplication.query\
            .join(Job)\
            .filter(
                JobApplication.id == application_id,
                Job.company_id == current_user.id
            ).first()
        
        if not application:
            flash("Application not found or not authorized", "warning")
            return redirect(url_for('frontend.applicants'))
        
        # Update the status
        application.status = new_status
        application.updated_at = datetime.now()
        db.session.commit()
        
        # Get applicant name for the success message
        applicant_name = application.applicant.name
        job_title = application.job.title
        # log
        current_app.logger.info(f"Status for application {job_title}, applicant name: {applicant_name}")
        # send notification to applicant
        notification_message = f"Status for your application for '{job_title}' at {application.job.company.name} updated to {new_status.capitalize()}. application_id: {application_id}"
        create_notification(application.applicant_id, notification_message, emit_notification=True)
        # return a success message for the company
        flash(f"Status for {applicant_name}'s application to '{job_title}' updated to {new_status.capitalize()}", "success")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error updating application status:", str(e))
        flash("Error updating application status", "danger")
    
    return redirect(url_for('frontend.applicants'))



# ------------------------------------------------------------------------

#NOT NEEDED - TOO COMPLICATED TO HANDLE
# @applications_bp.route("/application/update/", methods=["POST"])
# @login_required
# def update_application():
#     print(f"Request form on update application: {request.form}")
#     print(f"Request files on update application: {request.files}")
    
#     if not isinstance(current_user, Person) or not current_user.can_apply_to_job():
#         flash("Only Professionals can update applications", "danger")
#         return redirect(url_for('frontend.applications_page'))

#     application_id = request.form.get('applicationId')
#     if not application_id:
#         flash("An unexpected error occurred", "warning")
#         return redirect(url_for('frontend.index'))

#     application = JobApplication.query.filter_by(
#         id=application_id,
#         applicant_id=current_user.id
#     ).first()

#     if not application:
#         flash("Application not found", "warning")
#         return redirect(url_for('frontend.applications_page'))
    
#     try:
#         if 'resume' in request.files:
#             unique_filename, file_url = save_resume(request.files.get('resume'))
#             print(f"Saved file as {unique_filename}, URL: {file_url}")
#             if unique_filename:
#                 application.resume_filename = unique_filename
#             else:
#                 flash("Error saving resume file", "danger")
#                 return redirect(url_for('frontend.applications_page'))
        
#         application.updated_at = datetime.now()
#         db.session.commit()
#         flash("Application updated successfully", "success")
#         return redirect(url_for('frontend.applications_page'))
#     except Exception as e:
#         db.session.rollback()
#         print("Error updating application:", str(e))
#         flash("Error updating application", "danger")

#     return redirect(url_for('frontend.applications_page'))


# @applications_bp.route("/application/upload_resume/<string:file_name>", methods=["POST"])
# @login_required
# def upload_resume(file_name):
#     pass