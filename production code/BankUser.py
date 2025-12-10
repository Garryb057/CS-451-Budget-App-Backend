import tkinter as tk
from tkinter import messagebox
import mysql.connector
import bcrypt
import time
import uuid
from datetime import datetime, timedelta
import secrets
from BankDashboard import open_dashboard

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Melt1129",
    database="banking_db"
)

cursor = db.cursor()

# Functions
def register_user():
    first_name = entry_first.get()
    last_name = entry_last.get()
    email_reg = entry_email_reg.get()
    password_reg = entry_password_reg.get()
    phone_number = entry_phone.get()

    if not first_name or not last_name or not email_reg or not password_reg or not phone_number:
        messagebox.showwarning("Missing Fields", "Please fill in all fields")
        return

    hashed = bcrypt.hashpw(password_reg.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO bankUser (first_name, last_name, email, password_hash, phone_number) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email_reg, hashed.decode(), phone_number)
        )
        db.commit()
        messagebox.showinfo("Success", "User registered successfully!")
        clear_register_fields()
        show_login_screen()
    except mysql.connector.Error as err:
        db.rollback()
        if err.errno == 1062:
            messagebox.showerror("Error", "That email/phone number is already in use.")
        else:
            messagebox.showerror("Error", f"Database error: {err}")

def login_user():
    email = entry_email.get()
    password = entry_password.get()

    cursor.execute("SELECT idbankUser, first_name, last_name, password_hash FROM bankUser WHERE email=%s", (email,))
    row = cursor.fetchone()

    if not row:
        messagebox.showerror("Login Failed", "Invalid email or password")
        return

    user_id, first_name, last_name, password_hash = row

    if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
        messagebox.showinfo("Login", f"Welcome, {first_name} {last_name}!")

        # store current user's email for later settings lookups
        global current_user_email
        current_user_email = email

        # import here to avoid circular dependency
        from BankDashboard import open_dashboard

        # open dashboard and provide settings callback + pass db/cursor
        open_dashboard(root,first_name,last_name,user_id,logout_callback,settings_callback=show_account_settings,db=db,cursor=cursor)
    else:
        messagebox.showerror("Login Failed", "Invalid email or password")


root = tk.Tk()
root.title("Login System")
root.geometry("350x400")

frame_login = tk.Frame(root)
frame_register = tk.Frame(root)

# Login screen
tk.Label(frame_login, text="Login", font=("Arial", 16, "bold")).pack(pady=10)

tk.Label(frame_login, text="Email").pack(pady=2)
entry_email = tk.Entry(frame_login)
entry_email.pack(pady=2)

tk.Label(frame_login, text="Password").pack(pady=2)
entry_password = tk.Entry(frame_login, show="*")
entry_password.pack(pady=2)

tk.Button(frame_login, text="Login", command=login_user).pack(pady=10)

tk.Label(frame_login, text="Don't have an account?").pack(pady=5)
tk.Button(frame_login, text="Sign up here", command=lambda: show_register_screen()).pack()


# sign up screen
tk.Label(frame_register, text="Register", font=("Arial", 16, "bold")).pack(pady=10)

tk.Label(frame_register, text="First Name").pack(pady=2)
entry_first = tk.Entry(frame_register)
entry_first.pack(pady=2)

tk.Label(frame_register, text="Last Name").pack(pady=2)
entry_last = tk.Entry(frame_register)
entry_last.pack(pady=2)

tk.Label(frame_register, text="Email").pack(pady=2)
entry_email_reg = tk.Entry(frame_register)
entry_email_reg.pack(pady=2)

tk.Label(frame_register, text="Password").pack(pady=2)
entry_password_reg = tk.Entry(frame_register, show="*")
entry_password_reg.pack(pady=2)

tk.Label(frame_register, text="Phone Number").pack(pady=2)
entry_phone = tk.Entry(frame_register)
entry_phone.pack(pady=2)

tk.Button(frame_register, text="Register", command=register_user).pack(pady=10)
tk.Button(frame_register, text="Return", command=lambda: show_login_screen()).pack()

# switch between screens
def show_login_screen():
    frame_register.pack_forget()
    frame_login.pack(fill="both", expand=True)

#shows the register screen.
def show_register_screen():
    frame_login.pack_forget()
    frame_register.pack(fill="both", expand=True)

#used to clear out the fields once done.
def clear_register_fields():
    entry_first.delete(0, tk.END)
    entry_last.delete(0, tk.END)
    entry_email_reg.delete(0, tk.END)
    entry_password_reg.delete(0, tk.END)
    entry_phone.delete(0, tk.END)

#once the user logs out, this function will be called and delete each filed of the entry email and password.
def logout_callback(root):
    entry_email.delete(0, tk.END)
    entry_password.delete(0, tk.END)
    root.deiconify()

#Function to verify the account of the user.
def verify_account(token):
    cursor.execute("SELECT token_expiry FROM bankUser WHERE verification_token=%s", (token,))
    row = cursor.fetchone()

    if not row:
        messagebox.showerror("Error", "Invalid verification code.")
        return

    expiry = row[0]
    if expiry is None or datetime.now() > expiry:
        messagebox.showwarning("Expired Code", "This verification code has expired. Please request a new one.")
        return

    # Mark verified
    cursor.execute("""
        UPDATE bankUser
        SET is_verified=1, verification_token=NULL, token_expiry=NULL
        WHERE verification_token=%s
    """, (token,))
    db.commit()

    messagebox.showinfo("Verified", "Your account has been successfully verified!")

