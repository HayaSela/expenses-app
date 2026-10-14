-- יצירת טבלת החשבונות (Dim_Accounts)
CREATE TABLE Dim_Accounts (
    account_id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(50) NOT NULL, -- 'BANK' or 'CREDIT_CARD'
    credit_limit NUMERIC(10, 2) DEFAULT 0,
    initial_balance NUMERIC(10, 2) DEFAULT 0
);

-- יצירת טבלת התנועות (Fact_Transactions)
CREATE TABLE Fact_Transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INT REFERENCES Dim_Accounts(account_id),
    transaction_date DATE NOT NULL,
    description VARCHAR(255) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    category_type VARCHAR(50), -- 'Fixed' or 'Variable'
    is_luxury BOOLEAN DEFAULT FALSE,
    is_cleared BOOLEAN DEFAULT FALSE,
    refund_amount NUMERIC(10, 2) DEFAULT 0
);

