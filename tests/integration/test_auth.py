import pytest
from app import db
from app.models import Person, Company


@pytest.mark.integration
class TestAuthentication:
    """Test user authentication flow."""
    
    def test_person_login_success(self, client, app, test_person):
        """Test successful login as person."""
        with app.app_context():
            test_person = db.session.merge(test_person)
            
            response = client.post('/users/login', data={
                'email': test_person.email,
                'password': 'password123',
                'user_type': 'person'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Check that user is logged in by redirecting to jobs page
            assert b'job' in response.data.lower() or b'seeker' in response.data.lower()
    
    def test_company_login_success(self, client, app, test_company):
        """Test successful login as company."""
        with app.app_context():
            test_company = db.session.merge(test_company)
            
            response = client.post('/users/login', data={
                'email': test_company.email,
                'password': 'password123',
                'user_type': 'company'
            }, follow_redirects=True)
            
            assert response.status_code == 200
    
    def test_login_wrong_password(self, client, app, test_person):
        """Test login fails with wrong password."""
        with app.app_context():
            test_person = db.session.merge(test_person)
            
            response = client.post('/users/login', data={
                'email': test_person.email,
                'password': 'wrongpassword',
                'user_type': 'person'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            # Should redirect back to login with error
            assert b'login' in response.data.lower() or b'invalid' in response.data.lower()
    
    def test_login_nonexistent_user(self, client, app):
        """Test login fails with non-existent user."""
        with app.app_context():
            response = client.post('/users/login', data={
                'email': 'nonexistent@example.com',
                'password': 'password123',
                'user_type': 'person'
            }, follow_redirects=True)
            
            assert response.status_code == 200
