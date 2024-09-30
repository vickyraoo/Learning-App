import mysql
import sys
import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
import tkinterweb
from tkinter import messagebox
from ttkthemes import ThemedTk
import subprocess
from Account import n

conn = mysql.connector.connect(
    host="your_mysql_host",
    user="your_mysql_username",
    password="your_mysql_password",
    database="your_database_name"
)


# ppt link: https://www.canva.com/design/DAGDKT-NZfU/wG9z7FJC3s_zml9lDXLdyw/view?utm_content=DAGDKT-NZfU&utm_campaign=share_your_design&utm_medium=link&utm_source=shareyourdesignpanel


# Create database tables if they don't exist
global quiz_card_index, quiz_current_tabs  # New variables for quiz mode
quiz_card_index = 0
quiz_current_tabs = []

global card_index, current_tabs  # Existing variables for learn mode
card_index = 0
current_tabs = []

global quiz_active
quiz_active=False

def create_tables(conn):
    cursor = conn.cursor()

    # Create flashcard_sets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcard_sets (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   ac_id INTEGER NOT NULL,
                   FOREIGN KEY (ac_id) REFERENCES Accounts(acc_id)
        )
    ''')
    conn.commit()
    # Create flashcards table with foreign key reference to flashcard_sets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            FOREIGN KEY (set_id) REFERENCES flashcard_sets(id)               
        )
    ''')
    conn.commit()


# Function to Add a new flashcard set to the database
def add_set(conn, name, ac_id):
    cursor = conn.cursor()

    # Insert the set name into flashcard_sets table
    cursor.execute('''
        INSERT INTO flashcard_sets (name, ac_id)
        VALUES (?, ?)
    ''', (name, ac_id))

    set_id = cursor.lastrowid
    conn.commit()

    return set_id


def get_session():
    try:
        with open("name.txt", 'r') as f:
            data = f.read().strip()
            parts = data.split(',', 1)
            if len(data) < 2:
                raise ValueError("Invalid session data format.")
            username = parts[0]
            acc_id = int(parts[1])
            return username, acc_id
    except FileNotFoundError:
        handle_missing_session()
    except ValueError as ve:
        handle_corrupted_session(str(ve))


def handle_missing_session():
    print("Session file not found. Redirecting to login...")
    subprocess.run(["python", "Account.py"])  # Assume 'login.py' is your login script.


def handle_corrupted_session(error_message):
    print(f"Error reading session data: {error_message}")
    subprocess.run(["python", "Account.py"])  # Redirect to login script after showing an error message.


if __name__ == "__main__":
    try:
        username, acc_id = get_session()
        # Proceed with your application logic using `username` and `acc_id`.
    except TypeError:
        # This exception is caught if `get_session` does not return values, implying that the session could not be established.
        sys.exit(1)

if __name__ == "__main__":
    create_tables(conn)

    # Continue with your main application logic.
    # Ensure that all database operations use `acc_id` to filter user-specific data.


# Function to add a flashcard to the database
def add_card(conn, set_id, word, definition):
    cursor = conn.cursor()

    # Execute SQL query to insert a new flashcard into the database
    cursor.execute('''
        INSERT INTO flashcards (set_id, word, definition)
        VALUES (?, ?, ?)
    ''', (set_id, word, definition))

    # Get the ID of the newly inserted card
    card_id = cursor.lastrowid
    conn.commit()

    return card_id


# Function to retrieve all flashcard sets from the database
def get_sets(conn, ac_id):
    cursor = conn.cursor()

    # Execite SQL query to fetch all flashcard sets
    cursor.execute('''
        SELECT id, name FROM flashcard_sets WHERE ac_id=?
    ''', (ac_id,))

    rows = cursor.fetchall()
    sets = {row[1]: row[0] for row in rows}  # Create a dictionary of sets (name: id)

    return sets


