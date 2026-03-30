import random
import string
from datetime import datetime, timedelta

from faker import Faker
from dotenv import load_dotenv

from app import create_app, db
from app.models import Person, Company, Job, JobApplication, Room, Message, Notifications


# Initialize Faker for generating random data
fake = Faker()

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_test_users(num_persons=10, num_companies=5):
    """Create test users (both persons and companies)"""
    users = []
    
    # Create persons
    for _ in range(num_persons):
        person = Person(
            email=f"person_{generate_random_string()}@example.com",
            password="test123", # this should be hashed...
            name=fake.first_name(),
            surname=fake.last_name(),
            user_type="person",
            location=fake.city(),
            profession=fake.job(),
            skills=[fake.word() for _ in range(random.randint(3, 8))],
            experience=[{
                "title": fake.job(),
                "company": fake.company(),
                "description": fake.text(),
                "start_date": (datetime.now() - timedelta(days=random.randint(365, 2000))).strftime("%Y-%m-%d"),
                "end_date": (datetime.now() - timedelta(days=random.randint(1, 364))).strftime("%Y-%m-%d")
            } for _ in range(random.randint(1, 3))],
            current_company_info={
                "company": fake.company(),
                "title": fake.job()
            }
        )
        users.append(person)
    
    # Create companies
    for _ in range(num_companies):
        company = Company(
            email=f"company_{generate_random_string()}@example.com",
            password="test123",  # this should be hashed...
            name=fake.company(),
            user_type="company",
            location=fake.city(),
            description=fake.text(),
            social_links={
                "linkedin": f"https://linkedin.com/company/{generate_random_string()}",
                "website": f"https://{generate_random_string()}.com"
            }
        )
        print(company.email)
        users.append(company)
    
    return users

def create_test_jobs(companies, num_jobs_per_company=3):
    """Create test jobs for companies"""
    jobs = []
    for company in companies:
        if isinstance(company, Company):
            for _ in range(num_jobs_per_company):
                job = Job(
                    company_id=company.id,
                    title=fake.job(),
                    description=fake.text(),
                    location=fake.city(),
                    salary=f"{random.randint(50000, 150000)}",
                    is_active=random.choice([True, False])
                )
                jobs.append(job)
    return jobs

def create_test_applications(jobs, persons, num_applications_per_job=2):
    """Create test job applications"""
    applications = []
    for job in jobs:
        if job.is_active:
            # Select random persons to apply for this job
            applicants = random.sample([p for p in persons if isinstance(p, Person)], 
                                    min(num_applications_per_job, len(persons)))
            for person in applicants:
                application = JobApplication(
                    job_id=job.id,
                    applicant_id=person.id,
                    resume_filename=f"resume_{generate_random_string()}.pdf",
                    status=random.choice(["pending", "accepted", "rejected", "under_review"]),
                    applied_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                applications.append(application)
    return applications

def create_test_rooms(users, num_rooms=15):
    """Create test chat rooms between users"""
    rooms = []
    for _ in range(num_rooms):
        # Select two different random users
        user1, user2 = random.sample(users, 2)
        room = Room(
            name=f"room_{generate_random_string()}",
            owner_id=user1.id,
            other_user_id=user2.id,
            is_active=True
        )
        rooms.append(room)
    return rooms

def create_test_messages(rooms, num_messages_per_room=5):
    """Create test messages in rooms"""
    messages = []
    for room in rooms:
        for _ in range(num_messages_per_room):
            # Randomly select sender from room participants
            sender_id = random.choice([room.owner_id, room.other_user_id])
            message = Message(
                room_id=room.id,
                sender_id=sender_id,
                message=fake.text(),
                created_at=datetime.now() - timedelta(minutes=random.randint(1, 60))
            )
            messages.append(message)
    return messages

def create_test_notifications(users, num_notifications=20):
    """Create test notifications for users"""
    notifications = []
    for _ in range(num_notifications):
        user = random.choice(users)
        notification = Notifications(
            receiver_id=user.id,
            message=fake.sentence(),
            read=random.choice([True, False])
        )
        notifications.append(notification)
    return notifications

# main function
def seed_database():
    """Main function to seed the database with test data"""
    # Load environment variables
    load_dotenv()
    # create app in testing config
    app = create_app('testing')

    with app.app_context():
        try:
            # Create and commit users first to get their IDs
            print("Creating test users...")
            users = create_test_users()
            db.session.add_all(users)
            db.session.flush()  # This assigns IDs without committing
            
            # Create jobs
            print("Creating test jobs...")
            companies = [u for u in users if isinstance(u, Company)] # only companies can create a job
            jobs = create_test_jobs(companies)
            db.session.add_all(jobs)
            db.session.flush()
            
            # Create applications
            print("Creating test applications...")
            persons = [u for u in users if isinstance(u, Person)] # only persons can apply to a job
            applications = create_test_applications(jobs, persons)
            db.session.add_all(applications)
            
            # Create rooms
            print("Creating test rooms...")
            rooms = create_test_rooms(users)
            db.session.add_all(rooms)
            db.session.flush()
            
            # Create messages
            print("Creating test messages...")
            messages = create_test_messages(rooms)
            db.session.add_all(messages)
            
            # Create notifications
            print("Creating test notifications...")
            notifications = create_test_notifications(users)
            db.session.add_all(notifications)
            
            # Finally commit everything
            db.session.commit()
            print("Database seeded successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding database: {str(e)}")
            raise

if __name__ == "__main__":
    seed_database() 