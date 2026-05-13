import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
import bcrypt
from datetime import date, datetime

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Student Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- LOAD CSS ---------------- #

def load_css():

    with open("assets/styles.css") as f:

        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css()

# ---------------- DATABASE SETUP ---------------- #

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB
)
""")

# EXPENSES TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    category TEXT,
    note TEXT,
    expense_date TEXT
)
""")

# BUDGET TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    monthly_budget REAL,
    month INTEGER,
    year INTEGER
)
""")

conn.commit()
conn.close()

# ---------------- AUTH FUNCTIONS ---------------- #

def register_user(username, password):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    try:

        cursor.execute(
            """
            INSERT INTO users
            (username, password)
            VALUES (?, ?)
            """,
            (username, hashed_password)
        )

        conn.commit()

        return True

    except:

        return False

    finally:

        conn.close()


def login_user(username, password):

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM users
        WHERE username = ?
        """,
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        stored_password = user[2]

        if bcrypt.checkpw(
            password.encode(),
            stored_password
        ):

            return user

    return None

# ---------------- SESSION STATE ---------------- #

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

if "user_id" not in st.session_state:

    st.session_state.user_id = None

if "username" not in st.session_state:

    st.session_state.username = ""

# ---------------- LOGIN PAGE ---------------- #

if not st.session_state.logged_in:

    st.title("💰 Student Expense Tracker")

    st.subheader(
        "Professional Monthly Expense Manager"
    )

    tab1, tab2 = st.tabs([
        "Login",
        "Register"
    ])

    # LOGIN
    with tab1:

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login"):

            user = login_user(
                username,
                password
            )

            if user:

                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]

                st.success(
                    "Login Successful!"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password"
                )

    # REGISTER
    with tab2:

        new_username = st.text_input(
            "Create Username"
        )

        new_password = st.text_input(
            "Create Password",
            type="password"
        )

        if st.button("Register"):

            success = register_user(
                new_username,
                new_password
            )

            if success:

                st.success(
                    "Account created successfully!"
                )

            else:

                st.error(
                    "Username already exists"
                )

# ---------------- MAIN APP ---------------- #

