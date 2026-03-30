from datetime import datetime, date

from flask_login import UserMixin
from sqlalchemy import DateTime
from sqlalchemy import JSON
# local
from app import db


class User(UserMixin, db.Model):
    """Base User class for both Person and Company users"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'person' or 'company'
    location = db.Column(db.String(100))
    # valid email checks
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(DateTime, nullable=True)
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.now)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = db.Column(DateTime)

    # Relationships for chat
    rooms_owned = db.relationship('Room', 
                                foreign_keys='Room.owner_id',
                                backref=db.backref('owner', passive_deletes=True),
                                cascade='all, delete-orphan',
                                single_parent=True)
    
    rooms_joined = db.relationship('Room',
                                 foreign_keys='Room.other_user_id',
                                 backref=db.backref('other_user', passive_deletes=True),
                                 cascade='all, delete-orphan',
                                 single_parent=True)
    
    messages = db.relationship('Message',
                             backref=db.backref('sender', passive_deletes=True),
                             cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

    def __str__(self):
        return f"{self.user_type.capitalize()}: {self.name} ({self.email})"


class Person(User):
    """Person specific attributes and relationships"""
    __tablename__ = 'persons'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    surname = db.Column(db.String(100))
    profession = db.Column(db.String(100))
    skills = db.Column(JSON)
    experience = db.Column(JSON)
    current_company_info = db.Column(JSON)
    
    # Relationship for job applications
    applications = db.relationship('JobApplication',
                                 backref=db.backref('applicant', passive_deletes=True),
                                 cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'person',
    }

    def can_apply_to_job(self):
        return True

    def can_create_job(self):
        return False


class Company(User):
    """Company specific attributes and relationships"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    description = db.Column(db.Text)
    social_links = db.Column(JSON)
    # Relationship for jobs
    jobs = db.relationship('Job',
                          backref=db.backref('company', passive_deletes=True),
                          cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'company',
    }

    def can_apply_to_job(self):
        return False

    def can_create_job(self):
        return True


class Room(db.Model):
    """Chat room between two users"""
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, 
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    other_user_id = db.Column(db.Integer,
                             db.ForeignKey('users.id', ondelete='CASCADE'),
                             nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.now)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Messages in this room
    messages = db.relationship('Message',
                             backref=db.backref('room', passive_deletes=True),
                             cascade='all, delete-orphan')

    def get_other_participant(self, current_user_id):
        """Get the other participant's info based on current user"""
        if current_user_id == self.owner_id:
            return self.other_user
        return self.owner


class Message(db.Model):
    """Direct messages between users"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer,
                       db.ForeignKey('rooms.id', ondelete='CASCADE'),
                       nullable=False)
    sender_id = db.Column(db.Integer,
                         db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(DateTime, default=datetime.now)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)

    
    def json_version(self):
        return{
            'room_id': self.room_id,
            'sender_id': self.sender_id,
            'message': self.message,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

class Job(db.Model):
    """Job posting by a company"""
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer,
                          db.ForeignKey('companies.id', ondelete='CASCADE'),
                          nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    salary = db.Column(db.String(100))
    created_at = db.Column(DateTime, default=datetime.now)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship to applications
    applications = db.relationship('JobApplication',
                                 backref=db.backref('job', passive_deletes=True),
                                 cascade='all, delete-orphan')


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer,
                      db.ForeignKey('jobs.id', ondelete='CASCADE'),
                      nullable=False)
    applicant_id = db.Column(db.Integer,
                            db.ForeignKey('persons.id', ondelete='CASCADE'),
                            nullable=False)
    # Store only the unique filename or URL
    resume_filename = db.Column(db.String(255))
    status = db.Column(db.String(100), default="pending")
    applied_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @property
    def calculate_days_applied(self):
        days = date(self.applied_at) - date.today()
        return f"Days passed from applied day {days}"

    def __json__(self):
        return {
            "id": self.id,
            "applied_at": self.applied_at.strftime("%Y-%m-%d %H:%M:%S"),
            "resume_url": f"/static/resume_upload/{self.resume_filename}" if self.resume_filename else None,
        }

class Notifications(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    receiver_id = db.Column(db.Integer, nullable=False) # Can be a user or a company
    message = db.Column(db.Text)  # Large text for messages
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(DateTime, default=datetime.now)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __json__(self):
        return {
            "id": self.id,
            "receiver_id": self.receiver_id,
            "message": self.message,
            "read": self.read,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            
        }


class ContactMessage(db.Model):
    __tablename__ = 'contact_message'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    is_read = db.Column(db.Boolean, default=False)


    
class SimpleRepr(object):
    """A mixin implementing a simple __repr__."""
    def __repr__(self):
        return "<{klass} @{id:x} {attrs}>".format(
            klass=self.__class__.__name__,
            id=id(self) & 0xFFFFFF,
            attrs=" ".join("{}={!r}".format(k, v) for k, v in self.__dict__.items()),
            )
    
