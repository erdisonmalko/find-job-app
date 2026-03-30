import pytest
from werkzeug.security import check_password_hash

from app import db
from app.models import User, Person, Company, Job, JobApplication


@pytest.mark.unit
class TestPersonModel:
    """Test Person model."""
    
    def test_person_creation(self, app, test_person):
        """Test creating a person user."""
        with app.app_context():
            # Merge detached fixture into session
            test_person = db.session.merge(test_person)
            
            assert test_person.name == 'John Seeker'
            assert test_person.email == 'seeker@example.com'
            assert test_person.user_type == 'person'
            assert test_person.is_confirmed is True
    
    def test_person_can_apply_to_job(self, app, test_person):
        """Test person can apply to jobs."""
        with app.app_context():
            test_person = db.session.merge(test_person)
            
            assert test_person.can_apply_to_job() is True
            assert test_person.can_create_job() is False


@pytest.mark.unit
class TestCompanyModel:
    """Test Company model."""
    
    def test_company_creation(self, app, test_company):
        """Test creating a company user."""
        with app.app_context():
            test_company = db.session.merge(test_company)
            
            assert test_company.name == 'Tech Corp'
            assert test_company.email == 'company@example.com'
            assert test_company.user_type == 'company'
            assert test_company.is_confirmed is True
    
    def test_company_can_create_job(self, app, test_company):
        """Test company can create jobs."""
        with app.app_context():
            test_company = db.session.merge(test_company)
            
            assert test_company.can_apply_to_job() is False
            assert test_company.can_create_job() is True


@pytest.mark.unit
class TestJobModel:
    """Test Job model."""
    
    def test_job_creation(self, app, test_company):
        """Test creating a job."""
        with app.app_context():
            # Merge detached fixture into session
            test_company = db.session.merge(test_company)
            
            job = Job(
                title='Senior Developer',
                description='We are looking for a senior developer',
                location='New York',
                salary='$100k - $150k',
                company_id=test_company.id,
                is_active=True
            )
            db.session.add(job)
            db.session.commit()
            
            assert job.title == 'Senior Developer'
            assert job.company_id == test_company.id
            assert job.is_active is True


@pytest.mark.unit
class TestJobApplicationModel:
    """Test JobApplication model."""
    
    def test_job_application_creation(self, app, test_person, test_company):
        """Test creating a job application."""
        with app.app_context():
            # Merge detached fixtures into session
            test_person = db.session.merge(test_person)
            test_company = db.session.merge(test_company)
            
            job = Job(
                title='Developer',
                description='Job desc',
                location='NYC',
                salary='$100k',
                company_id=test_company.id
            )
            db.session.add(job)
            db.session.commit()
            
            application = JobApplication(
                job_id=job.id,
                applicant_id=test_person.id,
                resume_filename='resume.pdf',
                status='pending'
            )
            db.session.add(application)
            db.session.commit()
            
            assert application.status == 'pending'
            assert application.applicant_id == test_person.id
            assert application.job_id == job.id
