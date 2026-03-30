# JobFind

JobFind is a web application designed to facilitate job searching and networking. It provides features for job listings, direct messaging, notifications, and user profiles.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)


## Installation

To set up the project locally using Docker, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/erdisonmalko/find-job-app.git
   ```
2. Navigate to the project directory:
   ```bash
   cd JobFind
   ```
3. Build and start the Docker containers:
   ```bash
   docker-compose up -d
   ```
   This command will build the Docker images and start the containers in detached mode.

4. Access the application:
   - The web application will be available at `http://localhost:5001`.

## Usage

To stop the application, use the following command:

```bash
docker-compose down
```

This command will stop and remove the containers.