# Function to retrieve all flashcards of a specific set
def get_cards(conn, set_id):
    cursor = conn.cursor()

    cursor.execute('''
        SELECT word, definition FROM flashcards
        WHERE set_id = ?
    ''', (set_id,))

    rows = cursor.fetchall()
    if not rows:
        print(f"No cards found for set_id: {set_id}")
    cards = [(row[0], row[1]) for row in rows]  # Create a list of cards (word, definition)

    return cards


# Function to delete a flashcard set from the database
def delete_set(conn, set_id):
    cursor = conn.cursor()

    # Execute SQL query to delete a flashcard set
    cursor.execute('''
        DELETE FROM flashcard_sets
        WHERE id = ?
    ''', (set_id,))

    conn.commit()
    sets_combobox.set('')
    clear_flashcard_display()
    populate_sets_combobox()

    # Clear the current_cards list and reset card_index
    global current_tabs, card_index
    current_tabs = []
    card_index = 0


# Function to create a new flashcard set
def create_set():
    set_name = set_name_var.get()
    if set_name:
        if set_name not in get_sets(conn, acc_id):
            set_id = add_set(conn, set_name, acc_id)
            populate_sets_combobox()
            set_name_var.set('')

            # Clear the input fields
            set_name_var.set('')
            word_var.set('')
            definition_var.set('')


def add_word():
    set_name = set_name_var.get()
    word = word_var.get()
    definition = definition_var.get()

    if set_name and word and definition:
        if set_name not in get_sets(conn, acc_id):
            set_id = add_set(conn, set_name, acc_id)
        else:
            set_id = get_sets(conn, acc_id)[set_name]

        add_card(conn, set_id, word, definition)

        word_var.set('')
        definition_var.set('')

        populate_sets_combobox()


def populate_sets_combobox():
    sets_combobox['values'] = tuple(get_sets(conn, acc_id).keys())


# Function to delete a selected flashcard set
def delete_selected_set():
    set_name = sets_combobox.get()

    if set_name:
        result = messagebox.askyesno(
            'Confirmation', f'Are you sure you want to delete the "{set_name}" set?'
        )

        if result == tk.YES:
            set_id = get_sets(conn, acc_id)[set_name]
            delete_set(conn, set_id)
            populate_sets_combobox()
            clear_flashcard_display()


def select_set():
    set_name = sets_combobox.get()

    if set_name:
        global card_num
        set_id = get_sets(conn, acc_id)[set_name]
        cards = get_cards(conn, set_id)
        card_num = len(cards)
        score_label.config(text=f'Score:{score}/{card_num}')
        if cards:
            display_flashcards(cards)
        else:
            word_label.config(text="No cards in this set")
            definition_label.config(text='')
    else:
        # Clear the current cards list and reset card index
        global current_tabs, card_index
        current_tabs = []
        card_index = 0
        clear_flashcard_display()


def display_flashcards(cards):
    global card_index
    global current_tabs

    card_index = 0
    current_tabs = cards

    # Clear the display
    if not cards:
        clear_flashcard_display()
    else:
        show_card()

    #show_card()


def clear_flashcard_display():
    wor_label.config(text='')
    word_label.config(text='')
    definition_label.config(text='')


# Function to display the current flashcards word
def show_card():
    global card_index
    global current_tabs

    if current_tabs:
        if 0 <= card_index < len(current_tabs):
            word, definition = current_tabs[card_index]
            word_label.config(text=word)
            #wor_label.config(text=word)
            definition_label.config(text='')

        else:
            clear_flashcard_display()


    else:
        clear_flashcard_display()


# Function to flip the current card and display its definition
def flip_card():
    global card_index
    global current_tabs

    if current_tabs:
        _, definition = current_tabs[card_index]
        definition_label.config(text=definition)

#def restart_quiz():
 #   global quiz_card_index, quiz_current_tabs, quiz_active, score
  #  score = 0
   # quiz_card_index = 0
    #init_quiz()


