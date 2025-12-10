import tkinter as tk
from tkinter import messagebox
import time
import uuid


SESSION_TIMEOUT = 30  # 5 minutes/30 secs for testing

# Global session info
SESSION = {
    "token": None,
    "last_active": None
}

#Opening dashboard after login. 
def open_dashboard(root, first_name, last_name, user_id, logout_callback, settings_callback=None, db=None, cursor=None):
    # Hide login window
    root.withdraw()

    # Create session token
    SESSION["token"] = str(uuid.uuid4())
    SESSION["last_active"] = time.time()

    # Dashboard window
    dashboard = tk.Toplevel()
    dashboard.title("User Dashboard")
    dashboard.geometry("500x400")

    tk.Label(dashboard, text=f"Welcome, {first_name} {last_name}", font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(dashboard, text="Account Overview", font=("Arial", 14)).pack(pady=5)

    balance_var = tk.StringVar()
    balance = get_user_balance(user_id, cursor)
    balance_var.set(f"${balance:,.2f}")
    tk.Label(dashboard, textvariable=balance_var, font=("Arial", 24, "bold"), fg="green").pack(pady=10)

    # Dashboard buttons
    tk.Button(dashboard,text="Deposit",width=20,command=lambda: deposit_money(user_id, db, cursor, balance_var)).pack(pady=5)
    tk.Button(dashboard, text="Withdraw", width=20).pack(pady=5)
    tk.Button(dashboard, text="Transfer Money", width=20).pack(pady=5)
    tk.Button(dashboard, text="View Transactions", width=20).pack(pady=5)
    # Account Settings button will call the provided settings_callback if present.
    tk.Button(dashboard, text="Account Settings", width=20,
              command=(lambda: settings_callback(dashboard) if settings_callback else None)).pack(pady=5)

    tk.Button(dashboard, text="Logout", width=15, fg="red",
              command=lambda: logout(dashboard, root, logout_callback)).pack(pady=20)

    # Bind activity tracking
    dashboard.bind_all("<Any-KeyPress>", lambda e: update_activity())
    dashboard.bind_all("<Any-ButtonPress>", lambda e: update_activity())
    dashboard.bind_all("<Motion>", lambda e: update_activity())

    # Start inactivity check
    check_inactivity(dashboard, root, logout_callback, user_id, cursor)

# Function for depositing money to the users balances.
def deposit_money(user_id, db, cursor, balance_var):
    """Popup window for depositing money."""
    deposit_win = tk.Toplevel()
    deposit_win.title("Deposit Funds")
    deposit_win.geometry("300x200")
    deposit_win.grab_set()

    tk.Label(deposit_win, text="Enter deposit amount:", font=("Arial", 12)).pack(pady=10)
    amount_entry = tk.Entry(deposit_win)
    amount_entry.pack(pady=5)

    def confirm_deposit():
        try:
            amount = float(amount_entry.get())
            if amount <= 0:
                messagebox.showwarning("Invalid Amount", "Please enter a positive amount.")
                return

            # Update balance in database
            update_user_balance(user_id, amount, db, cursor)

            # Refresh displayed balance
            new_balance = get_user_balance(user_id, cursor)
            balance_var.set(f"${new_balance:,.2f}")

            messagebox.showinfo("Success", f"Deposited ${amount:,.2f} successfully!")
            deposit_win.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")

    tk.Button(deposit_win, text="Confirm", command=confirm_deposit).pack(pady=10)
    tk.Button(deposit_win, text="Cancel", command=deposit_win.destroy).pack()


def get_user_balance(user_id, cursor):
    """Fetch the user's balance from the database."""
    try:
        cursor.execute("SELECT userBalance FROM bankBalance WHERE userID = %s", (user_id,))
        result = cursor.fetchone()
        return float(result[0]) if result else 0.00
    except Exception as e:
        print("Database error while getting balance:", e)
        return 0.00


def update_user_balance(user_id, amount, db, cursor):
    """Deposit money — creates a balance record if one doesn't exist yet."""
    try:
        # Check if the record exists
        cursor.execute("SELECT userBalance FROM bankBalance WHERE userID = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            # User already has a record it'll just update it
            cursor.execute("""
                UPDATE bankBalance
                SET userBalance = userBalance + %s, lastUpdated = NOW()
                WHERE userID = %s
            """, (amount, user_id))
        else:
            # No record yet, it'll create one with the deposited amount
            cursor.execute("""
                INSERT INTO bankBalance (userID, userBalance, lastUpdated)
                VALUES (%s, %s, NOW())
            """, (user_id, amount))

        db.commit()

    except Exception as e:
        print("Error updating or creating balance record:", e)


def update_activity():
    SESSION["last_active"] = time.time()

def check_inactivity(window, root, logout_callback, user_id, cursor):
    """Check every few seconds if the user has been inactive."""
    if SESSION["last_active"] is not None:
        elapsed = time.time() - SESSION["last_active"]
        if elapsed > SESSION_TIMEOUT:
            from BankEmail import send_alert_email
            cursor.execute("SELECT email FROM bankUser WHERE idbankUser = %s", (user_id,))
            user_email = cursor.fetchone()[0]

            

            send_alert_email(
                to_email=user_email,
                subject="Logged Out Due to Inactivity",
                body="You were automatically logged out due to inactivity. If this was not you, please check your account immediately."
            )

            messagebox.showinfo("Session Expired", "You have been logged out due to inactivity.")
            logout(window, root, logout_callback)
            return
    window.after(2000, lambda: check_inactivity(window, root, logout_callback, user_id, cursor))


def logout(dashboard_window, root, logout_callback):
    """Logs out and returns to login."""
    SESSION["token"] = None
    SESSION["last_active"] = None
    dashboard_window.destroy()
    logout_callback(root)

