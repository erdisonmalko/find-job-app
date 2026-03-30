import re

from app.models import User, Company,Room,Message


def validate_register_user_data(req_data) -> list:
    errors = []

    # Required field checks with length validation
    if not req_data.get("surname"):
        errors.append("Surname is required.")
    elif len(req_data["surname"]) > 128:
        errors.append("Surname must be 128 characters or less.")

    if not req_data.get("profession"):
        errors.append("Profession is required.")
    elif len(req_data["profession"]) > 128:
        errors.append("Profession must be 128 characters or less.")

    # Check email exists in User table as Person
    existing_user = User.query.filter_by(
        email=req_data.get("email"),
        user_type='person'
    ).first()
    if existing_user:
        errors.append("Email already registered as Person.")

    return errors



def validate_register_company_data(req_data) -> list:
    errors = []

    # Required field checks with length validation
    if not req_data.get('description'):
        errors.append("Description is required.")
    if not req_data.get('location'):
        errors.append("Location is required.")

    # Check email exists in User table as Company
    existing_company = User.query.filter_by(
        email=req_data.get("email"),
        user_type='company'
    ).first()
    if existing_company:
        errors.append("Email already registered as Company.")

    # Check name exists for companies
    existing_name = Company.query.filter_by(name=req_data.get("name")).first()
    if existing_name:
        errors.append("Name already in use.")
        
    return errors



def validate_register_data(req_data) -> list:
    errors = []
    # Common fields for both company and person  
    if not req_data.get("user_type"):
        errors.append("User Type is required.")
    elif req_data["user_type"].lower() not in ["company", "person"]:
        errors.append("Invalid User Type chosen.")
    elif len(req_data["user_type"]) > 8:
        errors.append("Invalid User Type chosen.")

    if not req_data.get("name"):
        errors.append("Name is required.")
    elif len(req_data["name"]) > 128:
        errors.append("Name must be 128 characters or less.")
    
    if not req_data.get("email"):
        errors.append("Email is required.")
    
    if not req_data.get("password"):
        errors.append("Password is required.")

    return errors


def validate_login_data(req_data) -> list:
    errors = []
    if not req_data.get("email"):
        errors.append("Email is required.")
    if not req_data.get("password"):
        errors.append("Password is required.")
    if req_data.get("remember") is not None and req_data.get("remember").lower() not in ["on", "off"]:
        errors.append("Invalid value for remember.")
    if req_data.get("user_type").lower() not in ["company", "person"]:
        errors.append("Invalid User Type chosen.")
    return errors

def is_form_empty(req_data, exclude_keys=None) -> bool:
    exclude_keys = exclude_keys or []
    return not any(value for key, value in req_data.items() if key not in exclude_keys)



def validate_new_room_data(req_data) -> list:
    errors = []
    # room check
    if not req_data.get("name"):
        errors.append("Room name is required.")
    elif len(req_data.get("name")) > 100:
        errors.append("Invalid room name.")
    # other user id checks
    if not req_data.get("other_user_id"):
        errors.append("Please choose a user to chat with.")
    elif not req_data.get("other_user_id").isdigit():
        errors.append("Id is not of correct type.")
    else:
        # Check if other user exists in User table
        other_user = User.query.get(req_data.get("other_user_id"))
        if not other_user:
            errors.append("Selected user does not exist.")
    
    return errors

def validate_job_data(req_data) -> list:
    errors = []
    
    # Required fields check
    if not req_data.get('jobtitle'):
        errors.append("Job title is required.")
    elif len(req_data['jobtitle']) > 100:
        errors.append("Job title must be 100 characters or less.")
        
    if not req_data.get('description'):
        errors.append("Job description is required.")
    # elif len(req_data['description']) > 5000:  # Adjust max length as needed
    #     errors.append("Job description is too long.")
        
    if not req_data.get('joblocation'):
        errors.append("Job location is required.")
    elif len(req_data['joblocation']) > 100:
        errors.append("Location must be 100 characters or less.")
        
    if not req_data.get('jobsalary'):
        errors.append("Salary information is required.")
    elif len(req_data['jobsalary']) > 50:
        errors.append("Salary information must be 50 characters or less.")
    
    # Optional: Add format validation
    # Example: Ensure title doesn't contain special characters
    if req_data.get('jobtitle') and not re.match("^[a-zA-Z0-9\s\-\&\(\)]+$", req_data['jobtitle']):
        errors.append("Job title contains invalid characters.")
        
    return errors

def validate_job_update_data(req_data) -> list:
    errors = []
    
    # Required fields check
    if not req_data.get('editJobTitle'):
        errors.append("Job title is required.")
    elif len(req_data['editJobTitle']) > 100:
        errors.append("Job title must be 100 characters or less.")
        
    if not req_data.get('editJobDescription'):
        errors.append("Job description is required.")
    # elif len(req_data['editJobDescription']) > 5000:  # Adjust max length as needed
    #     errors.append("Job description is too long.")
        
    if not req_data.get('editJobLocation'):
        errors.append("Job location is required.")
    elif len(req_data['editJobLocation']) > 100:
        errors.append("Location must be 100 characters or less.")
        
    if not req_data.get('editJobSalary'):
        errors.append("Salary information is required.")
    elif len(req_data['editJobSalary']) > 50:
        errors.append("Salary information must be 50 characters or less.")
    
    # Optional: Add format validation
    # Example: Ensure title doesn't contain special characters
    if req_data.get('editJobTitle') and not re.match("^[a-zA-Z0-9\s\-\&\(\)]+$", req_data['editJobTitle']):
        errors.append("Job title contains invalid characters.")
        
    return errors
        


def validate_new_message(req_data, current_user_id: int, db=None):
    """
    Validate new message data and verify room access.
    Returns a tuple: (errors, room)
    """
    errors = []
    room_id = req_data.get('room_id')
    message_text = req_data.get("message")

    if not room_id:
        errors.append("Room id is required.")
    elif not str(room_id).isdigit():
        errors.append("Room id was invalid.")
    
    if not message_text:
        errors.append("Message key is required.")
    elif not message_text.strip():
        errors.append("No message text. Please type something.")

    # Verify room access.
    room = Room.query.filter(
        Room.id == room_id,
        db.or_(
            Room.owner_id == current_user_id,
            Room.other_user_id == current_user_id
        )
    ).first()
    if not room:
        errors.append("Access denied.")

    return errors, room


def create_new_message(room_id, sender_id, message_text,db=None):
    """
    Create a new message record in the database.
    """
    try:
        message = Message(
            room_id=room_id,
            sender_id=sender_id,
            message=message_text.strip()
        )
        db.session.add(message)
        db.session.commit()
        return message
    
    except Exception:
        db.session.rollback()
        raise