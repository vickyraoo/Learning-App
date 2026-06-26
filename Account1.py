import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkbootstrap import Style
import subprocess

# Assuming these are correctly implemented in your auth_utils.py
from auth_utils import hash_password, verify_password

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'flashcards.db')

def get_user_details(conn, acc_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name, city, phone_number FROM Accounts WHERE acc_id = ?", (acc_id,))
    return cursor.fetchone()  # Returns a tuple (name, city, phone_number)

def Accounts():
    global cursor, conn
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Accounts(
            acc_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            city TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS History(
            h_id INTEGER PRIMARY KEY AUTOINCREMENT,
            acc_id INTEGER NOT NULL,
            quiz_topic INTEGER NOT NULL,
            Scores INTEGER NOT NULL,
            FOREIGN KEY(acc_id) REFERENCES Accounts(acc_id)
        )
    ''')
    conn.commit()

def add_missing_columns():
    global cursor, conn
    cursor.execute("PRAGMA table_info(Accounts)")
    columns = [info[1] for info in cursor.fetchall()]
    if "city" not in columns:
        cursor.execute("ALTER TABLE Accounts ADD COLUMN city TEXT NOT NULL DEFAULT ''")
        print("Column 'city' added successfully")
    if "phone_number" not in columns:
        cursor.execute("ALTER TABLE Accounts ADD COLUMN phone_number TEXT NOT NULL DEFAULT ''")
        print("Column 'phone_number' added successfully")
    conn.commit()

def add_account(name, city, phone_number, password):
    global cursor, conn
    cursor.execute("SELECT 1 FROM Accounts WHERE name = ?", (name,))
    if cursor.fetchone():
        messagebox.showerror("Error", "That username is already taken. Please choose another.")
        return False
    try:
        cursor.execute('''
            INSERT INTO Accounts(name, city, phone_number, password)
            VALUES (?, ?, ?, ?)
        ''', (name, city, phone_number, hash_password(password)))
        conn.commit()
        messagebox.showinfo("Signup Success", "Account created successfully!")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Error", f"Database error: {e}")
        return False

def save_session(username, acc_id):
    with open("name.txt", 'w') as f:
        f.write(f"{username},{acc_id}")

def Open_account(name, password):
    global cursor
    if not name or not password:
        messagebox.showwarning("Incomplete Data", "Please enter both username and password.")
        return

    # Secure data handling: Retrieve only the specific user's data
    cursor.execute("SELECT acc_id, password FROM Accounts WHERE name = ?", (name,))
    result = cursor.fetchone()

    if result:
        acc_id, hashed_password = result
        if verify_password(hashed_password, password):
            save_session(name, acc_id)  # Save session with username and acc_id
            root_acc.destroy()
            subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "Edu1.py")])
        else:
            messagebox.showwarning("Login Failed", "Wrong password.")
    else:
        messagebox.showwarning("Login Failed", "Username does not exist. Please sign up.")

def Login():
    global newWindow
    newWindow = tk.Toplevel(root_acc)
    newWindow.title("Login")
    newWindow.geometry("400x300")
    
    name_var = tk.StringVar()
    pass_var = tk.StringVar()
    
    ttk.Label(newWindow, text='Name:').pack(padx=5, pady=5)
    ttk.Entry(newWindow, textvariable=name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(newWindow, text='Password:').pack(padx=5, pady=5)
    # Added show="*" to mask the password on login
    ttk.Entry(newWindow, textvariable=pass_var, width=30, show="*").pack(padx=5, pady=5)

    ttk.Button(newWindow, text='Login', command=lambda: Open_account(name_var.get(), pass_var.get())).pack(padx=5, pady=5)

def validate_and_add_account(name, city, phone, password, re_password):
    if password != re_password:
        messagebox.showerror("Error", "Passwords do not match. Please try again.")
        return
    if not (name.strip() and city.strip() and phone.strip() and password.strip()):
        messagebox.showerror("Error", "All fields are required. Please fill out all fields.")
        return
    
    if add_account(name.strip(), city.strip(), phone.strip(), password):
        newWindow.destroy()  # Close the signup window
        Login()

def Signup():
    global newWindow
    newWindow = tk.Toplevel(root_acc)
    newWindow.title("Signup")
    newWindow.geometry("800x600")
    
    name_var = tk.StringVar()
    pass_var = tk.StringVar()
    city_var = tk.StringVar()
    phone_number_var = tk.StringVar()
    re_pass_var = tk.StringVar()

    ttk.Label(newWindow, text='Name:').pack(padx=10, pady=5)
    ttk.Entry(newWindow, textvariable=name_var, width=30).pack(padx=10, pady=5)

    ttk.Label(newWindow, text='City:').pack(padx=10, pady=5)
    ttk.Entry(newWindow, textvariable=city_var, width=30).pack(padx=10, pady=5)

    ttk.Label(newWindow, text='Phone Number:').pack(padx=10, pady=5)
    ttk.Entry(newWindow, textvariable=phone_number_var, width=30).pack(padx=10, pady=5)

    ttk.Label(newWindow, text='Password:').pack(padx=10, pady=5)
    password_entry = ttk.Entry(newWindow, textvariable=pass_var, width=30, show="*")
    password_entry.pack(padx=10, pady=5)

    ttk.Label(newWindow, text='Retype Password:').pack(padx=10, pady=5)
    re_password_entry = ttk.Entry(newWindow, textvariable=re_pass_var, width=30, show="*")
    re_password_entry.pack(padx=10, pady=5)

    ttk.Button(newWindow, text='Signup',
               command=lambda: validate_and_add_account(
                   name_var.get().strip(), 
                   city_var.get().strip(),
                   phone_number_var.get().strip(), 
                   pass_var.get().strip(),
                   re_pass_var.get().strip()
               )).pack(padx=10, pady=20)

if __name__ == '__main__':
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        Accounts()
        add_missing_columns()
        
        root_acc = tk.Tk()
        root_acc.geometry('200x200')
        root_acc.title('Accounts')

        style = Style(theme='superhero')
        style.configure('TLabel', font=('TkDefaultFont', 18))
        style.configure('TButton', font=('TkDefaultFont', 16))

        ttk.Button(text='Login', command=Login).pack(padx=5, pady=5)
        ttk.Button(text='Signup', command=Signup).pack(padx=5, pady=5)

        root_acc.mainloop()

    except sqlite3.Error as e:
        print(f"Failed to connect to the database: {e}")
    finally:
        # Close database connections when the UI is closed to prevent database locking issues
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()