def init_or_restart_quiz():
    global quiz_card_index, quiz_current_tabs, quiz_active, score, quiz_button
    set_name = sets_combobox.get()

    if set_name:
        set_id = get_sets(conn, acc_id).get(set_name)
        if set_id:
            quiz_card_index = 0  # Reset the quiz index
            quiz_current_tabs = get_cards(conn, set_id)
            score = 0  # Reset score

            if quiz_current_tabs:
                quiz_show_card()
                quiz_active = True  # Indicate that quiz is now active
                quiz_button.config(text="Restart Quiz")  # Change button text to "Restart Quiz"
                score_label.config(text=f'Score: {score}/{len(quiz_current_tabs)}')
            else:
                messagebox.showinfo("No Data", "No flashcards available for this quiz.")
        else:
            messagebox.showinfo("Error", "Selected set not found in database.")
    else:
        messagebox.showinfo("Select a set", "Please select a set to start the quiz.")


# Add this button in the quiz_frame setup

 # Reinitialize the quiz

def load_quiz_data(set_id):
    global quiz_card_index, quiz_current_tabs
    quiz_card_index = 0  # Reset the quiz index each time new quiz data is loaded
    quiz_current_tabs = get_cards(conn, set_id)  # Fetch cards for the set
    if quiz_current_tabs:
        quiz_show_card()  # Display the first card of the new quiz data
    else:
        #wor_label.config(text="No cards available for this quiz.")
        messagebox.showinfo("No Data", "No flashcards available for this quiz.")

def select_quiz_set(set_id):
    load_quiz_data(set_id)

# Function to move to the next card
def next_card():
    global card_index
    global current_tabs

    if current_tabs and card_index < len(current_tabs) - 1:
        card_index += 1
        show_card()


# Function to move to the previous card
def prev_card():
    global card_index
    global current_tabs

    if current_tabs and card_index > 0:
        card_index -= 1
        show_card()

def quiz_show_card():
    global quiz_card_index, quiz_current_tabs, wor_label
    if quiz_current_tabs and quiz_card_index < len(quiz_current_tabs):
        word, definition = quiz_current_tabs[quiz_card_index]
        wor_label.config(text=word)
    else:
        wor_label.config(text="No more cards or error loading cards.")
def quiz_next_card():
    global quiz_card_index, quiz_current_tabs
    if quiz_current_tabs:
        quiz_card_index = min(quiz_card_index + 1, len(quiz_current_tabs) - 1)
        quiz_show_card()

def quiz_prev_card():
    global quiz_card_index, quiz_current_tabs
    if quiz_current_tabs:
        quiz_card_index = max(quiz_card_index - 1, 0)
        quiz_show_card()
def check_ans():
        global score_label, score, quiz_card_index, quiz_current_tabs

        if not quiz_current_tabs:
            messagebox.showinfo("No Cards", "No cards available in this set.")
            return

        # Retrieve and clean user input
        ans = answer_var.get().strip()
        answer_var.set('')  # Clear the input field for the next response

        # Get the correct answer for the current card
        _, correct_def = quiz_current_tabs[quiz_card_index]

        # Check the user's answer and provide feedback
        if ans.lower() == correct_def.lower():
            score += 1
            messagebox.showinfo("Correct!", "Correct answer!")
        else:
            messagebox.showerror("Wrong Answer!", f"Incorrect answer. The correct answer was: {correct_def}")

        # Update the score display
        score_label.config(text=f'Score: {score}/{len(quiz_current_tabs)}')

        # Advance to the next card if there are more cards
        if quiz_card_index < len(quiz_current_tabs) - 1:
            quiz_card_index += 1
            quiz_show_card()  # Display the next card
        else:
            # End of quiz
            messagebox.showinfo("Quiz Completed", f"Quiz is over. Your final score is {score}/{len(quiz_current_tabs)}")
            score = 0
            quiz_card_index = 0
            score_label.config(text=f'Score: {score}/{len(quiz_current_tabs)}')
            quiz_show_card()  # Refresh to start or hide quiz area, depending on your design

