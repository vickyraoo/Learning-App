# Learning-App (Flashcards & Quiz Desktop Application)

A desktop study tool built with **Python** and **Tkinter**. Create an account, organize
study material into flashcard sets, and reinforce learning through a self-paced **Learn**
mode and a scored **Quiz** mode. The app ships with two interchangeable database
backends — **MySQL** and **SQLite** — so you can run it against either a client-server
database or a zero-setup embedded one.

## Features

- Account sign-up and login, with salted + hashed passwords (no plaintext storage)
- Duplicate-username prevention
- Create, select, and delete flashcard sets
- Add word/definition flashcards to any set
- **Learn mode** — browse cards at your own pace
- **Quiz mode** — type answers, get a running score, restart anytime
- Built-in reference browser tab (for quick look-ups while studying)
- Consistent themed UI (`ttkbootstrap`, "superhero" theme)

## Project Structure

| File | Purpose |
|---|---|
| `Account.py` | Login / sign-up UI — **MySQL** backend |
| `Account1.py` | Login / sign-up UI — **SQLite** backend |
| `Edu.py` | Main app (sets, Learn mode, Quiz mode) — **MySQL** backend |
| `Edu1.py` | Main app (sets, Learn mode, Quiz mode) — **SQLite** backend |
| `auth_utils.py` | Shared password hashing/verification helper |
| `name.txt` | Auto-generated session file (created at login, don't edit by hand) |

> The MySQL pair (`Account.py` + `Edu.py`) and the SQLite pair (`Account1.py` + `Edu1.py`)
> are independent — pick **one** pair to run, not a mix of the two.

## Prerequisites

- Python 3.9+
- pip packages:
  ```bash
  pip install ttkbootstrap ttkthemes tkinterweb
  ```
- For the MySQL backend only, also install:
  ```bash
  pip install mysql-connector-python
  ```
  and have a MySQL server running and reachable.

## Getting Started

### Option A — SQLite (quickest, no server required)

```bash
python Account1.py
```

A `flashcards.db` file is created automatically in the project folder the first time
you run it. Sign up, then log in — the app will open `Edu1.py` for you automatically.

### Option B — MySQL

1. Create a database for the app (any name you like).
2. Set the following environment variables before launching (defaults shown — change
   them to match your setup):

   ```bash
   export FLASHCARDS_DB_HOST=localhost
   export FLASHCARDS_DB_USER=root
   export FLASHCARDS_DB_PASSWORD=yourpassword
   export FLASHCARDS_DB_NAME=flashcards_app
   ```

   On Windows (PowerShell):
   ```powershell
   $env:FLASHCARDS_DB_HOST="localhost"
   $env:FLASHCARDS_DB_USER="root"
   $env:FLASHCARDS_DB_PASSWORD="yourpassword"
   $env:FLASHCARDS_DB_NAME="flashcards_app"
   ```

3. Run:
   ```bash
   python Account.py
   ```

   Required tables (`Accounts`, `History`, `flashcard_sets`, `flashcards`) are created
   automatically on first launch.

## Using the App

1. **Sign up** with a username, city, phone number, and password.
2. **Log in** — you're taken straight into the main application.
3. Use the **Create Set** option to start a new flashcard set, then add word/definition
   pairs to it.
4. Switch to **Learn** to review cards at your own pace, or **Quiz** to test yourself
   with a running score.
5. **Logout** returns you to the login screen and clears the session.

## How It Works

The login UI and the main application run as two separate processes rather than one:

```
User → Login/Signup (Account.py / Account1.py)
            │  on success, writes name.txt and launches the main app
            ▼
       Main App (Edu.py / Edu1.py) → Database (MySQL / SQLite)
```

`name.txt` is the handoff point — it stores the logged-in username and account ID so
the main application knows who's signed in after being launched as a new process.

## Database Schema (summary)

| Table | Key Columns | Purpose |
|---|---|---|
| `Accounts` | `acc_id` (PK), `name` (unique), `city`, `phone_number`, `password` (hash) | One row per user |
| `History` | `h_id` (PK), `acc_id` (FK → Accounts), `quiz_topic`, `Scores` | Quiz attempt records |
| `flashcard_sets` | `id` (PK), `name`, `ac_id` (FK → Accounts) | A user's named set of flashcards |
| `flashcards` | `id` (PK), `set_id` (FK → flashcard_sets), `word`, `definition` | Individual flashcards |

## Known Limitations / Possible Next Steps

- `History` is defined and ready to use, but no quiz results are written to it yet —
  wiring this up would enable a "past attempts" view.
- The login ↔ main-app handoff uses a file-based session and separate processes;
  switching to in-app frame navigation within one Tkinter root would remove that
  dependency entirely.
- The embedded reference-browser tab uses a lightweight HTML renderer without
  JavaScript support, so not all websites will display correctly.

## License

This project is provided as-is for educational purposes.
