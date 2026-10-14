import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date

DB_URI = "postgresql://myuser:mypassword@db:5432/expensedb"
engine = create_engine(DB_URI)

st.title("ניהול הוצאות והכנסות 💸")

# --- תפריט צד להוספת חשבונות ---
st.sidebar.header("ניהול חשבונות וכרטיסים")
with st.sidebar.form("new_account"):
    st.subheader("הוספת חשבון/כרטיס חדש")
    acc_name = st.text_input("שם החשבון (למשל: בנק פועלים, ויזה מקס)")
    
    acc_type_options = {"חשבון בנק": "BANK", "כרטיס אשראי": "CREDIT_CARD"}
    acc_type_display = st.selectbox("סוג", list(acc_type_options.keys()))
    
    initial_balance = st.number_input("יתרה התחלתית (לבנק) / נוכחית", value=0.0)
    credit_limit = st.number_input("מסגרת אשראי (לכרטיס בלבד, 0 לבנק)", value=0.0)
    
    submit_acc = st.form_submit_button("הוסף חשבון")
    
    if submit_acc and acc_name:
        actual_acc_type = acc_type_options[acc_type_display]
        insert_acc_query = f"""
        INSERT INTO Dim_Accounts (account_name, account_type, credit_limit, initial_balance)
        VALUES ('{acc_name}', '{actual_acc_type}', {credit_limit}, {initial_balance});
        """
        with engine.connect() as conn:
            conn.execute(text(insert_acc_query))
            conn.commit() # שמירה מפורשת
        st.sidebar.success("החשבון נוסף בהצלחה!")
        st.rerun()

# --- חישוב יתרות עדכניות ---
live_balance_query = """
SELECT 
    a.account_id,
    a.account_name AS "שם חשבון", 
    CASE WHEN a.account_type = 'BANK' THEN 'בנק' ELSE 'אשראי' END AS "סוג",
    a.credit_limit AS "מסגרת",
    a.initial_balance AS "יתרה התחלתית",
    COALESCE(SUM(t.amount), 0) AS "סך תנועות",
    CASE 
        WHEN a.account_type = 'BANK' THEN a.initial_balance + COALESCE(SUM(t.amount), 0)
        ELSE a.credit_limit + COALESCE(SUM(t.amount), 0)
    END AS "יתרה עדכנית"
FROM Dim_Accounts a
LEFT JOIN Fact_Transactions t ON a.account_id = t.account_id
GROUP BY a.account_id, a.account_name, a.account_type, a.credit_limit, a.initial_balance
ORDER BY a.account_id;
"""

balance_df = pd.read_sql(live_balance_query, engine)

if balance_df.empty:
    st.warning("👋 ברוכים הבאים! כדי להתחיל, הוסיפו חשבון בנק או כרטיס אשראי בתפריט הצדדי.")
else:
    st.header("מצב החשבונות (מעודכן בזמן אמת)")
    st.dataframe(balance_df[["שם חשבון", "סוג", "מסגרת", "יתרה התחלתית", "סך תנועות", "יתרה עדכנית"]])
    
    st.header("הזנת תנועה חדשה")
    with st.form("new_transaction"):
        account_options = dict(zip(balance_df['שם חשבון'], balance_df['account_id']))
        selected_account_name = st.selectbox("בחר חשבון/אשראי", options=list(account_options.keys()))
        
        t_date = st.date_input("תאריך", date.today())
        description = st.text_input("תיאור (למשל: סופר, פילאטיס, משכורת)")
        amount = st.number_input("סכום (מינוס להוצאה, פלוס להכנסה)", value=0.0, step=10.0)
        
        category_type = st.selectbox("סוג הוצאה", ["קבועה", "משתנה"])
        is_luxury = st.checkbox("מותרות?")
        
        submitted = st.form_submit_button("שמור תנועה")
        
        if submitted:
            account_id = account_options[selected_account_name]
            db_category = "Fixed" if category_type == "קבועה" else "Variable"
            
            insert_query = f"""
            INSERT INTO Fact_Transactions (account_id, transaction_date, description, amount, category_type, is_luxury)
            VALUES ({account_id}, '{t_date}', '{description}', {amount}, '{db_category}', {is_luxury});
            """
            
            # הכרחת שמירה של הנתונים
            with engine.connect() as conn:
                conn.execute(text(insert_query))
                conn.commit() 
            
            st.success("התנועה נשמרה בהצלחה!")
            st.rerun()

    # --- תצוגת היסטוריית תנועות ---
    st.header("היסטוריית תנועות")
    history_query = """
    SELECT 
        t.transaction_date AS "תאריך",
        a.account_name AS "חשבון",
        t.description AS "תיאור",
        t.amount AS "סכום",
        CASE WHEN t.category_type = 'Fixed' THEN 'קבועה' ELSE 'משתנה' END AS "סוג הוצאה",
        CASE WHEN t.is_luxury THEN 'כן' ELSE 'לא' END AS "מותרות"
    FROM Fact_Transactions t
    JOIN Dim_Accounts a ON t.account_id = a.account_id
    ORDER BY t.transaction_date DESC, t.transaction_id DESC;
    """
    history_df = pd.read_sql(history_query, engine)
    
    if not history_df.empty:
        st.dataframe(history_df)
    else:
        st.info("עדיין אין תנועות במערכת.")