def start_verification_flow(parent_window):
    from BankEmail import send_verification_email
    import random

    # Generates a 6-digit code for the user.
    token = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=10)

    # this will then store it in the database.
    cursor.execute("""
        UPDATE bankUser
        SET verification_token=%s, token_expiry=%s
        WHERE email=%s
    """, (token, expiry, current_user_email))
    db.commit()

    # Send the code by email
    send_verification_email(current_user_email, token)

    # Open the small entry window
    show_verification_entry_window(parent_window)

def show_verification_entry_window(parent_window):
    win = tk.Toplevel(parent_window)
    win.title("Verify Account")
    win.geometry("300x150")
    win.transient(parent_window)
    win.grab_set()

    tk.Label(win, text="Code sent to your email!", font=("Arial", 11, "bold")).pack(pady=5)
    tk.Label(win, text="Enter the code below:").pack(pady=5)

    code_entry = tk.Entry(win)
    code_entry.pack(pady=2)

    def submit_code():
        token = code_entry.get().strip()
        if not token:
            messagebox.showwarning("Missing Code", "Please enter the verification code.")
            return
        verify_account(token)
        win.destroy()

    tk.Button(win, text="Verify", command=submit_code).pack(pady=10)

# This shows the infomation of the settings to the user.
def show_account_settings(parent_window):
    """Open a modal window showing account info and allow edits."""
    # fetch latest user info
    cursor.execute("SELECT first_name, last_name, email, phone_number, is_verified FROM bankUser WHERE email=%s", (current_user_email,))
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Error", "Could not load user info.")
        return

    fname, lname, email, phone, is_verified = row

    settings_win = tk.Toplevel(parent_window)
    settings_win.title("Account Settings")
    settings_win.geometry("350x350")
    settings_win.transient(parent_window)
    settings_win.grab_set()

    tk.Label(settings_win, text="Account Settings", font=("Arial", 14, "bold")).pack(pady=8)

    tk.Label(settings_win, text="First Name").pack(pady=2)
    e_fname = tk.Entry(settings_win)
    e_fname.insert(0, fname)
    e_fname.pack(pady=2)

    tk.Label(settings_win, text="Last Name").pack(pady=2)
    e_lname = tk.Entry(settings_win)
    e_lname.insert(0, lname)
    e_lname.pack(pady=2)

    tk.Label(settings_win, text="Email").pack(pady=2)
    e_email = tk.Entry(settings_win)
    e_email.insert(0, email)
    e_email.pack(pady=2)

    tk.Label(settings_win, text="Phone Number").pack(pady=2)
    e_phone = tk.Entry(settings_win)
    e_phone.insert(0, phone)
    e_phone.pack(pady=2)

    def save_changes():
        global current_user_email
        new_fname = e_fname.get().strip()
        new_lname = e_lname.get().strip()
        new_email = e_email.get().strip()
        new_phone = e_phone.get().strip()

        if not new_fname or not new_lname or not new_email or not new_phone:
            messagebox.showwarning("Missing Fields", "Please fill in all fields")
            return

        try:
            cursor.execute("UPDATE bankUser SET first_name=%s, last_name=%s, email=%s, phone_number=%s WHERE email=%s",
                           (new_fname, new_lname, new_email, new_phone, current_user_email))
            db.commit()
        except mysql.connector.Error as err:
            db.rollback()
            if err.errno == 1062:
                messagebox.showerror("Error", "That email or phone number is already in use.")
                return
            else:
                messagebox.showerror("Error", f"Database error: {err}")
                return

        # If email changed (compare normalized values), update session and prompt to re-login
        try:
            old_norm = (current_user_email or "").strip().lower()
        except Exception:
            old_norm = ""
        new_norm = new_email.strip().lower()

        if new_norm != old_norm:
            messagebox.showinfo("Email Changed", "Your email was changed. You will be logged out and need to login with the new email.")
            settings_win.destroy()
            # force logout: close parent dashboard and show login
            parent_window.destroy()
            logout_callback(root)
            return

        # Once user info is updated, it will send out an alert email to the user's email address.
        from BankEmail import send_alert_email
        send_alert_email(
            to_email=new_email,
            subject="Your Account Information Was Updated",
            body=(
                "Hello,\n\nYour account information was recently updated.\n"
                "If this was not you, please reset your password immediately."
            )
        )
        # No email change — success
        messagebox.showinfo("Success", "Account updated successfully.")
        settings_win.destroy()
    
    #checks if the user is verified or not.
    if is_verified == 1:
        tk.Label(settings_win, text="✅ Account Verified", fg="green", font=("Arial", 10, "bold")).pack(pady=5)
    else:
        frame_verify = tk.Frame(settings_win)
        frame_verify.pack(pady=5)

        tk.Label(frame_verify, text="Not verified? ", fg="red").pack(side="left")

        link_label = tk.Label(
            frame_verify,
            text="Click here to verify",
            fg="blue",
            cursor="hand2",
            font=("Arial", 10, "underline")
        )
        link_label.pack(side="left")

        # Clicking the link triggers opens a verification window
        link_label.bind("<Button-1>", lambda e: start_verification_flow(settings_win))



    tk.Button(settings_win, text="Save Changes", command=save_changes).pack(pady=12)
    tk.Button(settings_win, text="Close", command=settings_win.destroy).pack()

#starts with the login screen firstly
show_login_screen()


root.mainloop()
