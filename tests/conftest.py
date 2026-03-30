import os
import tempfile
import pytest
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User, Person, Company


@pytest.fixture
def app():
    """Create application for testing with SQLite in-memory database."""
    app = create_app('testing')
    
    # Override database to use in-memory SQLite for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # Create test uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        
        # Clean up test uploads directory
        import shutil
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_person(app):
    """Create a test person (job seeker) user."""
    with app.app_context():
        person = Person(
            name='John Seeker',
            email='seeker@example.com',
            password=generate_password_hash('password123'),
            location='New York',
            user_type='person',
            is_confirmed=True
        )
        db.session.add(person)
        db.session.commit()
        return person


@pytest.fixture
def test_company(app):
    """Create a test company user."""
    with app.app_context():
        company = Company(
            name='Tech Corp',
            email='company@example.com',
            password=generate_password_hash('password123'),
            location='San Francisco',
            user_type='company',
            is_confirmed=True,
            description='A tech company'
        )
        db.session.add(company)
        db.session.commit()
        return company


@pytest.fixture
def auth_person(client, test_person):
    """Authenticate as person and return client with session."""
    client.post('/users/login', data={
        'email': 'seeker@example.com',
        'password': 'password123',
        'user_type': 'person'
    }, follow_redirects=True)
    return client


@pytest.fixture
def auth_company(client, test_company):
    """Authenticate as company and return client with session."""
    client.post('/users/login', data={
        'email': 'company@example.com',
        'password': 'password123',
        'user_type': 'company'
    }, follow_redirects=True)
    return client