else:

    st.sidebar.title("Navigation")

    st.sidebar.success(
        f"Logged in as: {st.session_state.username}"
    )

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""

        st.rerun()

    page = st.sidebar.radio(
        "Go to",
        [
            "Dashboard",
            "Add Expense",
            "Expense History",
            "Analytics",
            "Currency Converter"
        ]
    )

    # ---------------- DASHBOARD ---------------- #

    if page == "Dashboard":

        st.title("📊 Dashboard")

        current_month = datetime.now().month
        current_year = datetime.now().year

        conn = sqlite3.connect("expenses.db")

        df = pd.read_sql_query(
            f"""
            SELECT *
            FROM expenses
            WHERE user_id = {st.session_state.user_id}
            AND strftime('%m', expense_date)
            = '{current_month:02d}'
            AND strftime('%Y', expense_date)
            = '{current_year}'
            """,
            conn
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT monthly_budget
            FROM budget
            WHERE user_id = ?
            AND month = ?
            AND year = ?
            """,
            (
                st.session_state.user_id,
                current_month,
                current_year
            )
        )

        budget_data = cursor.fetchone()

        if not budget_data:

            st.warning(
                "No budget set for this month."
            )

            monthly_budget = st.number_input(
                "Enter Monthly Budget",
                min_value=0.0
            )

            if st.button(
                "Save Monthly Budget"
            ):

                cursor.execute(
                    """
                    INSERT INTO budget
                    (
                        user_id,
                        monthly_budget,
                        month,
                        year
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        st.session_state.user_id,
                        monthly_budget,
                        current_month,
                        current_year
                    )
                )

                conn.commit()

                st.success(
                    "Monthly budget saved!"
                )

                st.rerun()

        else:

            monthly_budget = budget_data[0]

            total_expense = (
                df["amount"].sum()
                if not df.empty
                else 0
            )

            remaining_budget = (
                monthly_budget - total_expense
            )

            highest_category = (
                df.groupby("category")["amount"]
                .sum()
                .idxmax()
                if not df.empty
                else "N/A"
            )

            # DASHBOARD CARDS

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                with st.container(border=True):

                    st.markdown("""
                    <h1 style="
                        font-size:24px;
                        font-weight:600;
                    ">
                        Budget
                    </h1>
                    """, unsafe_allow_html=True)

                    st.markdown(
                        f"""
                        <p style="
                            font-size:20px;
                            color:#D1D5DB;
                        ">
                            ₹{monthly_budget:.2f}
                        </p>
                        """,
                        unsafe_allow_html=True
                    )

            with col2:

                with st.container(border=True):

                    st.markdown("""
                    <h1 style="
                        font-size:24px;
                        font-weight:600;
                    ">
                        Total Spent
                    </h1>
                    """, unsafe_allow_html=True)

                    st.markdown(
                        f"""
                        <p style="
                            font-size:20px;
                            color:#D1D5DB;
                        ">
                            ₹{total_expense:.2f}
                        </p>
                        """,
                        unsafe_allow_html=True
                    )

            with col3:

                with st.container(border=True):

                    st.markdown("""
                    <h1 style="
                        font-size:24px;
                        font-weight:600;
                    ">
                        Remaining
                    </h1>
                    """, unsafe_allow_html=True)

                    st.markdown(
                        f"""
                        <p style="
                            font-size:20px;
                            color:#D1D5DB;
                        ">
                            ₹{remaining_budget:.2f}
                        </p>
                        """,
                        unsafe_allow_html=True
                    )

            with col4:

                with st.container(border=True):

                    st.markdown("""
                    <h1 style="
                        font-size:20px;
                        font-weight:600;
                    ">
                        Highest Category
                    </h1>
                    """, unsafe_allow_html=True)

                    st.markdown(
                        f"""
                        <p style="
                            font-size:20px;
                            color:#D1D5DB;
                        ">
                            {highest_category}
                        </p>
                        """,
                        unsafe_allow_html=True
                    )

            if remaining_budget < 0:

                st.error(
                    "Budget exceeded!"
                )

        conn.close()

    # ---------------- ADD EXPENSE ---------------- #

    elif page == "Add Expense":

        st.title("Add Expense")

        amount = st.number_input(
            "Amount",
            min_value=0.0,
            format="%.2f"
        )

        category = st.selectbox(
            "Category",
            [
                "Food",
                "Travel",
                "Shopping",
                "Education",
                "Entertainment",
                "Bills",
                "Others"
            ]
        )

        expense_date = st.date_input(
            "Expense Date",
            value=date.today()
        )

        note = st.text_area("Note")

        if st.button("Add Expense"):

            conn = sqlite3.connect("expenses.db")
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO expenses
                (
                    user_id,
                    amount,
                    category,
                    note,
                    expense_date
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    st.session_state.user_id,
                    amount,
                    category,
                    note,
                    str(expense_date)
                )
            )

            conn.commit()
            conn.close()

            st.success(
                "Expense added successfully!"
            )

    # ---------------- EXPENSE HISTORY ---------------- #

    elif page == "Expense History":

        st.title("Expense History")

        conn = sqlite3.connect("expenses.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM expenses
            WHERE user_id = ?
            ORDER BY expense_date DESC
            """,
            (st.session_state.user_id,)
        )

        data = cursor.fetchall()

        df = pd.DataFrame(
            data,
            columns=[
                "ID",
                "User ID",
                "Amount",
                "Category",
                "Note",
                "Date"
            ]
        )

        if not df.empty:

            csv = df.to_csv(
                index=False
            ).encode('utf-8')

            st.download_button(
                label="Download Expense Report",
                data=csv,
                file_name="expense_report.csv",
                mime="text/csv"
            )

            st.markdown(
                "### Expense Records"
            )

            col1, col2, col3, col4, col5 = st.columns(
                [1.2, 1.5, 2, 1.5, 1]
            )

            col1.markdown("**Amount**")
            col2.markdown("**Category**")
            col3.markdown("**Note**")
            col4.markdown("**Date**")
            col5.markdown("**Action**")

            st.divider()

            for expense in data:

                col1, col2, col3, col4, col5 = st.columns(
                    [1.2, 1.5, 2, 1.5, 1]
                )

                col1.write(
                    f"₹{expense[2]}"
                )

                col2.write(
                    expense[3]
                )

                col3.write(
                    expense[4]
                )

                col4.write(
                    expense[5]
                )

                if col5.button(
                    "Delete",
                    key=expense[0]
                ):

                    cursor.execute(
                        """
                        DELETE FROM expenses
                        WHERE id = ?
                        """,
                        (expense[0],)
                    )

                    conn.commit()

                    st.success(
                        "Expense deleted!"
                    )

                    st.rerun()

                st.markdown(
                    "<hr style='margin:5px 0;'>",
                    unsafe_allow_html=True
                )

        else:

            st.info(
                "No expenses added yet."
            )

        conn.close()

    # ---------------- ANALYTICS ---------------- #

    elif page == "Analytics":

        st.title("Expense Analytics")

        current_month = datetime.now().month
        current_year = datetime.now().year

        conn = sqlite3.connect("expenses.db")

        df = pd.read_sql_query(
            f"""
            SELECT amount, category
            FROM expenses
            WHERE user_id = {st.session_state.user_id}
            AND strftime('%m', expense_date)
            = '{current_month:02d}'
            AND strftime('%Y', expense_date)
            = '{current_year}'
            """,
            conn
        )

        conn.close()

        if not df.empty:

            df["category"] = (
                df["category"]
                .str.strip()
                .str.title()
            )

            category_data = (
                df.groupby("category")["amount"]
                .sum()
                .reset_index()
            )

            pie_chart = px.pie(
                category_data,
                values="amount",
                names="category",
                hole=0.4,
                title="Expense Distribution"
            )

            st.plotly_chart(
                pie_chart,
                use_container_width=True
            )

            bar_chart = px.bar(
                category_data,
                x="category",
                y="amount",
                title="Category-wise Spending"
            )

            st.plotly_chart(
                bar_chart,
                use_container_width=True
            )

        else:

            st.info(
                "No expense data available."
            )

    # ---------------- CURRENCY CONVERTER ---------------- #

    elif page == "Currency Converter":

        st.title("Currency Converter")

        amount = st.number_input(
            "Enter Amount",
            min_value=1.0
        )

        from_currency = st.selectbox(
            "From Currency",
            [
                "INR",
                "USD",
                "EUR",
                "GBP",
                "JPY",
                "KWD"
            ]
        )

        to_currency = st.selectbox(
            "To Currency",
            [
                "USD",
                "INR",
                "EUR",
                "GBP",
                "JPY",
                "KWD"
            ]
        )

        if st.button(
            "Convert Currency"
        ):

            url = (
                f"https://api.exchangerate-api.com/v4/latest/"
                f"{from_currency}"
            )

            response = requests.get(url)

            data = response.json()

            rate = data["rates"][to_currency]

            converted_amount = (
                amount * rate
            )

            st.success(
                f"{amount} {from_currency} = "
                f"{converted_amount:.2f} {to_currency}"
            )