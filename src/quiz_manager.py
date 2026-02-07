import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

# --- Datenbank-Manager ---
class DatabaseManager:
    def __init__(self, db_name="quiz_app.db", schema_file="schema.sql"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        
        # Prüfen, ob die Tabellen existieren, sonst schema.sql ausführen
        try:
            self.cursor.execute("SELECT * FROM Konfiguration")
        except sqlite3.OperationalError:
            self.initialize_db(schema_file)

    def initialize_db(self, schema_file):
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            self.cursor.executescript(sql_script)
            self.conn.commit()
            print("Datenbank wurde erfolgreich aus schema.sql neu erstellt.")
        else:
            messagebox.showerror("Fehler", f"Datei '{schema_file}' nicht gefunden! Bitte erstellen Sie diese Datei mit dem SQL-Code.")

    def execute(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except sqlite3.IntegrityError as e:
            raise e
        except sqlite3.Error as e:
            messagebox.showerror("Datenbankfehler", str(e))

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

# --- GUI Anwendung ---
class QuizApp:
    def __init__(self, root):
        self.db = DatabaseManager()
        self.root = root
        self.root.title("Quiz App Manager (Teil 1 - Angepasst)")
        self.root.geometry("900x600")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')

        self.setup_category_tab()
        self.setup_question_tab()

    # --- Tab: Kategorien verwalten ---
    def setup_category_tab(self):
        self.cat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cat_frame, text="Kategorien verwalten")

        # Eingabebereich
        input_frame = ttk.Frame(self.cat_frame, padding=10)
        input_frame.pack(fill='x')
        
        ttk.Label(input_frame, text="Kategorie Name:").pack(side='left')
        self.cat_entry = ttk.Entry(input_frame)
        self.cat_entry.pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(input_frame, text="Hinzufügen", command=self.add_category).pack(side='left')

        # Listenbereich
        self.cat_list = tk.Listbox(self.cat_frame)
        self.cat_list.pack(expand=True, fill='both', padx=10, pady=5)
        
        btn_frame = ttk.Frame(self.cat_frame, padding=10)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="Markierte löschen", command=self.delete_category).pack(side='right')

        self.refresh_categories()

    def add_category(self):
        name = self.cat_entry.get()
        if name:
            try:
                # Angepasst an neue Tabelle: Kategorie (Bezeichnung)
                self.db.execute("INSERT INTO Kategorie (Bezeichnung) VALUES (?)", (name,))
                self.cat_entry.delete(0, 'end')
                self.refresh_categories()
                self.refresh_dropdowns()
            except sqlite3.IntegrityError:
                messagebox.showerror("Fehler", "Kategorie existiert bereits!")

    def delete_category(self):
        selection = self.cat_list.curselection()
        if selection:
            cat_text = self.cat_list.get(selection[0])
            cat_id = cat_text.split(":")[0]
            # Angepasst: Tabelle Kategorie
            try:
                self.db.execute("DELETE FROM Kategorie WHERE KategorieID=?", (cat_id,))
                self.refresh_categories()
                self.refresh_dropdowns()
            except sqlite3.Error:
                messagebox.showerror("Fehler", "Kategorie kann nicht gelöscht werden (wird evtl. noch verwendet).")

    def refresh_categories(self):
        self.cat_list.delete(0, 'end')
        cats = self.db.fetch_all("SELECT KategorieID, Bezeichnung FROM Kategorie")
        for cat in cats:
            self.cat_list.insert('end', f"{cat[0]}: {cat[1]}")

    # --- Tab: Fragen verwalten ---
    def setup_question_tab(self):
        self.q_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.q_frame, text="Fragen & Antworten verwalten")

        # Formular
        form_frame = ttk.LabelFrame(self.q_frame, text="Frage erstellen / bearbeiten", padding=10)
        form_frame.pack(fill='x', padx=10, pady=5)

        # Kategorie Auswahl
        ttk.Label(form_frame, text="Kategorie:").grid(row=0, column=0, sticky='w')
        self.q_cat_combo = ttk.Combobox(form_frame, state="readonly")
        self.q_cat_combo.grid(row=0, column=1, sticky='ew', padx=5)

        # Schwierigkeit Auswahl (Jetzt neu: Aus DB Tabelle Schwierigkeitsgrad)
        ttk.Label(form_frame, text="Schwierigkeit:").grid(row=0, column=2, sticky='w')
        self.q_diff_combo = ttk.Combobox(form_frame, state="readonly")
        self.q_diff_combo.grid(row=0, column=3, sticky='w', padx=5)

        # Fragetext
        ttk.Label(form_frame, text="Frage:").grid(row=1, column=0, sticky='ne')
        self.q_text = tk.Text(form_frame, height=3, width=50)
        self.q_text.grid(row=1, column=1, columnspan=3, sticky='ew', padx=5, pady=5)

        ttk.Button(form_frame, text="Frage speichern", command=self.save_question).grid(row=2, column=1, sticky='w')

        # Fragen Liste
        columns = ("ID", "Kategorie", "Level", "Text")
        self.q_tree = ttk.Treeview(self.q_frame, columns=columns, show='headings')
        self.q_tree.heading("ID", text="ID")
        self.q_tree.heading("Kategorie", text="Kategorie")
        self.q_tree.heading("Level", text="Level")
        self.q_tree.heading("Text", text="Frage")
        
        self.q_tree.column("ID", width=30)
        self.q_tree.column("Kategorie", width=120)
        self.q_tree.column("Level", width=80)
        self.q_tree.pack(expand=True, fill='both', padx=10, pady=5)

        # Aktionen
        action_frame = ttk.Frame(self.q_frame, padding=10)
        action_frame.pack(fill='x')
        ttk.Button(action_frame, text="Antworten verwalten (Auswahl)", command=self.manage_answers).pack(side='left')
        ttk.Button(action_frame, text="Frage löschen", command=self.delete_question).pack(side='right')

        self.refresh_dropdowns()
        self.refresh_questions()

    def refresh_dropdowns(self):
        # Kategorien laden
        cats = self.db.fetch_all("SELECT KategorieID, Bezeichnung FROM Kategorie")
        self.cat_map = {name: id for id, name in cats}
        self.q_cat_combo['values'] = list(self.cat_map.keys())

        # Schwierigkeitsgrade laden
        diffs = self.db.fetch_all("SELECT SchwierigkeitID, Bezeichnung FROM Schwierigkeitsgrad")
        self.diff_map = {name: id for id, name in diffs}
        self.q_diff_combo['values'] = list(self.diff_map.keys())

    def save_question(self):
        cat_name = self.q_cat_combo.get()
        diff_name = self.q_diff_combo.get()
        text = self.q_text.get("1.0", 'end-1c').strip()

        if not cat_name or not diff_name or not text:
            messagebox.showwarning("Unvollständig", "Bitte alle Felder ausfüllen.")
            return

        cat_id = self.cat_map[cat_name]
        diff_id = self.diff_map[diff_name]

        # Insert in neue Tabellenstruktur
        self.db.execute(
            "INSERT INTO Frage (FrageText, KategorieID, SchwierigkeitID) VALUES (?, ?, ?)", 
            (text, cat_id, diff_id)
        )
        self.q_text.delete("1.0", 'end')
        self.refresh_questions()

    def refresh_questions(self):
        for row in self.q_tree.get_children():
            self.q_tree.delete(row)
        
        # Join über die 3 Tabellen für die Anzeige
        query = """
            SELECT f.FrageID, k.Bezeichnung, s.Bezeichnung, f.FrageText 
            FROM Frage f
            JOIN Kategorie k ON f.KategorieID = k.KategorieID
            JOIN Schwierigkeitsgrad s ON f.SchwierigkeitID = s.SchwierigkeitID
        """
        questions = self.db.fetch_all(query)
        for q in questions:
            self.q_tree.insert("", "end", values=q)

    def delete_question(self):
        selected = self.q_tree.selection()
        if selected:
            q_id = self.q_tree.item(selected[0])['values'][0]
            # Dank ON DELETE CASCADE im SQL Skript werden Antworten automatisch gelöscht
            self.db.execute("DELETE FROM Frage WHERE FrageID=?", (q_id,))
            self.refresh_questions()

    # --- Antworten verwalten ---
    def manage_answers(self):
        selected = self.q_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Bitte erst eine Frage aus der Liste auswählen.")
            return
        
        q_id = self.q_tree.item(selected[0])['values'][0]
        q_text = self.q_tree.item(selected[0])['values'][3]

        win = tk.Toplevel(self.root)
        win.title(f"Antworten für: {q_text[:30]}...")
        win.geometry("600x400")

        # Antwort Eingabe
        input_frame = ttk.Frame(win, padding=10)
        input_frame.pack(fill='x')
        ttk.Label(input_frame, text="Antwort Text:").pack(anchor='w')
        ans_entry = ttk.Entry(input_frame)
        ans_entry.pack(fill='x', pady=2)
        
        is_correct_var = tk.BooleanVar()
        tk.Checkbutton(input_frame, text="Ist korrekte Antwort?", variable=is_correct_var).pack(anchor='w')

        def add_ans():
            if ans_entry.get():
                # Angepasst: Tabelle Antwort (AntwortText, IstRichtig, FrageID)
                self.db.execute(
                    "INSERT INTO Antwort (AntwortText, IstRichtig, FrageID) VALUES (?, ?, ?)",
                    (ans_entry.get(), is_correct_var.get(), q_id)
                )
                ans_entry.delete(0, 'end')
                is_correct_var.set(False)
                refresh_ans()

        ttk.Button(input_frame, text="Antwort hinzufügen", command=add_ans).pack(anchor='w', pady=5)

        # Antwort Liste
        ans_list = tk.Listbox(win)
        ans_list.pack(expand=True, fill='both', padx=10, pady=5)

        def refresh_ans():
            ans_list.delete(0, 'end')
            answers = self.db.fetch_all("SELECT AntwortText, IstRichtig FROM Antwort WHERE FrageID=?", (q_id,))
            for ans in answers:
                status = "[RICHTIG]" if ans[1] else "[FALSCH]"
                ans_list.insert('end', f"{status} {ans[0]}")

        refresh_ans()

if __name__ == "__main__":
    # Stellt sicher, dass wir im richtigen Verzeichnis arbeiten
    if not os.path.exists("schema.sql"):
        # Fallback: Warnung falls Datei fehlt
        print("ACHTUNG: 'schema.sql' nicht gefunden. Bitte erstellen Sie die Datei im selben Ordner.")
    
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()