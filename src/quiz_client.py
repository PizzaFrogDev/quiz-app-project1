#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quiz App Client - Hauptanwendung
Unterstützt Duell-Modus und Statistiken
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import random
from datetime import datetime
import os


class DatabaseConnection:
    """Datenbank-Verbindungsklasse mit Context Manager Support"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()


class QuizDatabase:
    """Datenbank-Handler für Quiz-Operationen"""
    
    def __init__(self, db_path="../database/quiz_app.db"):
        self.db_path = db_path
        
    def hash_password(self, password):
        """Erstellt SHA256 Hash für Passwort"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password):
        """Registriert neuen Benutzer"""
        try:
            with DatabaseConnection(self.db_path) as db:
                password_hash = self.hash_password(password)
                db.cursor.execute(
                    "INSERT INTO Spieler (Username, PasswortHash) VALUES (?, ?)",
                    (username, password_hash)
                )
                db.conn.commit()
                return True, "Registrierung erfolgreich!"
        except sqlite3.IntegrityError:
            return False, "Username bereits vergeben!"
        except Exception as e:
            return False, f"Fehler: {str(e)}"
    
    def login_user(self, username, password):
        """Authentifiziert Benutzer"""
        try:
            with DatabaseConnection(self.db_path) as db:
                password_hash = self.hash_password(password)
                db.cursor.execute(
                    "SELECT SpielerID, Username FROM Spieler WHERE Username=? AND PasswortHash=?",
                    (username, password_hash)
                )
                result = db.cursor.fetchone()
                
                if result:
                    # Session Key generieren
                    session_key = hashlib.sha256(f"{username}{datetime.now()}".encode()).hexdigest()
                    db.cursor.execute(
                        "UPDATE Spieler SET SessionKey=?, SessionTime=? WHERE SpielerID=?",
                        (session_key, datetime.now(), result[0])
                    )
                    db.conn.commit()
                    return True, result[0], result[1]
                else:
                    return False, None, "Falsche Anmeldedaten!"
        except Exception as e:
            return False, None, f"Fehler: {str(e)}"
    
    def get_categories(self):
        """Lädt alle Kategorien"""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute("SELECT KategorieID, Bezeichnung FROM Kategorie")
            return db.cursor.fetchall()
    
    def get_difficulties(self):
        """Lädt alle Schwierigkeitsgrade"""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute(
                "SELECT SchwierigkeitID, Bezeichnung, LevelWert FROM Schwierigkeitsgrad ORDER BY LevelWert"
            )
            return db.cursor.fetchall()
    
    def get_random_question(self, category_id, difficulty_id, exclude_ids=[]):
        """Holt zufällige Frage mit genau 4 Antworten"""
        with DatabaseConnection(self.db_path) as db:
            # Frage laden
            exclude_clause = ""
            params = [category_id, difficulty_id]
            
            if exclude_ids:
                placeholders = ','.join('?' * len(exclude_ids))
                exclude_clause = f"AND FrageID NOT IN ({placeholders})"
                params.extend(exclude_ids)
            
            db.cursor.execute(f"""
                SELECT FrageID, FrageText 
                FROM Frage 
                WHERE KategorieID=? AND SchwierigkeitID=? {exclude_clause}
                ORDER BY RANDOM() 
                LIMIT 1
            """, params)
            
            question = db.cursor.fetchone()
            if not question:
                return None
            
            question_id, question_text = question
            
            # Antworten laden
            db.cursor.execute("""
                SELECT AntwortID, AntwortText, IstRichtig 
                FROM Antwort 
                WHERE FrageID=?
            """, (question_id,))
            
            all_answers = db.cursor.fetchall()
            
            # Genau 1 richtige und 3 falsche auswählen
            correct = [a for a in all_answers if a[2] == 1]
            incorrect = [a for a in all_answers if a[2] == 0]
            
            if not correct or len(incorrect) < 3:
                return None  # Nicht genug Antworten
            
            selected_correct = random.choice(correct)
            selected_incorrect = random.sample(incorrect, min(3, len(incorrect)))
            
            # Kombinieren und mischen
            final_answers = [selected_correct] + selected_incorrect
            random.shuffle(final_answers)
            
            return {
                'id': question_id,
                'text': question_text,
                'answers': [(a[0], a[1]) for a in final_answers],  # Ohne IstRichtig Flag!
                'correct_id': selected_correct[0]
            }
    
    def create_game(self, player_ids, difficulty_id):
        """Erstellt neues Spiel"""
        with DatabaseConnection(self.db_path) as db:
            # Spiel erstellen
            db.cursor.execute("""
                INSERT INTO Spiel (KonfigID, GewaehlteSchwierigkeitID) 
                VALUES (1, ?)
            """, (difficulty_id,))
            
            game_id = db.cursor.lastrowid
            
            # Teilnahmen erstellen
            for player_id in player_ids:
                db.cursor.execute("""
                    INSERT INTO Teilnahme (SpielID, SpielerID, EndScore) 
                    VALUES (?, ?, 0)
                """, (game_id, player_id))
            
            db.conn.commit()
            return game_id
    
    def save_answer(self, game_id, player_id, question_id, answer_id, is_correct, round_nr):
        """Speichert Antwort in Historie"""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute("""
                INSERT INTO SpielHistorie 
                (SpielID, SpielerID, FrageID, RundeNr, GegebeneAntwortID, WarKorrekt)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (game_id, player_id, question_id, round_nr, answer_id, is_correct))
            
            # Score aktualisieren
            if is_correct:
                db.cursor.execute("""
                    UPDATE Teilnahme 
                    SET EndScore = EndScore + 10 
                    WHERE SpielID=? AND SpielerID=?
                """, (game_id, player_id))
            
            db.conn.commit()
    
    def get_game_scores(self, game_id):
        """Holt aktuelle Spielstände"""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute("""
                SELECT s.Username, t.EndScore 
                FROM Teilnahme t
                JOIN Spieler s ON t.SpielerID = s.SpielerID
                WHERE t.SpielID=?
                ORDER BY t.EndScore DESC
            """, (game_id,))
            return db.cursor.fetchall()
    
    def finish_game(self, game_id):
        """Beendet Spiel"""
        with DatabaseConnection(self.db_path) as db:
            db.cursor.execute("""
                UPDATE Spiel SET EndZeit=? WHERE SpielID=?
            """, (datetime.now(), game_id))
            db.conn.commit()
    
    def get_user_statistics(self, player_id):
        """Holt Benutzerstatistiken"""
        with DatabaseConnection(self.db_path) as db:
            # Gespielte Spiele
            db.cursor.execute("""
                SELECT COUNT(DISTINCT SpielID) FROM Teilnahme WHERE SpielerID=?
            """, (player_id,))
            games_played = db.cursor.fetchone()[0]
            
            # Gewonnene Duelle
            db.cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT t1.SpielID
                    FROM Teilnahme t1
                    WHERE t1.SpielerID=? 
                    AND t1.EndScore = (
                        SELECT MAX(t2.EndScore) 
                        FROM Teilnahme t2 
                        WHERE t2.SpielID = t1.SpielID
                    )
                    AND (SELECT COUNT(*) FROM Teilnahme t3 WHERE t3.SpielID = t1.SpielID) > 1
                )
            """, (player_id,))
            duels_won = db.cursor.fetchone()[0]
            
            # Richtige Antworten
            db.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN WarKorrekt=1 THEN 1 ELSE 0 END) as correct
                FROM SpielHistorie 
                WHERE SpielerID=?
            """, (player_id,))
            
            result = db.cursor.fetchone()
            total_answers = result[0] if result[0] else 0
            correct_answers = result[1] if result[1] else 0
            
            percentage = (correct_answers / total_answers * 100) if total_answers > 0 else 0
            
            return {
                'games_played': games_played,
                'duels_won': duels_won,
                'total_answers': total_answers,
                'correct_answers': correct_answers,
                'percentage': percentage
            }
    
    def get_all_users(self, exclude_id=None):
        """Holt alle Benutzer (für Duell-Auswahl)"""
        with DatabaseConnection(self.db_path) as db:
            if exclude_id:
                db.cursor.execute(
                    "SELECT SpielerID, Username FROM Spieler WHERE SpielerID != ?",
                    (exclude_id,)
                )
            else:
                db.cursor.execute("SELECT SpielerID, Username FROM Spieler")
            return db.cursor.fetchall()


class LoginWindow:
    """Login/Registrierungs-Fenster"""
    
    def __init__(self, parent, db, on_success):
        self.parent = parent
        self.db = db
        self.on_success = on_success
        
        self.window = tk.Toplevel(parent)
        self.window.title("Quiz App - Login")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        # Zentrieren
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (300 // 2)
        self.window.geometry(f'400x300+{x}+{y}')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = ttk.Label(
            self.window, 
            text="🎯 Quiz App", 
            font=('Arial', 24, 'bold')
        )
        header.pack(pady=20)
        
        # Login Frame
        login_frame = ttk.LabelFrame(self.window, text="Anmeldung", padding=20)
        login_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Username
        ttk.Label(login_frame, text="Benutzername:").grid(row=0, column=0, sticky='w', pady=5)
        self.username_entry = ttk.Entry(login_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # Password
        ttk.Label(login_frame, text="Passwort:").grid(row=1, column=0, sticky='w', pady=5)
        self.password_entry = ttk.Entry(login_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Buttons
        btn_frame = ttk.Frame(login_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            btn_frame, 
            text="Anmelden", 
            command=self.login,
            width=12
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Registrieren", 
            command=self.register,
            width=12
        ).pack(side='left', padx=5)
        
        # Enter-Taste für Login
        self.password_entry.bind('<Return>', lambda e: self.login())
        
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Eingabe fehlt", "Bitte alle Felder ausfüllen!")
            return
        
        success, player_id, message = self.db.login_user(username, password)
        
        if success:
            self.window.destroy()
            self.on_success(player_id, username)
        else:
            messagebox.showerror("Login fehlgeschlagen", message)
    
    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Eingabe fehlt", "Bitte alle Felder ausfüllen!")
            return
        
        if len(password) < 4:
            messagebox.showwarning("Passwort zu kurz", "Passwort muss mindestens 4 Zeichen haben!")
            return
        
        success, message = self.db.register_user(username, password)
        
        if success:
            messagebox.showinfo("Erfolg", "Registrierung erfolgreich! Bitte jetzt anmelden.")
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')
        else:
            messagebox.showerror("Registrierung fehlgeschlagen", message)


class GameWindow:
    """Hauptfenster für Quiz-Spiel"""
    
    def __init__(self, parent, db, player_id, username, is_duel=False, opponent_id=None, opponent_name=None, category_id=None, difficulty_id=None):
        self.parent = parent
        self.db = db
        self.player_id = player_id
        self.username = username
        self.is_duel = is_duel
        self.opponent_id = opponent_id
        self.opponent_name = opponent_name
        self.category_id = category_id
        self.difficulty_id = difficulty_id
        
        self.game_id = None
        self.current_question = None
        self.current_round = 1
        self.max_rounds = 5
        self.asked_questions = []
        self.timer_seconds = 30
        self.timer_id = None
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Quiz Spiel - {username}")
        self.window.geometry("700x600")
        
        self.setup_ui()
        self.start_game()
        
    def setup_ui(self):
        # Header mit Spielinfo
        self.header_frame = ttk.Frame(self.window)
        self.header_frame.pack(fill='x', padx=10, pady=10)
        
        self.round_label = ttk.Label(
            self.header_frame, 
            text=f"Runde 1/{self.max_rounds}",
            font=('Arial', 12, 'bold')
        )
        self.round_label.pack(side='left')
        
        self.timer_label = ttk.Label(
            self.header_frame,
            text="⏱️ 30s",
            font=('Arial', 12),
            foreground='green'
        )
        self.timer_label.pack(side='right')
        
        # Score Frame
        self.score_frame = ttk.LabelFrame(self.window, text="Punktestand", padding=10)
        self.score_frame.pack(fill='x', padx=10, pady=5)
        
        self.score_label = ttk.Label(
            self.score_frame,
            text=f"{self.username}: 0",
            font=('Arial', 11)
        )
        self.score_label.pack()
        
        if self.is_duel:
            self.opponent_score_label = ttk.Label(
                self.score_frame,
                text=f"{self.opponent_name}: 0",
                font=('Arial', 11)
            )
            self.opponent_score_label.pack()
        
        # Frage Frame
        self.question_frame = ttk.LabelFrame(self.window, text="Frage", padding=15)
        self.question_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.question_label = ttk.Label(
            self.question_frame,
            text="Frage wird geladen...",
            font=('Arial', 13),
            wraplength=650,
            justify='center'
        )
        self.question_label.pack(pady=20)
        
        # Antwort Buttons
        self.answer_buttons = []
        for i in range(4):
            btn = ttk.Button(
                self.question_frame,
                text=f"Antwort {i+1}",
                command=lambda idx=i: self.check_answer(idx),
                width=60
            )
            btn.pack(pady=8, padx=20)
            self.answer_buttons.append(btn)
        
        # Feedback Label
        self.feedback_label = ttk.Label(
            self.window,
            text="",
            font=('Arial', 11, 'bold')
        )
        self.feedback_label.pack(pady=5)
        
    def start_game(self):
        """Startet neues Spiel"""
        player_ids = [self.player_id]
        if self.is_duel and self.opponent_id:
            player_ids.append(self.opponent_id)
        
        self.game_id = self.db.create_game(player_ids, self.difficulty_id)
        self.load_next_question()
        
    def start_timer(self):
        """Startet Countdown-Timer"""
        self.timer_seconds = 30
        self.update_timer()
        
    def update_timer(self):
        """Aktualisiert Timer"""
        if self.timer_seconds > 0:
            color = 'green' if self.timer_seconds > 10 else 'orange' if self.timer_seconds > 5 else 'red'
            self.timer_label.config(text=f"⏱️ {self.timer_seconds}s", foreground=color)
            self.timer_seconds -= 1
            self.timer_id = self.window.after(1000, self.update_timer)
        else:
            # Zeit abgelaufen
            self.timeout()
    
    def stop_timer(self):
        """Stoppt Timer"""
        if self.timer_id:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None
    
    def timeout(self):
        """Behandelt Timeout"""
        self.stop_timer()
        self.disable_answers()
        
        # Speichere als falsch
        self.db.save_answer(
            self.game_id, 
            self.player_id, 
            self.current_question['id'],
            None,  # Keine Antwort
            False,
            self.current_round
        )
        
        self.feedback_label.config(text="⏰ Zeit abgelaufen!", foreground='red')
        self.window.after(2000, self.next_question_or_finish)
    
    def load_next_question(self):
        """Lädt nächste Frage"""
        self.feedback_label.config(text="")
        
        question = self.db.get_random_question(
            self.category_id,
            self.difficulty_id,
            self.asked_questions
        )
        
        if not question:
            messagebox.showerror("Fehler", "Keine weiteren Fragen verfügbar!")
            self.finish_game()
            return
        
        self.current_question = question
        self.asked_questions.append(question['id'])
        
        # UI aktualisieren
        self.round_label.config(text=f"Runde {self.current_round}/{self.max_rounds}")
        self.question_label.config(text=question['text'])
        
        # Antwort-Buttons aktualisieren
        for i, (answer_id, answer_text) in enumerate(question['answers']):
            self.answer_buttons[i].config(
                text=answer_text,
                state='normal',
                style='TButton'
            )
        
        self.start_timer()
    
    def disable_answers(self):
        """Deaktiviert Antwort-Buttons"""
        for btn in self.answer_buttons:
            btn.config(state='disabled')
    
    def check_answer(self, button_index):
        """Prüft gewählte Antwort"""
        self.stop_timer()
        self.disable_answers()
        
        selected_answer_id = self.current_question['answers'][button_index][0]
        correct_answer_id = self.current_question['correct_id']
        is_correct = (selected_answer_id == correct_answer_id)
        
        # Speichere Antwort
        self.db.save_answer(
            self.game_id,
            self.player_id,
            self.current_question['id'],
            selected_answer_id,
            is_correct,
            self.current_round
        )
        
        # Feedback anzeigen
        if is_correct:
            self.feedback_label.config(text="✅ Richtig! +10 Punkte", foreground='green')
            self.answer_buttons[button_index].config(style='Success.TButton')
        else:
            self.feedback_label.config(text="❌ Falsch! Richtig war:", foreground='red')
            self.answer_buttons[button_index].config(style='Error.TButton')
            
            # Zeige richtige Antwort
            for i, (ans_id, ans_text) in enumerate(self.current_question['answers']):
                if ans_id == correct_answer_id:
                    self.answer_buttons[i].config(style='Success.TButton')
        
        # Scores aktualisieren
        self.update_scores()
        
        # Weiter zur nächsten Frage
        self.window.after(3000, self.next_question_or_finish)
    
    def update_scores(self):
        """Aktualisiert Punkteanzeige"""
        scores = self.db.get_game_scores(self.game_id)
        
        for username, score in scores:
            if username == self.username:
                self.score_label.config(text=f"{username}: {score}")
            elif self.is_duel and username == self.opponent_name:
                self.opponent_score_label.config(text=f"{username}: {score}")
    
    def next_question_or_finish(self):
        """Entscheidet ob nächste Frage oder Spielende"""
        if self.current_round < self.max_rounds:
            self.current_round += 1
            self.load_next_question()
        else:
            self.finish_game()
    
    def finish_game(self):
        """Beendet Spiel und zeigt Ergebnis"""
        self.db.finish_game(self.game_id)
        scores = self.db.get_game_scores(self.game_id)
        
        # Erstelle Ergebnis-Fenster
        result_window = tk.Toplevel(self.window)
        result_window.title("Spielende")
        result_window.geometry("400x300")
        
        ttk.Label(
            result_window,
            text="🏁 Spiel beendet!",
            font=('Arial', 18, 'bold')
        ).pack(pady=20)
        
        # Ergebnisse anzeigen
        result_frame = ttk.LabelFrame(result_window, text="Endergebnis", padding=20)
        result_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        for i, (username, score) in enumerate(scores):
            place = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            ttk.Label(
                result_frame,
                text=f"{place} {username}: {score} Punkte",
                font=('Arial', 14)
            ).pack(pady=5)
        
        ttk.Button(
            result_window,
            text="Schließen",
            command=lambda: [result_window.destroy(), self.window.destroy()]
        ).pack(pady=10)


class QuizMainApp:
    """Hauptanwendung mit Menü"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz App - Hauptmenü")
        self.root.geometry("600x500")
        
        # Datenbank initialisieren
        db_path = os.path.join(os.path.dirname(__file__), "../database/quiz_app.db")
        self.db = QuizDatabase(db_path)
        
        self.player_id = None
        self.username = None
        
        # Styles
        self.setup_styles()
        
        # Login anzeigen
        self.show_login()
        
    def setup_styles(self):
        """Konfiguriert UI Styles"""
        style = ttk.Style()
        style.configure('Success.TButton', foreground='green')
        style.configure('Error.TButton', foreground='red')
        style.configure('Big.TButton', font=('Arial', 12), padding=10)
        
    def show_login(self):
        """Zeigt Login-Fenster"""
        LoginWindow(self.root, self.db, self.on_login_success)
        
    def on_login_success(self, player_id, username):
        """Callback nach erfolgreichem Login"""
        self.player_id = player_id
        self.username = username
        self.show_main_menu()
        
    def show_main_menu(self):
        """Zeigt Hauptmenü"""
        # Lösche altes Content
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header
        header = ttk.Label(
            self.root,
            text=f"Willkommen, {self.username}! 🎯",
            font=('Arial', 20, 'bold')
        )
        header.pack(pady=30)
        
        # Menü Buttons
        menu_frame = ttk.Frame(self.root)
        menu_frame.pack(expand=True)
        
        ttk.Button(
            menu_frame,
            text="📝 Einzelspieler Quiz starten",
            command=self.start_single_player,
            style='Big.TButton',
            width=35
        ).pack(pady=10)
        
        ttk.Button(
            menu_frame,
            text="⚔️ Duell starten",
            command=self.start_duel,
            style='Big.TButton',
            width=35
        ).pack(pady=10)
        
        ttk.Button(
            menu_frame,
            text="📊 Meine Statistiken",
            command=self.show_statistics,
            style='Big.TButton',
            width=35
        ).pack(pady=10)
        
        ttk.Button(
            menu_frame,
            text="❌ Beenden",
            command=self.root.quit,
            width=35
        ).pack(pady=10)
    
    def start_single_player(self):
        """Startet Einzelspieler-Modus"""
        self.select_game_options(is_duel=False)
    
    def start_duel(self):
        """Startet Duell-Modus"""
        # Gegner auswählen
        users = self.db.get_all_users(exclude_id=self.player_id)
        
        if not users:
            messagebox.showinfo("Keine Gegner", "Es sind keine anderen Spieler registriert!")
            return
        
        # Auswahl-Dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Gegner auswählen")
        dialog.geometry("300x400")
        
        ttk.Label(dialog, text="Wähle deinen Gegner:", font=('Arial', 12)).pack(pady=10)
        
        listbox = tk.Listbox(dialog, height=10)
        listbox.pack(padx=20, pady=10, fill='both', expand=True)
        
        for user_id, user_name in users:
            listbox.insert('end', user_name)
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                opponent_id, opponent_name = users[selection[0]]
                dialog.destroy()
                self.select_game_options(is_duel=True, opponent_id=opponent_id, opponent_name=opponent_name)
        
        ttk.Button(dialog, text="Auswählen", command=on_select).pack(pady=10)
    
    def select_game_options(self, is_duel=False, opponent_id=None, opponent_name=None):
        """Kategorie und Schwierigkeit auswählen"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Spiel konfigurieren")
        dialog.geometry("400x300")
        
        ttk.Label(
            dialog, 
            text="Wähle Kategorie und Schwierigkeit:",
            font=('Arial', 12)
        ).pack(pady=15)
        
        # Kategorie
        ttk.Label(dialog, text="Kategorie:").pack(anchor='w', padx=40)
        cat_combo = ttk.Combobox(dialog, state='readonly', width=30)
        cat_combo.pack(padx=40, pady=5)
        
        categories = self.db.get_categories()
        cat_map = {name: cat_id for cat_id, name in categories}
        cat_combo['values'] = list(cat_map.keys())
        if cat_combo['values']:
            cat_combo.current(0)
        
        # Schwierigkeit
        ttk.Label(dialog, text="Schwierigkeit:").pack(anchor='w', padx=40, pady=(15, 0))
        diff_combo = ttk.Combobox(dialog, state='readonly', width=30)
        diff_combo.pack(padx=40, pady=5)
        
        difficulties = self.db.get_difficulties()
        diff_map = {name: diff_id for diff_id, name, level in difficulties}
        diff_combo['values'] = list(diff_map.keys())
        if diff_combo['values']:
            diff_combo.current(0)
        
        def start_game():
            if not cat_combo.get() or not diff_combo.get():
                messagebox.showwarning("Auswahl fehlt", "Bitte Kategorie und Schwierigkeit wählen!")
                return
            
            category_id = cat_map[cat_combo.get()]
            difficulty_id = diff_map[diff_combo.get()]
            
            dialog.destroy()
            
            GameWindow(
                self.root,
                self.db,
                self.player_id,
                self.username,
                is_duel=is_duel,
                opponent_id=opponent_id,
                opponent_name=opponent_name,
                category_id=category_id,
                difficulty_id=difficulty_id
            )
        
        ttk.Button(
            dialog,
            text="Spiel starten!",
            command=start_game,
            style='Big.TButton'
        ).pack(pady=30)
    
    def show_statistics(self):
        """Zeigt Benutzerstatistiken"""
        stats = self.db.get_user_statistics(self.player_id)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Meine Statistiken")
        dialog.geometry("450x400")
        
        ttk.Label(
            dialog,
            text=f"📊 Statistiken - {self.username}",
            font=('Arial', 16, 'bold')
        ).pack(pady=20)
        
        stats_frame = ttk.LabelFrame(dialog, text="Übersicht", padding=20)
        stats_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Statistiken anzeigen
        stats_data = [
            ("Gespielte Spiele:", stats['games_played']),
            ("Gewonnene Duelle:", stats['duels_won']),
            ("Beantwortete Fragen:", stats['total_answers']),
            ("Richtige Antworten:", stats['correct_answers']),
            ("Erfolgsquote:", f"{stats['percentage']:.1f}%")
        ]
        
        for i, (label, value) in enumerate(stats_data):
            ttk.Label(
                stats_frame,
                text=label,
                font=('Arial', 11)
            ).grid(row=i, column=0, sticky='w', pady=8)
            
            ttk.Label(
                stats_frame,
                text=str(value),
                font=('Arial', 11, 'bold')
            ).grid(row=i, column=1, sticky='e', pady=8, padx=(20, 0))
        
        ttk.Button(
            dialog,
            text="Schließen",
            command=dialog.destroy
        ).pack(pady=15)


def main():
    """Hauptfunktion"""
    root = tk.Tk()
    app = QuizMainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()