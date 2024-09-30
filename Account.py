import mysql.connector
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkbootstrap import Style
import subprocess


def get_user_details(conn, acc_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name, city, phone_number FROM Accounts WHERE acc_id = %s", (acc_id,))
    return cursor.fetchone()  # Returns a tuple (name, city, phone_number)

def Accounts():
    global cursor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Accounts(
            acc_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            city VARCHAR(255) NOT NULL,
            phone_number VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS History(
            a_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
            quiz_topic INT NOT NULL,
            Scores INT NOT NULL,
            FOREIGN KEY(a_id) REFERENCES Accounts(acc_id)                  
        )
    ''')
    conn.commit()


def get_accounts():
    cursor.execute('''
                   SELECT name,password FROM Accounts''')
    rows = cursor.fetchall()
    accounts = {row[0]: row[1] for row in rows}
    return accounts

def add_missing_columns():
        global cursor, conn
        cursor.execute("SHOW COLUMNS FROM Accounts")
        columns = [info[0] for info in cursor.fetchall()]
        if "city" not in columns:
            cursor.execute("ALTER TABLE Accounts ADD COLUMN city VARCHAR(255) NOT NULL DEFAULT ''")
            print("Column 'city' added successfully")
        if "phone_number" not in columns:
            cursor.execute("ALTER TABLE Accounts ADD COLUMN phone_number VARCHAR(255) NOT NULL DEFAULT ''")
            print("Column 'phone_number' added successfully")
        conn.commit()


def add_account(name,city,phone_number, password):
    global cursor
    try:
     cursor.execute('''
         INSERT INTO Accounts(name,city,phone_number,password)
         VALUES (%s, %s, %s, %s)
     ''', (name, city, phone_number, password))
     conn.commit()
     messagebox.showinfo("Signup Success", "Account created successfully!")
     return True
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Database error: {e}")
        return False


def check_account(name, password):
    accounts = get_accounts()
    try:
        return (accounts[name] == password)
    except:
        messagebox.showwarning("Wrong", "Wrong Username or Password")

def save_session(username, acc_id):
    with open("name.txt", 'w') as f:
        f.write(f"{username},{acc_id}")
def Open_account(name, password):
    if not name or not password:
        messagebox.showwarning("Incomplete Data", "Please enter both username and password.")
        return

    accounts = get_accounts()
    if name in accounts:
        if accounts[name] == password:
            cursor.execute("SELECT acc_id FROM Accounts WHERE name = %s", (name,))
            acc_id = cursor.fetchone()[0]
            save_session(name, acc_id)  # Save session with username and acc_id
            root_acc.destroy()
            subprocess.run(["python", "Edu.py"])
        else:
            messagebox.showwarning("Login Failed", "Wrong password.")
            # window.destroy()
    else:
        messagebox.showwarning("Login Failed", "Username does not exist. Please sign up.")
        # window.destroy()


def Login():
    # Toplevel object which will
    # be treated as a new window
    global newWindow
    newWindow = tk.Toplevel(root_acc)

    # sets the title of the
    # Toplevel widget
    newWindow.title("Login")

    # sets the geometry of toplevel
    newWindow.geometry("400x300")
    name_var = tk.StringVar()
    pass_var = tk.StringVar()
    ttk.Label(newWindow, text='Name:').pack(padx=5, pady=5)
    ttk.Entry(newWindow, textvariable=name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(newWindow, text='Password:').pack(padx=5, pady=5)
    ttk.Entry(newWindow, textvariable=pass_var, width=30).pack(padx=5, pady=5)

    ttk.Button(newWindow, text='Login', command=lambda: Open_account(name_var.get(), pass_var.get())).pack(padx=5,pady=5)

def validate_and_add_account(name, city, phone, password, re_password):
    #print(f"Debug | Name: '{name}', City: '{city}', Phone: '{phone}', Password: '{password}', Retype: '{re_password}'")

    if password != re_password:
        messagebox.showerror("Error", "Passwords do not match. Please try again.")
        return
    if not (name.strip() and city.strip() and phone.strip() and password.strip()):
        messagebox.showerror("Error", "All fields are required. Please fill out all fields.")
        return
    #add_account(name.strip(), city.strip(), phone.strip(), password)
    if add_account(name.strip(), city.strip(), phone.strip(), password):
        newWindow.destroy()  # Close the signup window
        Login()


def Signup():
    global newWindow
    newWindow= tk.Toplevel(root_acc)

    # sets the title of the
    # Toplevel widget
    newWindow.title("Signup")

    # sets the geometry of toplevel
    newWindow.geometry("800x600")
    name_var = tk.StringVar()
    pass_var = tk.StringVar()
    city_var = tk.StringVar()
    phone_number_var = tk.StringVar()
    re_pass_var = tk.StringVar()

    #ttk.Label(newWindow, text='Name:').pack(padx=15, pady=15)
    #ttk.Entry(newWindow, textvariable=name_var, width=30).pack(padx=5, pady=5)

    #ttk.Label(newWindow, text='Password:').pack(padx=5, pady=5)
    #ttk.Entry(newWindow, textvariable=pass_var, width=30).pack(padx=5, pady=5)

    #ttk.Button(newWindow, text='Signup', command=lambda: add_account(name_var.get(), pass_var.get())).pack(padx=5,pady=5)
    ttk.Label(newWindow, text='Name:').pack(padx=10, pady=5)
    ttk.Entry(newWindow, textvariable=name_var, width=30).pack(padx=10, pady=5)

    ttk.Label(newWindow, text='City:').pack(padx=10, pady=5)
    ttk.Entry(newWindow, textvariable=city_var, width=30).pack(padx=10, pady=5)

    ttk.Label(newWindow, text='Phone Number:').pack(padx=10, pady=5)
    phone_var = tk.StringVar()
    ttk.Entry(newWindow, textvariable=phone_number_var, width=30).pack(padx=10, pady=5)

    ttk.Label(newWindow, text='Password:').pack(padx=10, pady=5)
    password_entry = ttk.Entry(newWindow, textvariable=pass_var, width=30, show="*")
    password_entry.pack(padx=10, pady=5)

    ttk.Label(newWindow, text='Retype Password:').pack(padx=10, pady=5)
    re_password_entry = ttk.Entry(newWindow, textvariable=re_pass_var, width=30, show="*")
    re_password_entry.pack(padx=10, pady=5)

    ttk.Button(newWindow, text='Signup',
               command=lambda: validate_and_add_account(name_var.get().strip(), city_var.get().strip(),
                                                        phone_number_var.get().strip(), pass_var.get().strip(),
                                                        re_pass_var.get().strip())).pack(padx=10, pady=20)


if __name__ == '__main__':
    conn = mysql.connector.connect(
        host="your_mysql_host",
        user="your_mysql_username",
        password="your_mysql_password",
        database="your_database_name"
    )
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

    global name_var

    root_acc.mainloop()

# n = name_var.get()
