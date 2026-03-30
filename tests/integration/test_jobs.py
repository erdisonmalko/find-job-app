import pytest
from app import db
from app.models import Job, JobApplication


@pytest.mark.integration
class TestJobAPI:
    """Test job API endpoints."""
    
    def test_list_jobs(self, auth_person, app, test_company):
        """Test listing jobs."""
        with app.app_context():
            # Merge detached fixture
            test_company = db.session.merge(test_company)
            
            # Create a job
            job = Job(
                title='Senior Developer',
                description='Looking for senior developer',
                location='New York',
                salary='$100k-$150k',
                company_id=test_company.id,
                is_active=True
            )
            db.session.add(job)
            db.session.commit()
        
        response = auth_person.get('/jobs')
        assert response.status_code == 200
        assert b'Senior Developer' in response.data
    
    def test_create_job_as_company(self, client, auth_company, app, test_company):
        """Test creating a job as company."""
        response = auth_company.post('/jobs/job/create', data={
            'jobtitle': 'Backend Engineer',
            'description': 'We need a backend engineer',
            'joblocation': 'San Francisco',
            'jobsalary': '$120k-$180k'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Check job was created
        with app.app_context():
            test_company = db.session.merge(test_company)
            job = Job.query.filter_by(title='Backend Engineer').first()
            assert job is not None
            assert job.company_id == test_company.id
    
    def test_create_job_as_person_fails(self, client, auth_person):
        """Test that person cannot create jobs."""
        response = auth_person.post('/jobs/job/create', data={
            'jobtitle': 'Some Job',
            'description': 'Desc',
            'joblocation': 'NYC',
            'jobsalary': '$100k'
        }, follow_redirects=True)
        
        # Should redirect or show error - person cannot create jobs
        assert b'company' in response.data.lower() or b'only' in response.data.lower()


@pytest.mark.integration
class TestJobApplicationAPI:
    """Test job application endpoints."""
    
    def test_apply_for_job(self, client, auth_person, app, test_person, test_company):
        """Test applying for a job."""
        with app.app_context():
            # Merge detached fixtures
            test_company = db.session.merge(test_company)
            test_person = db.session.merge(test_person)
            
            job = Job(
                title='Frontend Developer',
                description='We need frontend developers',
                location='NYC',
                salary='$90k-$130k',
                company_id=test_company.id,
                is_active=True
            )
            db.session.add(job)
            db.session.commit()
            job_id = job.id
        
        # Mock file upload
        response = auth_person.post(f'/jobs/job/apply/{job_id}', data={
            'resume': (open('/dev/null', 'rb'), 'resume.pdf')
        }, follow_redirects=True)
        
        # Application should be created (or redirect if successful)
        assert response.status_code == 200
    
    def test_get_application_detail(self, client, auth_person, app, test_person, test_company):
        """Test getting application details."""
        with app.app_context():
            # Merge detached fixtures
            test_company = db.session.merge(test_company)
            test_person = db.session.merge(test_person)
            
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
                status='pending'
            )
            db.session.add(application)
            db.session.commit()
            app_id = application.id
        
        response = auth_person.get(f'/applications/application/detail/{app_id}')
        assert response.status_code == 200
        assert b'Developer' in response.data or b'pending' in response.data.lower()
