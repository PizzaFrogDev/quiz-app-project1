-- DDL Skript für QuizzApp Datenbank
-- Löscht existierende Tabellen um eine saubere Neuerstellung zu garantieren
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS SpielHistorie;
DROP TABLE IF EXISTS Teilnahme;
DROP TABLE IF EXISTS Antwort;
DROP TABLE IF EXISTS Frage;
DROP TABLE IF EXISTS Spiel;
DROP TABLE IF EXISTS Spieler;
DROP TABLE IF EXISTS Kategorie;
DROP TABLE IF EXISTS Schwierigkeitsgrad;
DROP TABLE IF EXISTS Konfiguration;

PRAGMA foreign_keys = ON;

-- 1. Konfigurationstabelle (Für flexible Spielregeln)
CREATE TABLE Konfiguration (
    KonfigID INTEGER PRIMARY KEY AUTOINCREMENT,
    Bezeichnung TEXT DEFAULT 'Standard',
    RundenAnzahl INTEGER NOT NULL CHECK (RundenAnzahl > 0),
    FragenProRunde INTEGER NOT NULL CHECK (FragenProRunde > 0),
    MaxAntwortenAnzahl INTEGER NOT NULL CHECK (MaxAntwortenAnzahl >= 2),
    MaxSpielzeitSec INTEGER, -- NULL bedeutet unendlich
    ErstelltAm DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Initiale Konfiguration einfügen
INSERT INTO Konfiguration (Bezeichnung, RundenAnzahl, FragenProRunde, MaxAntwortenAnzahl, MaxSpielzeitSec) 
VALUES ('Standard Modus', 3, 5, 4, 600);

-- 2. Schwierigkeitsgrad (Erweiterbar)
CREATE TABLE Schwierigkeitsgrad (
    SchwierigkeitID INTEGER PRIMARY KEY AUTOINCREMENT,
    Bezeichnung TEXT NOT NULL UNIQUE,
    LevelWert INTEGER NOT NULL -- z.B. 1, 2, 3 für Sortierung
);

INSERT INTO Schwierigkeitsgrad (Bezeichnung, LevelWert) VALUES ('Leicht', 1), ('Mittel', 2), ('Schwer', 3);

-- 3. Kategorie (Erweiterbar)
CREATE TABLE Kategorie (
    KategorieID INTEGER PRIMARY KEY AUTOINCREMENT,
    Bezeichnung TEXT NOT NULL UNIQUE
);

-- 4. Spieler
CREATE TABLE Spieler (
    SpielerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL UNIQUE,
    PasswortHash TEXT NOT NULL,
    SessionKey TEXT,
    SessionTime DATETIME
);

-- 5. Frage
CREATE TABLE Frage (
    FrageID INTEGER PRIMARY KEY AUTOINCREMENT,
    FrageText TEXT NOT NULL,
    KategorieID INTEGER NOT NULL,
    SchwierigkeitID INTEGER NOT NULL,
    ErstelltAm DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (KategorieID) REFERENCES Kategorie(KategorieID),
    FOREIGN KEY (SchwierigkeitID) REFERENCES Schwierigkeitsgrad(SchwierigkeitID)
);

-- 6. Antwort (Mehr als 4 möglich, mehrere richtige möglich)
CREATE TABLE Antwort (
    AntwortID INTEGER PRIMARY KEY AUTOINCREMENT,
    AntwortText TEXT NOT NULL,
    IstRichtig BOOLEAN NOT NULL CHECK (IstRichtig IN (0, 1)),
    FrageID INTEGER NOT NULL,
    FOREIGN KEY (FrageID) REFERENCES Frage(FrageID) ON DELETE CASCADE
);

-- 7. Spiel (Kopfdaten einer Session)
CREATE TABLE Spiel (
    SpielID INTEGER PRIMARY KEY AUTOINCREMENT,
    StartZeit DATETIME DEFAULT CURRENT_TIMESTAMP,
    EndZeit DATETIME,
    KonfigID INTEGER NOT NULL,
    GewaehlteSchwierigkeitID INTEGER,
    FOREIGN KEY (KonfigID) REFERENCES Konfiguration(KonfigID),
    FOREIGN KEY (GewaehlteSchwierigkeitID) REFERENCES Schwierigkeitsgrad(SchwierigkeitID)
);

-- 8. Teilnahme (Verknüpfung Spieler <-> Spiel für Multiuser/Duell)
CREATE TABLE Teilnahme (
    TeilnahmeID INTEGER PRIMARY KEY AUTOINCREMENT,
    SpielID INTEGER NOT NULL,
    SpielerID INTEGER NOT NULL,
    EndScore INTEGER DEFAULT 0,
    FOREIGN KEY (SpielID) REFERENCES Spiel(SpielID) ON DELETE CASCADE,
    FOREIGN KEY (SpielerID) REFERENCES Spieler(SpielerID)
);

-- 9. SpielHistorie (Statistik & Spiellogik: Wer hat was geantwortet?)
CREATE TABLE SpielHistorie (
    HistorieID INTEGER PRIMARY KEY AUTOINCREMENT,
    SpielID INTEGER NOT NULL,
    SpielerID INTEGER NOT NULL,
    FrageID INTEGER NOT NULL,
    RundeNr INTEGER NOT NULL,
    GegebeneAntwortID INTEGER, -- Kann NULL sein bei Zeitüberschreitung
    WarKorrekt BOOLEAN DEFAULT 0,
    Zeitstempel DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SpielID) REFERENCES Spiel(SpielID) ON DELETE CASCADE,
    FOREIGN KEY (SpielerID) REFERENCES Spieler(SpielerID),
    FOREIGN KEY (FrageID) REFERENCES Frage(FrageID),
    FOREIGN KEY (GegebeneAntwortID) REFERENCES Antwort(AntwortID)
);