def quiz_show_card():
    global quiz_card_index, quiz_current_tabs, wor_label

    if quiz_current_tabs and quiz_card_index < len(quiz_current_tabs):
            word, _ = quiz_current_tabs[quiz_card_index]
            wor_label.config(text=word)  # Update the word label to the new question
    else:
            wor_label.config(text="No more cards or error loading cards.")


def logout():
    with open("name.txt", 'w') as f:
        f.write('')
    print("Logged out. Closing application.")
    root_acc.destroy()
    subprocess.run(["python", "Account.py"])

#def restart_quiz():
 #   global score, quiz_card_index
  # quiz_card_index = 0
   # score_label.config(text=f'Score: {score}/{len(quiz_current_tabs)}')
    #init_quiz()  # Assuming init_quiz can reinitialize everything needed

def update_account_tab(account_frame, user_details):
    # Clear previous details
    for widget in account_frame.winfo_children():
        widget.destroy()

    ttk.Label(account_frame, text=f'Name: {user_details[0]}').pack(padx=5, pady=5)
    ttk.Label(account_frame, text=f'City: {user_details[1]}').pack(padx=5, pady=5)
    ttk.Label(account_frame, text=f'Phone Number: {user_details[2]}').pack(padx=5, pady=5)
    ttk.Button(account_frame, text="Logout", command=logout).pack(padx=5, pady=5)

