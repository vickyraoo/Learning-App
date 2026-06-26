import os
import sys
import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
import tkinterweb
from tkinter import messagebox
import subprocess
import psycopg2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variables for tracking states
quiz_card_index = 0
quiz_current_tabs = []
card_index = 0
current_tabs = []
score = 0


def create_tables(conn):
    cursor = conn.cursor()

    # Create flashcard_sets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcard_sets (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            ac_id INTEGER NOT NULL,
            FOREIGN KEY (ac_id) REFERENCES Accounts(acc_id) ON DELETE CASCADE
        )
    ''')
    
    # Create flashcards table with foreign key reference to flashcard_sets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards (
            id SERIAL PRIMARY KEY,
            set_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            FOREIGN KEY (set_id) REFERENCES flashcard_sets(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()


def add_set(conn, name, ac_id):
    cursor = conn.cursor()
    # PostgreSQL requires RETURNING id to get the last inserted row
    cursor.execute('''
        INSERT INTO flashcard_sets (name, ac_id)
        VALUES (%s, %s) RETURNING id
    ''', (name, ac_id))

    set_id = cursor.fetchone()[0]
    conn.commit()
    return set_id


def get_session():
    try:
        with open("name.txt", 'r') as f:
            data = f.read().strip()
            parts = data.split(',', 1)
            if len(data) < 2 or len(parts) < 2:
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
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "Account.py")])
    sys.exit(1)


def handle_corrupted_session(error_message):
    print(f"Error reading session data: {error_message}")
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "Account.py")])
    sys.exit(1)


def add_card(conn, set_id, word, definition):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO flashcards (set_id, word, definition)
        VALUES (%s, %s, %s) RETURNING id
    ''', (set_id, word, definition))

    card_id = cursor.fetchone()[0]
    conn.commit()
    return card_id


def get_sets(conn, ac_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name FROM flashcard_sets WHERE ac_id=%s
    ''', (ac_id,))

    rows = cursor.fetchall()
    sets = {row[1]: row[0] for row in rows}
    return sets


def get_cards(conn, set_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT word, definition FROM flashcards
        WHERE set_id = %s
    ''', (set_id,))

    rows = cursor.fetchall()
    if not rows:
        print(f"No cards found for set_id: {set_id}")
    cards = [(row[0], row[1]) for row in rows]
    return cards


