import sqlite3

# Create a connection to the SQLite database (or create it)
conn = sqlite3.connect('sec_cik.db')
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS cik_lookup (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    CIK TEXT NOT NULL,
    NAME TEXT NOT NULL
)
""")


with open("cik-lookup-data (1).txt", "r", encoding="cp1252") as file:
    data = file.read()

# Split the data into lines and parse each line
lines = data.strip().split('\n')
for line in lines:
    parts = line.split(':')
    if len(parts) == 3:
        company_name = parts[0]
        sic = parts[1]
        cursor.execute('INSERT INTO cik_lookup (NAME, CIK) VALUES (?, ?)', (company_name, sic))
    else:
        assert("Failed not enough fields")
# Commit the changes and close the connection
conn.commit()
conn.close()