def get_user_details(conn, acc_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name, city, phone_number FROM Accounts WHERE acc_id = ?", (acc_id,))
    return cursor.fetchone()

if __name__ == "__main__":
    # Connect to the SQLite database and create tables
    username, acc_id = get_session()
    create_tables(conn)
    user_details = get_user_details(conn, acc_id)
    # Create the main GUI window
    root_acc = tk.Tk()
    root_acc.title('Flashcards App')
    root_acc.geometry('800x600')
    # root_acc = ThemedTk(theme='winxpblue')

    # Apply styling to the GUI elements
    style = Style(theme='superhero')
    style.configure('TLabel', font=('TkDefaultFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    # Set up variables for storing user input
    global set_name_var
    set_name_var = tk.StringVar()
    global word_var
    word_var = tk.StringVar()
    global definition_var
    definition_var = tk.StringVar()
    global answer_var
    answer_var = tk.StringVar()

    # Create a notebook widget to manage tabs
    #notebook = ttk.Notebook(root_acc)
    #notebook.pack(fill='both', expand=True)

    # GUI for adding new sets
    #add_set_frame = ttk.Frame(root_acc)
    #add_set_frame.pack(fill='both', expand=True)

    #set_name_var = tk.StringVar()
    #ttk.Label(add_set_frame, text='Enter Set Name:').pack(pady=10)
    #ttk.Entry(add_set_frame, textvariable=set_name_var).pack(pady=10)
    #ttk.Button(add_set_frame, text='Add Set', command=lambda: add_set(set_name_var.get(), acc_id)).pack(pady=10)

    #ttk.Label(root_acc, text=f'Logged in as: {username}').pack(side=tk.TOP, fill=tk.X, pady=10)
    #ttk.Button(root_acc, text="Logout", command=logout).pack(side=tk.TOP, fill=tk.X, pady=10)

    # Create the "Create Set" tab and its content
    notebook = ttk.Notebook(root_acc)
    notebook.pack(fill='both', expand=True)
    create_set_frame = ttk.Frame(notebook)
    notebook.add(create_set_frame, text='Create Set')

    # Label and Entry widgets for entering set name, word and definition
    ttk.Label(create_set_frame, text='Topic Name:').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Question:').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=word_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Answer:').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=definition_var, width=30).pack(padx=5, pady=5)

    # Button to add a word to the set
    ttk.Button(create_set_frame, text='Add Question', command=add_word).pack(padx=5, pady=10)

    # Button to save the set
    ttk.Button(create_set_frame, text='Save Topic', command=create_set).pack(padx=5, pady=10)

    # Create the "Select Set" tab and its content
    select_set_frame = ttk.Frame(notebook)
    notebook.add(select_set_frame, text="Select Topic")

    # Combobox widget for selecting existing flashcard sets
    global sets_combobox
    sets_combobox = ttk.Combobox(select_set_frame, state='readonly')
    sets_combobox.pack(padx=5, pady=40)

    # Button to select a set
    ttk.Button(select_set_frame, text='Select Topic', command=select_set).pack(padx=5, pady=5)

    # Button to delete a set
    ttk.Button(select_set_frame, text='Delete Topic', command=delete_selected_set).pack(padx=5, pady=5)

    # Create the "Learn mode" tab and its content
    flashcards_frame = ttk.Frame(notebook)
    notebook.add(flashcards_frame, text='Learn Mode')

    # Initialize variables for tracking card index and current cards
    card_index = 0
    current_tabs = []

    # Label to display the word on flashcards
    global wor_label, word_label
    word_label = ttk.Label(flashcards_frame, text='', font=('TkDefaultFont', 24))
    word_label.pack(padx=5, pady=40)

    # Label to display the definition on flashcards
    global definition_label
    definition_label = ttk.Label(flashcards_frame, text='')
    definition_label.pack(padx=5, pady=5)

    # Button to flip the flashcard
    ttk.Button(flashcards_frame, text='Flip', command=flip_card).pack(side='left', padx=5, pady=5)

    # Button to view the next flashcard
    ttk.Button(flashcards_frame, text='Next', command=next_card).pack(side='right', padx=5, pady=5)

    # Button to view the previous flashcard
    ttk.Button(flashcards_frame, text='Previous', command=prev_card).pack(side='right', padx=5, pady=5)

    quiz_frame = ttk.Frame(notebook)
    notebook.add(quiz_frame, text='Quiz')
    global score
    score = 0

    wor_label = ttk.Label(quiz_frame, text='', font=('TkDefaultFont', 24))
    wor_label.pack(padx=5, pady=40)

    max_score = 0
    ttk.Label(quiz_frame, text='Answer:').pack(padx=5, pady=5)
    defi_label = ttk.Entry(quiz_frame, textvariable=answer_var, width=30).pack(padx=5, pady=5)
    global score_label
    #ttk.Button(quiz_frame, text="Start Quiz", command=init_quiz).pack(pady=10)
    global quiz_button
    quiz_button = ttk.Button(quiz_frame, text="Start Quiz", command=init_or_restart_quiz)
    quiz_button.pack(pady=10)
    score_label = ttk.Label(quiz_frame, text=f'Score:{score}/{max_score}')
    score_label.pack(padx=5, pady=5)
   # ttk.Button(quiz_frame, text="Restart Quiz", command=restart_quiz).pack(side='right', pady=10)
    ttk.Button(quiz_frame, text='Check & Next', command=check_ans,).pack(side='right', padx=5, pady=5)
    #ttk.Button(quiz_frame, text='Next', command=quiz_next_card).pack(side='right', padx=5, pady=5)

    # ttk.Button(quiz_frame, text='Previous', command=prev_card).pack(side='right', padx=5, pady=5)

    account_frame = ttk.Frame(notebook)
    notebook.add(account_frame, text='Account')
    update_account_tab(account_frame, user_details)
   # f = open('name.txt', 'r')
    #name = f.read().strip()
    #print("Name read from file:", username)
    #f.close()
    #ttk.Label(account_frame, text=f'Name: {username}').pack(padx=5, pady=5)
    #style = Style(theme='superhero')
    #style.configure('TButton', font=('TkDefaultFont', 16))
    ## Add a logout button
    #ttk.Button(account_frame, text="Logout", command=logout).pack(padx=5, pady=5)

    google_search_frame = ttk.Frame(notebook)
    notebook.add(google_search_frame, text="Google Search")
    google_frame = tkinterweb.HtmlFrame(google_search_frame)
    google_frame.load_website("https://google.com")
    google_frame.pack(fill='both', expand=True)

    populate_sets_combobox()

    root_acc.mainloop()