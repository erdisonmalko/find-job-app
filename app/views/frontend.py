from datetime import datetime

from flask import (Blueprint, render_template, request, 
                   current_app,redirect, url_for, flash,jsonify)
from flask import session
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc
# local
from app.models import (
    User, Person, Company, Job, 
    JobApplication, Room, Notifications,ContactMessage
)
from app import db
from app.utils.send_mail import send_contact_email, generate_token,send_email
from app.utils.validate_data import (validate_register_data, validate_login_data, is_form_empty,
                                   validate_register_company_data, validate_register_user_data)

frontend_bp = Blueprint("frontend", __name__)

# Home
@frontend_bp.route("/")
def index():
    return render_template("public/index.html")

# Jobs - feed
@frontend_bp.route("/jobs")
@login_required
def jobs():
    requested_page = request.args.get('page', 1, type=int)
    page = max(1, requested_page)
    per_page = 12

    search_for = request.args.get('search', '').strip()
    if search_for:
        base_query = Job.query.filter(Job.title.ilike(f"%{search_for}%"))
    else:
        base_query = Job.query

    jobs_pagination = base_query.order_by(desc(Job.created_at)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    jobs_list = jobs_pagination.items
    
    for job in jobs_list:
        if isinstance(current_user, Company):
            job.is_owner = job.company_id == current_user.id
        else:
            application = JobApplication.query.filter_by(
                job_id=job.id, 
                applicant_id=current_user.id
            ).first()
            job.already_applied = application is not None
        # tag of nr of applicants per job
        job.number_of_applicants = JobApplication.query.filter_by(job_id=job.id).count()
    # log
    current_app.logger.info(f"Total jobs found: {jobs_pagination.total}")
    
    return render_template(
        "jobs/jobs.html",
        active="jobs", 
        pagination=jobs_pagination,
        jobs=jobs_list,
        total_count=jobs_pagination.total,
        user=current_user
    )

# view_applications.html
@frontend_bp.route("/applications", methods=["GET"])
@login_required
def applications_page():
    # Check if current user is a Person
    if not isinstance(current_user, Person):
        flash("Only Professionals can view applications!", "info")
        return redirect(request.referrer or url_for('frontend.jobs'))
    
    # Get and sanitize parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', '').strip()

    # Base query
    base_query = db.session.query(
        Job,
        JobApplication
    ).join(
        JobApplication,
        Job.id == JobApplication.job_id
    ).filter(
        JobApplication.applicant_id == current_user.id
    )
    
    # Check if user has any applications
    applications_count = base_query.count()
    current_app.logger.info(f"Applications found: {applications_count}")
    
    if applications_count == 0:
        flash("You haven't applied to any jobs yet!", "info")
        return render_template(
            "applications/view_applications.html", 
            applications=[],
            user=current_user
        )
    # Add search filter if provided
    if search_term:
        base_query = base_query.filter(Job.title.ilike(f"%{search_term}%"))
    # Add ordering
    query = base_query.order_by(JobApplication.applied_at.desc())
    # Execute query with pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    # log
    current_app.logger.info(f"Total results: {pagination.total}")
    
    return render_template(
        "applications/view_applications.html",
        applications=pagination.items,
        pagination=pagination,
        total_count=pagination.total,
        user=current_user,
    )


#view applicants.html
@frontend_bp.route("/applicants", methods=["GET"])
@login_required
def applicants():
    # Check if current user is a Company
    if not isinstance(current_user, Company):
        flash("Only Companies can view applicants page!", "info")
        return redirect(request.referrer or url_for('frontend.jobs'))
    
    # Get and sanitize parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', '').strip()

    # Base query for jobs posted by current company
    base_query = Job.query.filter_by(company_id=current_user.id)
    
    # Apply search filter if provided
    if search_term:
        base_query = base_query.filter(Job.title.ilike(f"%{search_term}%"))
    # Order by creation date (most recent first)
    base_query = base_query.order_by(Job.created_at.desc())
    # Check if company has any jobs
    jobs_count = base_query.count()
    current_app.logger.info(f"Jobs found: {jobs_count}")
    
    if jobs_count == 0:
        flash("You haven't posted any jobs yet!", "info")
        return render_template(
            "applications/applicants.html", 
            jobs=[],
            user=current_user
        )
    
    # Paginate the results
    jobs_pagination = base_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Process each job to include its applications
    jobs_with_applications = []
    for job in jobs_pagination.items:
        applications = JobApplication.query\
            .filter_by(job_id=job.id)\
            .join(Person, JobApplication.applicant_id == Person.id)\
            .all()
        
        # Debug info for applications
        current_app.logger.info(f"Job {job.id} ({job.title}) has {len(applications)} applications")
        
        job_data = {
            "job": job,
            "applications": applications,
            "application_count": len(applications)
        }
        
        jobs_with_applications.append(job_data)
    
    return render_template(
        "applications/applicants.html",
        jobs=jobs_with_applications,
        pagination=jobs_pagination,
        search_query=search_term,
        total_count=jobs_pagination.total,
        user=current_user
    )


# show a single job details
@frontend_bp.route("/applications/view/<int:application_id>")
@login_required
def view_application(application_id):
    # Show the application page - data will be loaded via AJAX
    return render_template(
        "jobs/job.html",
        application_id=application_id,
        user=current_user
    )

# Profile
@frontend_bp.route("/profile",methods=["GET"])
@login_required
def profile():
    user_data = {
        # Base user info
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'user_type': current_user.user_type,
        'location': current_user.location,
        'created_at': current_user.created_at,
        'last_login': current_user.last_login,
        
        # Chat statistics
        'total_rooms': len(current_user.rooms_owned) + len(current_user.rooms_joined),
        'rooms_owned': len(current_user.rooms_owned),
        'rooms_joined': len(current_user.rooms_joined),
        'total_messages': len(current_user.messages),
    }

    # Add type-specific data
    if isinstance(current_user, Person):
        # Person-specific data
        user_data.update({
            'surname': current_user.surname,
            'profession': current_user.profession,
            'skills': current_user.skills or [],
            'experience': current_user.experience or [],
            'current_company_info': current_user.current_company_info or {},
            
            # Application statistics
            'total_applications': JobApplication.query.filter_by(
                applicant_id=current_user.id
            ).count(),
            'pending_applications': JobApplication.query.filter_by(
                applicant_id=current_user.id,
                status='pending'
            ).count(),
            'accepted_applications': JobApplication.query.filter_by(
                applicant_id=current_user.id,
                status='accepted'
            ).count(),
            
            # Recent activity
            'recent_applications': JobApplication.query.filter_by(
                applicant_id=current_user.id
            ).order_by(JobApplication.applied_at.desc()).limit(5).all(),
        })
        
    elif isinstance(current_user, Company):
        # Company-specific data
        user_data.update({
            'description': current_user.description,
            # Social links
            'social_links': current_user.social_links,
            # Job statistics
            'total_jobs': Job.query.filter_by(company_id=current_user.id).count(),
            'active_jobs': Job.query.filter_by(
                company_id=current_user.id,
                is_active=True
            ).count(),
            'total_applicants': JobApplication.query.join(Job).filter(
                Job.company_id == current_user.id
            ).count(),
            
            # Recent activity
            'recent_jobs': Job.query.filter_by(
                company_id=current_user.id
            ).order_by(Job.created_at.desc()).limit(5).all(),

            'recent_applications': JobApplication.query.join(Job).filter(
                Job.company_id == current_user.id
            ).order_by(JobApplication.applied_at.desc()).limit(5).all(),
        })

    return render_template(
        "profile/profile.html",
        active="profile",
        user=current_user,
        user_data=user_data,
        is_person=isinstance(current_user, Person),
        is_company=isinstance(current_user, Company)
    )


# Notifications
@frontend_bp.route("/notifications",methods=["GET"])
@login_required
def notifications():
    requested_page = request.args.get('page', 1, type=int)
    page = max(1, requested_page)
    per_page = 6

    search_for = request.args.get('search', '').strip()
    if search_for:
        base_query = Notifications.query.filter(Notifications.title.ilike(f"%{search_for}%"),Notifications.receiver_id == current_user.id)
    else:
        base_query = Notifications.query.filter(Notifications.receiver_id == current_user.id)

    # Get paginated jobs
    notifications_pagination = base_query.order_by(Notifications.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    notifications_list = notifications_pagination.items

    return render_template(
        "notifications/notifications.html",
        active="notifications", 
        pagination=notifications_pagination,
        notifications=notifications_list,
        total_count=notifications_pagination.total,
        user=current_user
    )

# Messages
@frontend_bp.route("/rooms",methods=["GET"])
@login_required
def rooms():
    requested_page = request.args.get('page', 1, type=int)
    page = max(1, requested_page)
    per_page = 6

    search_for = request.args.get('search', '').strip()
    
    # Create base query for rooms where current user is either owner or other user
    base_query = Room.query.filter(
        db.or_(
            Room.owner_id == current_user.id,
            Room.other_user_id == current_user.id
        )
    )
    
    # Add search filter if provided
    if search_for:
        base_query = base_query.filter(Room.name.ilike(f"%{search_for}%"))

    # Get paginated rooms
    rooms_pagination = base_query.order_by(Room.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    rooms_list = rooms_pagination.items
    for room in rooms_list:
        room.is_room_owner = room.owner_id == current_user.id

    return render_template(
        "dms/rooms.html",
        active="rooms", 
        pagination=rooms_pagination,
        rooms=rooms_list,
        total_count=rooms_pagination.total,
        user=current_user
    )

# Authentication
@frontend_bp.route("/users/login")
def login():
    return render_template("users/login.html", active="login")

@frontend_bp.route("/users/login", methods=["POST"])
def login_post():
    req_data = request.form

    if is_form_empty(req_data):
        flash("No data provided in the form.", "warning")
        return redirect(url_for("frontend.login"))
    
    errors = validate_login_data(req_data)
    if errors:
        for error in errors:
            flash(error, "warning")
        return redirect(url_for("frontend.login"))

    user_type = req_data.get("user_type")
    email = req_data.get("email")
    
    # Query the unified User table with type check
    user = User.query.filter_by(
        email=email,
        user_type=user_type.lower()
    ).first()

    if not user:
        flash(f"{user_type} not found.", "danger")
        return redirect(url_for("frontend.login"))

    # Check password
    if check_password_hash(user.password, req_data.get("password")):
        login_user(user, remember=req_data.get("remember", False))
        # Update the last_login variable
        user.last_login = datetime.now()
        db.session.merge(user)
        db.session.commit()
        # Store user type in the session
        session["user_type"] = user_type
        # log
        current_app.logger.info(f"Logging in the user: {user.name}")
        # return
        flash("Login successful!", "success")
        return redirect(url_for("frontend.jobs"))
    else:
        # log
        current_app.logger.error("Invalid credentials.")
        # return
        flash("Invalid credentials.", "danger")
        return redirect(url_for("frontend.login"))

@frontend_bp.route("/users/register")
def register():
    return render_template("users/register.html", active="register")

@frontend_bp.route('/register', methods=['POST'])
def register_post():
    try:
        req_data = request.form

        if is_form_empty(req_data):
            flash("No data provided in the form.", "warning")
            return redirect(url_for("frontend.register"))
            
        errors = validate_register_data(req_data)
        if errors:
            for error in errors:
                flash(error, "warning")
            return redirect(url_for("frontend.register"))

        if req_data.get("user_type") == 'Person':
            errors = validate_register_user_data(req_data)
            if errors:
                for error in errors:
                    flash(error, "warning")
                return redirect(url_for("frontend.register"))
            
            user = Person(
                email=req_data.get("email"),
                name=req_data.get("name"),
                surname=req_data.get("surname"),
                profession=req_data.get("profession"),
                location=req_data.get("location"),
                password=generate_password_hash(req_data.get("password"), method='pbkdf2')
            )
            
        elif req_data.get("user_type") == 'Company':
            errors = validate_register_company_data(req_data)
            if errors:
                for error in errors:
                    flash(error, "warning")
                return redirect(url_for("frontend.register"))
            
            user = Company(
                email=req_data.get("email"),
                name=req_data.get("name"),
                description=req_data.get("description"),
                location=req_data.get("location"),
                password=generate_password_hash(req_data.get("password"))
            )

        db.session.add(user)
        db.session.commit()
        # log
        current_app.logger.info(f"Registration successful for user: {user.name}")
        # return
        flash("Registration successful", "success")
        return redirect(url_for('frontend.login'))
        # TO DO: enable email confirmation 
        # token = generate_token(user.email)
        # confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
        # html = render_template("accounts/confirm_email.html", confirm_url=confirm_url)
        # subject = "Please confirm your email"
        # send_email(user.email, subject, html)
        # login_user(user)
        # flash("A confirmation email has been sent via email.", "success")
        # return redirect(url_for("accounts.inactive"))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {e}")
        flash('Error during registration', "danger")
        return redirect(url_for('frontend.register'))



# TO DO:
@frontend_bp.route("/inactive")
@login_required
def inactive():
    if current_user.is_confirmed:
        return redirect(url_for("core.home"))
    return render_template("accounts/inactive.html")


# TO DO:
@frontend_bp.route("/resend")
@login_required
def resend_confirmation():
    if current_user.is_confirmed:
        flash("Your account has already been confirmed.", "success")
        return redirect(url_for("core.home"))
    token = generate_token(current_user.email)
    confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
    html = render_template("accounts/confirm_email.html", confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash("A new confirmation email has been sent.", "success")
    return redirect(url_for("accounts.inactive"))


# Logout 
@frontend_bp.route("/logout")
@login_required
def logout():
    current_app.logger.info(f"User: {current_user.name} is logging out...")
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("frontend.login"))

# -------------------endpoints to handle public pages-------------
# privacy
@frontend_bp.route('/privacy')
def privacy():
    return render_template('public/privacy.html', active='privacy')


# handle new contact forms
@frontend_bp.route('/contact', methods=['POST'])
def contact_post():
    try:
        # Create new contact message
        contact = ContactMessage(
            name=request.form.get('name'),
            email=request.form.get('email'),
            subject=request.form.get('subject'),
            message=request.form.get('message'),
            created_at=datetime.now()
        )
        # Save to database
        db.session.add(contact)
        db.session.commit()
        # log
        current_app.logger.info("New contact form saved successfully")
        
        # Send email notification and return appropriate response
        if send_contact_email(contact):
            return jsonify({
                "status": "success",
                "message": "Thank you for your message! We will get back to you soon."
            })
        else:
            return jsonify({
                "status": "warning",
                "message": "Your message was received but there was an issue with email notification."
            })
 
    except Exception as e:
        current_app.logger.error(f"Error processing contact form: {e}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Sorry, there was an error sending your message."
        })