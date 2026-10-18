# NeuroNote [(Demo Video)](https://drive.google.com/file/d/1EtsaI_GRrXyUGs8sc8LQtT5g5q4XGc3J/view?usp=sharing)
NeuroNote is a backend focused project that serves as a study platform designed for students. Unlike many tools that focus only on theory, NeuroNote emphasizes practical, applied learning. It uses active recall and relative SRS (spaced repetition system) to help students master concepts deeply.
<img width="1431" height="729" alt="Screenshot 2026-09-29 at 9 03 59 PM" src="https://github.com/user-attachments/assets/d85bc19e-233c-4be4-8399-43345c3f2d98" />

## Features
### User Authentication
Google OAuth2 login + openID & in app login/signin
### Study Tools
**Notes**: Simple document to folder design. <br>
**File uploads**: In the study room users can upload files or links to their "pinned resources" section. <br>
**Quizzes**: User can either manually create or generate a quiz; take the quiz either with a timer or not & view the latest test results for review. <br>
**Flashcards**: Relative SRS with bucket tier system. <br>
*    Bucket Tier System -> Cards are categorized within their decks through buckets. Buckets are rankings for the flashcards cards that define if the card (since the latest review) was either a "complete struggle" (bucket 1), "poor" (bucket 2), "good" (bucket 3), "easy" (bucket 4), or if the card was just created it will automatically be placed in bucket 0 as it being a "new card". <br>
*    Relative SRS -> This flashcard approach was inspired by the relative spaced repetition system from Brainscape. The idea behind it is being flexible with the users time. Unlike absolute spaced repetition systems (Anki), these flashcards don't a dedicated review date. Instead they categorized and graded by bucket tiers which have dedicated probabilities. These probabilities are for when the user generates a study queue group, the flashcards will then have the chance to be selected to be apart of that group which can then be studied. The group will then reset allowing for new cards to be selected. Cards rated higher than a 1 will be blacklisted from being selected to a new study queue group for the next hour which allows for new information to be studied. 

## Planned Features
**Collaboration**: <br>
* Quiz battles
* notes/decks marketplace
* group study sessions <br>
  
**Study Methods**: <br>
1.    Flashchcard Study Methods: <br>
*    Exam -> The Exam group will create a schedule on a calendar from the day of until the date of the exam. The days will be populated with study material such as quizzes and flashcard study sessions. To help with properly scheduling the days with enough and proper material, AI (anthropic) will be used. The groups of cards chosen for the study sessions in the respective days will be chosen based on a dynamic forgetting curve algorithm. To make this possible the flashcards will have to keep the last reviewed date attribute. The exam group will also apply a scheduled date for when the cards are supposed to be reviewed. Cards in this group should be labeld as “Reserved” meaning they can only be studied on their specified date. <br>
*    Time Crunch -> The user will be asked how much time they currently have to study and based on that time there will be x amount of temporary groups created full of cards that the user would be able to study in that specified time frame back to back with the option to quit after each group has been completed (the cards will still use the probability feature of being in one of those groups). <br>
**Analytics**: Show progression of cards/quizzes and specific subjects, and record study time in total and each deck/subject. <br>
2.    General Study Methods: <br>
*    Research & Synthesis -> Practice searching for information. The user will use the question on the flashcard as the purpose of their search queries. They will then try searching for information with their query, AI will grade the quality of it based on specific or too broad it is, if its valid then the search will go through and articles will be returned that the user can choose from. After each article they visit they will summarize what they have read. Eventually the user can choose to come to a conclusion where they will then write an answer to the question on the flashcard.
     -    The cards used will be different from the traditional flashcards that hold a question and answer. These will be specifically for Research & Synthesis where they will only have a question. To know if these cards have been reviewed or not they will hold review history. <br>
**Achievements**: <br>
* Undecided amount of achievements but they will be earned through studying with quizzes, flashcards, general study methods, and login streaks <br>
**Improved Note Taking**: <br>
* Auto save
* Image resizing
* Improved tables (adding/removing rows and columns, and resizing)
**Mind Map**
* Allows for visual users to get more out of NeuroNote
**More Practical Study Methods**:
* Include an IDE for programming and canvas for math

## Tech Stack <br>
*    Backend: Django, Django REST Framework <br>
*    Database: PostgreSQL <br>
*    Frontend: React <br>
*    Services: Railway
