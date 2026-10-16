# NeuroNote
NeuroNote is a study platform designed for students. Unlike many tools that focus only on theory, NeuroNote emphasizes practical, applied learning. It uses active recall and relative SRS (spaced repetition system) to help students master concepts deeply.
<img width="1431" height="729" alt="Screenshot 2026-09-29 at 9 03 59 PM" src="https://github.com/user-attachments/assets/d85bc19e-233c-4be4-8399-43345c3f2d98" />

## Features
### User Authentication
Google OAuth2 login + openID & in app login/signin
### Study Tools
**Notes**: Simple document to folder design.
**File uploads**: In the study room users can upload files or links to their "pinned resources" section.
**Quizzes**: User can either manually create or generate a quiz; take the quiz either with a timer or not & view the latest test results for review.
**Flashcards**: Relative SRS with bucket tier system.
    -    Bucket Tier System -> Cards are categorized within their decks through buckets. Buckets are rankings for the flashcards cards that define if the card (since the latest review) was either a "complete struggle" (bucket 1), "poor" (bucket 2), "good" (bucket 3), "easy" (bucket 4), or if the card was just created it will automatically be placed in bucket 0 as it being a "new card".
    -    Relative SRS -> 

## 🛠️ Planned Features <br>
- 	Collaboration: quiz battles, notes/decks marketplace, group study sessions, leaderboards <br>
- 	Mobile app: Using react native <br>
- 	Automated study plan generator: Generate flashcard schedules, problems sets, quizzes, and breaks to avoid burnout <br>
- 	Analytics/dashboard: show weakness/strong areas, retention forecast, goal tracking <br>
- 	Study mode personalization: Focus mode, application mode, cram mode, deep mastery mode <br>
- 	Curriculum Inegration <br>

## ⚡ Tech Stack <br>
-	Backend: Django, Django REST Framework <br>
-	Database: SQLite (for development) and PostgreSQL (for production) <br>
-	Auth: Google OAuth2 <br>
-	Frontend: React <br>

## 🛠️ Setup Instructions <br>
1. Clone the repo <br>
- git clone https://github.com/jaylenmc/NeuroNote.git <br>
    
2. Create & activate a virtual environment (Use python3.12) <br>
- python3 -m venv venv <br>
- source venv/bin/activate (Mac/Linux) <br>
- venv\Scripts\activate (Windows) <br>
    
3. Install dependencies <br>
- pip install -r requirements.txt <br>
    
4. Run migrations <br>
⚠️ Note: Migrations were reset to simplify setup because of conflicting migrations. <br>
- python3 manage.py makemigrations <br>
- python3 manage.py migrate <br>
    
5. Create a superuser <br>
- python3 manage.py createsuperuser <br>
  
6. Run the server <br>
  - Backend: python3 manage.py runserver -> visit: http://127.0.0.1:8000/ <br>

## 📝 Notes for Reviewers / Employers <br>
  - The frontend code was intentionally excluded to protect proprietary work, so only the backend and necessary components are shared. <br>
  -	Migrations were reset for simplicity, so you won’t encounter historical conflicts when setting up locally. <br>
  ### Codebase demonstrates: <br>
  -	Includes implementation of spaced repetition scheduling (SM-2/SM-21 algorithms) <br>
  -	Clean API design with DRF <br>
  -	Custom serializers & services (e.g. scheduling algorithm) <br>
  -	Authentication flow with external providers <br>
  -	Unit tests for critical paths <br>
