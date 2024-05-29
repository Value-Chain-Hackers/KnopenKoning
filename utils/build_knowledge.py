
import sqlite3
import os
from datetime import datetime

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn

def cikLookup(name):
    conn = create_connection('data\\sec_cik\\sec_cik.db')
    cur = conn.cursor()
    cur.execute("SELECT cik, name FROM cik_lookup WHERE name like ?", ('%' + name.upper() + '%',))
    rows = cur.fetchall()
    return rows

def get_knowledge_from_wikipedia(search_term):
    import wikipedia
    wikipedia.set_lang("en")
    search_results = wikipedia.search(search_term)
    if not search_results:
        return None
    pages = []
    for result in search_results:
        try:
            page = wikipedia.page(result)
            pages.append(page.content)
        except Exception as e:
            continue
    return pages