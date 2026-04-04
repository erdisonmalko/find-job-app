from datetime import datetime

from flask import Blueprint, request, redirect, url_for, jsonify,render_template,current_app
from flask_login import logout_user
from flask_login import login_required, current_user
# local
from app import db
from app.extensions import  limiter
from app.models import Person, Company, User, Room, Notifications

profiles_bp = Blueprint("profiles", __name__)

# here will add rest api to edit profile

# endpoint to show profile to visitors
@profiles_bp.route("/view/<int:user_id>", methods=["GET"])
@limiter.limit("30 per minute")
@login_required
def visit_profile(user_id):
    # Find the user by ID
    user = User.query.get_or_404(user_id)
    
    # If user wants to see their own profile, redirect to profile page
    if user_id == current_user.id:
        return redirect(url_for('frontend.profile'))
    
    # Prepare the base user data
    user_data = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'location': user.location or 'No location set',
        'user_type': user.user_type
    }

    # Add type-specific data
    if isinstance(user, Person):
        user_data.update({
            'surname': user.surname,
            'profession': user.profession or 'Not specified',
            'skills': user.skills or [],
            'experience': user.experience or [],
            'current_company_info': user.current_company_info or {}
        })
        template = 'profile/visit_person_profile.html'
        
    elif isinstance(user, Company):
        user_data.update({
            'description': user.description or 'No description available',
            'social_links': user.social_links or {}
        })
        template = 'profile/visit_company_profile.html'
    # log
    current_app.logger.info(f"Visiting {user_data['name']}'s profile")
    
    return render_template(
        template,
        user=current_user,
        user_data=user_data,
        is_person=isinstance(user, Person),
        is_company=isinstance(user, Company)
    )


# showing all experiences of a person(for person them selfs and other visitors)
@profiles_bp.route("/experiences/<int:user_id>", methods=["GET"])
@limiter.limit("30 per minute")
@login_required
def all_experiences(user_id):

    user = Person.query.get_or_404(user_id)
    
    user_data = {
        'id': user.id,
        'name': user.name,
        'experience': user.experience or []
    }
    # log
    current_app.logger.info(f"User {current_user.id} requested to view profile of user: {user_id}")
    
    return render_template(
        'profile/all_experience.html',
        user=current_user,
        user_data=user_data
    )



# 1. Basic Profile Edit (shared data)
@profiles_bp.route("/edit/basic/<int:user_id>", methods=["POST"])
@limiter.limit("20 per minute")
@login_required
def edit_basic_profile(user_id):
    if user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'You can only edit your own profile'
        }), 403
    
    try:
        data = request.json
        user = User.query.get_or_404(user_id)
        
        # Update common fields
        if 'name' in data:
            user.name = data['name']
        if 'location' in data:
            user.location = data['location']
        if 'email' in data:
            user.email = data['email']
            
        # Person-specific basic fields
        if isinstance(user, Person) and 'surname' in data:
            user.surname = data['surname']
        if isinstance(user, Person) and 'profession' in data:
            user.profession = data['profession']
            
        user.updated_at = datetime.now()
        db.session.commit()
        # log
        current_app.logger.info(f"{user.name}'s basic profile info updated")

        return jsonify({
            'status': 'success',
            'message': 'Basic profile information updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.critical(f"Error updating basic profile info for user {user_id or None}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 2. Company Social Links
@profiles_bp.route("/edit/social-links/<int:user_id>", methods=["POST"])
@limiter.limit("20 per minute")
@login_required
def edit_social_links(user_id):
    if user_id != current_user.id or not isinstance(current_user, Company):
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized access'
        }), 403
    
    try:
        data = request.json
        company = Company.query.get_or_404(user_id)
        
        if 'social_links' in data and isinstance(data['social_links'], dict):
            company.social_links = data['social_links']
            company.updated_at = datetime.now()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Social links updated successfully'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500



# 3. Person Professional Info - Split into separate endpoints
@profiles_bp.route("/edit/skills/<int:user_id>", methods=["POST"])
@limiter.limit("20 per minute")
@login_required
def edit_skills(user_id):
    if user_id != current_user.id or not isinstance(current_user, Person):
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized access'
        }), 403
    
    try:
        data = request.json
        person = Person.query.get_or_404(user_id)
        
        # Handle skills update
        if 'skills' in data and isinstance(data['skills'], list):
            person.skills = data['skills']
            person.updated_at = datetime.now()
            db.session.commit()
            
            current_app.logger.info(f"Updated skills for profile {person.name}")
            return jsonify({
                'status': 'success',
                'message': 'Skills updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid skills data format'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating skills. Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@profiles_bp.route("/edit/experience/<int:user_id>", methods=["POST"])
@limiter.limit("20 per minute")
@login_required
def edit_experience(user_id):
    if user_id != current_user.id or not isinstance(current_user, Person):
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized access'
        }), 403
    
    try:
        data = request.json
        person = Person.query.get_or_404(user_id)
        
        # Handle experience update
        if 'experience' in data and isinstance(data['experience'], list):
            # list comprehension 
            all_experience = [
                {
                    'title': exp.get('title', ''),
                    'company': exp.get('company', ''),
                    'description': exp.get('description', ''),
                    'start_date': exp.get('start_date', ''),
                    'end_date': exp.get('end_date', '')
                }
                for exp in data['experience']
            ]
            person.experience = all_experience
            person.updated_at = datetime.now()
            db.session.commit()
            
            current_app.logger.info(f"Updated experience for profile {person.name}")
            return jsonify({
                'status': 'success',
                'message': 'Experience updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid experience data format'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating experience. Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@profiles_bp.route("/edit/current-company/<int:user_id>", methods=["POST"])
@limiter.limit("20 per minute")
@login_required
def edit_current_company(user_id):
    if user_id != current_user.id or not isinstance(current_user, Person):
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized access'
        }), 403
    
    try:
        data = request.json
        person = Person.query.get_or_404(user_id)
        
        # Handle current company info update
        if 'current_company_info' in data and isinstance(data['current_company_info'], dict):
            person.current_company_info = {
                'company': data['current_company_info'].get('company', ''),
                'title': data['current_company_info'].get('title', '')
            }
            person.updated_at = datetime.now()
            db.session.commit()
            
            current_app.logger.info(f"Updated current company info for profile {person.name}")
            return jsonify({
                'status': 'success',
                'message': 'Current company information updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid current company data format'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating current company info. Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# DANGER ZONE
# delete profile
@profiles_bp.route("/delete/<int:user_id>", methods=["POST"])
@limiter.limit("5 per minute")
@login_required
def delete_account(user_id):
    if user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized access'
        }), 403
    
    try:
        user = User.query.get_or_404(user_id)
        current_app.logger.info(f"Deleting account id: {user.name}")
        # Begin transaction
        db.session.begin_nested()
        
        # Handle rooms (not cascaded)
        Room.query.filter(
            db.or_(
                Room.owner_id == user_id,
                Room.other_user_id == user_id
            )
        ).delete(synchronize_session=False)
        
        # Delete notifications (if any)
        Notifications.query.filter_by(receiver_id=user_id).delete()
        
        # Delete the user (this will trigger cascades)
        db.session.delete(user)
        
        # Commit all changes
        db.session.commit()
        current_app.logger.critical(f"Profile deleted successfully, for user: {user.name}")
        # Log the user out
        logout_user()
        
        return jsonify({
            'status': 'success',
            'message': 'User deleted successfully'
        })
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting profile. Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500