def delete_set(conn, set_id):
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM flashcard_sets
        WHERE id = %s
    ''', (set_id,))

    conn.commit()
    sets_combobox.set('')
    clear_flashcard_display()
    populate_sets_combobox()

    global current_tabs, card_index
    current_tabs = []
    card_index = 0


def create_set():
    set_name = set_name_var.get().strip()
    if set_name:
        if set_name not in get_sets(conn, acc_id):
            add_set(conn, set_name, acc_id)
            populate_sets_combobox()

        # Clear the input fields
        set_name_var.set('')
        word_var.set('')
        definition_var.set('')


def add_word():
    set_name = set_name_var.get().strip()
    word = word_var.get().strip()
    definition = definition_var.get().strip()

    if set_name and word and definition:
        existing_sets = get_sets(conn, acc_id)
        if set_name not in existing_sets:
            set_id = add_set(conn, set_name, acc_id)
        else:
            set_id = existing_sets[set_name]

        add_card(conn, set_id, word, definition)

        word_var.set('')
        definition_var.set('')
        populate_sets_combobox()


def populate_sets_combobox():
    sets_combobox['values'] = tuple(get_sets(conn, acc_id).keys())


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
        global current_tabs, card_index
        current_tabs = []
        card_index = 0
        clear_flashcard_display()


def display_flashcards(cards):
    global card_index, current_tabs
    card_index = 0
    current_tabs = cards

    if not cards:
        clear_flashcard_display()
    else:
        show_card()


def clear_flashcard_display():
    if 'wor_label' in globals():
        wor_label.config(text='')
    if 'word_label' in globals():
        word_label.config(text='')
    if 'definition_label' in globals():
        definition_label.config(text='')


def show_card():
    global card_index, current_tabs

    if current_tabs:
        if 0 <= card_index < len(current_tabs):
            word, definition = current_tabs[card_index]
            word_label.config(text=word)
            definition_label.config(text='')
        else:
            clear_flashcard_display()
    else:
        clear_flashcard_display()


def flip_card():
    global card_index, current_tabs
    if current_tabs:
        _, definition = current_tabs[card_index]
        definition_label.config(text=definition)


def init_or_restart_quiz():
    global quiz_card_index, quiz_current_tabs, score, quiz_button
    set_name = sets_combobox.get()

    if set_name:
        set_id = get_sets(conn, acc_id).get(set_name)
        if set_id:
            quiz_card_index = 0
            quiz_current_tabs = get_cards(conn, set_id)
            score = 0

            if quiz_current_tabs:
                quiz_show_card()
                quiz_button.config(text="Restart Quiz")
                score_label.config(text=f'Score: {score}/{len(quiz_current_tabs)}')
            else:
                messagebox.showinfo("No Data", "No flashcards available for this quiz.")
        else:
            messagebox.showinfo("Error", "Selected set not found in database.")
    else:
        messagebox.showinfo("Select a set", "Please select a set to start the quiz.")


def load_quiz_data(set_id):
    global quiz_card_index, quiz_current_tabs
    quiz_card_index = 0
    quiz_current_tabs = get_cards(conn, set_id)
    if quiz_current_tabs:
        quiz_show_card()
    else:
        messagebox.showinfo("No Data", "No flashcards available for this quiz.")


def select_quiz_set(set_id):
    load_quiz_data(set_id)


def next_card():
    global card_index, current_tabs
    if current_tabs and card_index < len(current_tabs) - 1:
        card_index += 1
        show_card()


def prev_card():
    global card_index, current_tabs
    if current_tabs and card_index > 0:
        card_index -= 1
        show_card()


def quiz_show_card():
    global quiz_card_index, quiz_current_tabs, wor_label
    if quiz_current_tabs and quiz_card_index < len(quiz_current_tabs):
        word, _ = quiz_current_tabs[quiz_card_index]
        wor_label.config(text=word)
    else:
        wor_label.config(text="No more cards or error loading cards.")


def check_ans():
    global score_label, score, quiz_card_index, quiz_current_tabs

    if not quiz_current_tabs:
        messagebox.showinfo("No Cards", "No cards available in this set.")
        return

    ans = answer_var.get().strip()
    answer_var.set('')

    _, correct_def = quiz_current_tabs[quiz_card_index]

    if ans.lower() == correct_def.lower():
        score += 1
        messagebox.showinfo("Correct!", "Correct answer!")
    else:
        messagebox.showerror("Wrong Answer!", f"Incorrect answer. The correct answer was: {correct_def}")

    score_label.config(text=f'Score: {score}/{len(quiz_current_tabs)}')

    if quiz_card_index < len(quiz_current_tabs) - 1:
        quiz_card_index += 1
        quiz_show_card()
    else:
        messagebox.showinfo("Quiz Completed", f"Quiz is over. Your final score is {score}/{len(quiz_current_tabs)}")
        score = 0
        quiz_card_index = 0
        score_label.config(text=f'Score: {score}/{len(quiz_current_tabs)}')
        quiz_show_card()


def logout():
    with open("name.txt", 'w') as f:
        f.write('')
    print("Logged out. Closing application.")
    root_acc.destroy()
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "Account.py")])


def update_account_tab(account_frame, user_details):
    for widget in account_frame.winfo_children():
        widget.destroy()

    if user_details:
        ttk.Label(account_frame, text=f'Name: {user_details[0]}').pack(padx=5, pady=5)
        ttk.Label(account_frame, text=f'City: {user_details[1]}').pack(padx=5, pady=5)
        ttk.Label(account_frame, text=f'Phone Number: {user_details[2]}').pack(padx=5, pady=5)
    ttk.Button(account_frame, text="Logout", command=logout).pack(padx=5, pady=5)


def get_user_details(conn, acc_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name, city, phone_number FROM Accounts WHERE acc_id = %s", (acc_id,))
    return cursor.fetchone()


if __name__ == "__main__":
    try:
        username, acc_id = get_session()
    except TypeError:
        sys.exit(1)

    try:
        conn = psycopg2.connect(
            host="localhost",
            database="flashcards_app",
            user="postgres",
            password="password",
            port="5432"
        )
        create_tables(conn)
        user_details = get_user_details(conn, acc_id)

        # Create the main GUI window
        root_acc = tk.Tk()
        root_acc.title('Flashcards App')
        root_acc.geometry('800x600')

        # Apply styling to the GUI elements
        style = Style(theme='superhero')
        style.configure('TLabel', font=('TkDefaultFont', 18))
        style.configure('TButton', font=('TkDefaultFont', 16))

        # Set up variables for storing user input
        set_name_var = tk.StringVar()
        word_var = tk.StringVar()
        definition_var = tk.StringVar()
        answer_var = tk.StringVar()

        notebook = ttk.Notebook(root_acc)
        notebook.pack(fill='both', expand=True)

        # --- Create Set Tab ---
        create_set_frame = ttk.Frame(notebook)
        notebook.add(create_set_frame, text='Create Set')

        ttk.Label(create_set_frame, text='Topic Name:').pack(padx=5, pady=5)
        ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

        ttk.Label(create_set_frame, text='Question:').pack(padx=5, pady=5)
        ttk.Entry(create_set_frame, textvariable=word_var, width=30).pack(padx=5, pady=5)

        ttk.Label(create_set_frame, text='Answer:').pack(padx=5, pady=5)
        ttk.Entry(create_set_frame, textvariable=definition_var, width=30).pack(padx=5, pady=5)

        ttk.Button(create_set_frame, text='Add Question', command=add_word).pack(padx=5, pady=10)
        ttk.Button(create_set_frame, text='Save Topic', command=create_set).pack(padx=5, pady=10)

        # --- Select Set Tab ---
        select_set_frame = ttk.Frame(notebook)
        notebook.add(select_set_frame, text="Select Topic")

        sets_combobox = ttk.Combobox(select_set_frame, state='readonly')
        sets_combobox.pack(padx=5, pady=40)

        ttk.Button(select_set_frame, text='Select Topic', command=select_set).pack(padx=5, pady=5)
        ttk.Button(select_set_frame, text='Delete Topic', command=delete_selected_set).pack(padx=5, pady=5)

        # --- Learn Mode Tab ---
        flashcards_frame = ttk.Frame(notebook)
        notebook.add(flashcards_frame, text='Learn Mode')

        word_label = ttk.Label(flashcards_frame, text='', font=('TkDefaultFont', 24))
        word_label.pack(padx=5, pady=40)

        definition_label = ttk.Label(flashcards_frame, text='')
        definition_label.pack(padx=5, pady=5)

        ttk.Button(flashcards_frame, text='Flip', command=flip_card).pack(side='left', padx=5, pady=5)
        ttk.Button(flashcards_frame, text='Next', command=next_card).pack(side='right', padx=5, pady=5)
        ttk.Button(flashcards_frame, text='Previous', command=prev_card).pack(side='right', padx=5, pady=5)

        # --- Quiz Tab ---
        quiz_frame = ttk.Frame(notebook)
        notebook.add(quiz_frame, text='Quiz')

        wor_label = ttk.Label(quiz_frame, text='', font=('TkDefaultFont', 24))
        wor_label.pack(padx=5, pady=40)

        ttk.Label(quiz_frame, text='Answer:').pack(padx=5, pady=5)
        defi_label = ttk.Entry(quiz_frame, textvariable=answer_var, width=30)
        defi_label.pack(padx=5, pady=5)

        quiz_button = ttk.Button(quiz_frame, text="Start Quiz", command=init_or_restart_quiz)
        quiz_button.pack(pady=10)
        
        score_label = ttk.Label(quiz_frame, text='Score: 0/0')
        score_label.pack(padx=5, pady=5)
        
        ttk.Button(quiz_frame, text='Check & Next', command=check_ans).pack(side='right', padx=5, pady=5)

        # --- Account Tab ---
        account_frame = ttk.Frame(notebook)
        notebook.add(account_frame, text='Account')
        update_account_tab(account_frame, user_details)

        # --- Google Search Tab ---
        google_search_frame = ttk.Frame(notebook)
        notebook.add(google_search_frame, text="Google Search")
        google_frame = tkinterweb.HtmlFrame(google_search_frame)
        google_frame.load_website("https://google.com")
        google_frame.pack(fill='both', expand=True)

        populate_sets_combobox()

        root_acc.mainloop()

    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
