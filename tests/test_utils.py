import pytest

from app import db
from app.utils.validate_data import (
    validate_job_data,
    validate_new_room_data,
)


@pytest.mark.unit
class TestJobValidation:
    """Test job validation utility."""
    
    def test_validate_job_data_success(self, app):
        """Test successful job data validation."""
        with app.app_context():
            data = {
                'jobtitle': 'Senior Developer',
                'description': 'We are looking for...',
                'joblocation': 'New York',
                'jobsalary': '$100k-$150k'
            }
            errors = validate_job_data(data)
            assert errors == []
    
    def test_validate_job_data_missing_title(self, app):
        """Test validation fails with missing title."""
        with app.app_context():
            data = {
                'description': 'Description',
                'joblocation': 'NYC',
                'jobsalary': '$100k'
            }
            errors = validate_job_data(data)
            assert len(errors) > 0
    
    def test_validate_job_data_empty_fields(self, app):
        """Test validation fails with empty fields."""
        with app.app_context():
            data = {
                'jobtitle': '',
                'description': '',
                'joblocation': '',
                'jobsalary': ''
            }
            errors = validate_job_data(data)
            assert len(errors) > 0


@pytest.mark.unit
class TestRoomValidation:
    """Test room (messaging) validation."""
    
    def test_validate_room_data_success(self, app, test_person):
        """Test successful room data validation."""
        with app.app_context():
            test_person = db.session.merge(test_person)
            data = {
                'name': 'Chat with recruiter',
                'other_user_id': str(test_person.id)
            }
            errors = validate_new_room_data(data)
            assert errors == []
    
    def test_validate_room_data_missing_name(self, app, test_person):
        """Test validation fails with missing name."""
        with app.app_context():
            test_person = db.session.merge(test_person)
            data = {
                'other_user_id': str(test_person.id)
            }
            errors = validate_new_room_data(data)
            assert len(errors) > 0
    
    def test_validate_room_data_missing_user(self, app):
        """Test validation fails with missing user."""
        with app.app_context():
            data = {
                'name': 'Chat room'
            }
            errors = validate_new_room_data(data)
            assert len(errors) > 0
