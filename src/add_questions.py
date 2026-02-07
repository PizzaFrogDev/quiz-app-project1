import sqlite3
import os

# Verbindung zur Datenbank (Pfad relativ zum Skript)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database'))
os.makedirs(base_dir, exist_ok=True)
db_path = os.path.join(base_dir, 'quiz_app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Deine Fragen (Format: Frage, Kategorie, Schwierigkeit, [(Antwort, IstRichtig), ...])
meine_fragen = [
    ("Wer erfand das Telefon?", "Geschichte", "Mittel",
     [("Alexander Graham Bell", True), 
      ("Thomas Edison", False), 
      ("Nikola Tesla", False), 
      ("Guglielmo Marconi", False)]),
    
    ("Welches ist das größte Säugetier?", "Naturwissenschaften", "Leicht",
     [("Blauwal", True), 
      ("Elefant", False), 
      ("Giraffe", False), 
      ("Nashorn", False)]),
   
    # GEOGRAPHIE - LEICHT
    ("In welchem Land steht der Eiffelturm?", "Geographie", "Leicht", 
     [("Frankreich", True), ("Deutschland", False), ("Italien", False), ("Spanien", False), ("England", False)]),
    
    ("Welche ist die Hauptstadt von Deutschland?", "Geographie", "Leicht",
     [("Berlin", True), ("München", False), ("Hamburg", False), ("Frankfurt", False), ("Köln", False)]),
    
    ("Auf welchem Kontinent liegt Ägypten?", "Geographie", "Leicht",
     [("Afrika", True), ("Asien", False), ("Europa", False), ("Südamerika", False)]),
    
    ("Welcher Ozean ist der größte?", "Geographie", "Leicht",
     [("Pazifik", True), ("Atlantik", False), ("Indischer Ozean", False), ("Arktischer Ozean", False)]),
    
    ("Welches Land hat die Form eines Stiefels?", "Geographie", "Leicht",
     [("Italien", True), ("Griechenland", False), ("Spanien", False), ("Portugal", False)]),
    
    ("In welcher Stadt steht die Freiheitsstatue?", "Geographie", "Leicht",
     [("New York", True), ("Los Angeles", False), ("Chicago", False), ("Miami", False)]),
    
    ("Welcher Fluss fließt durch London?", "Geographie", "Leicht",
     [("Themse", True), ("Seine", False), ("Rhein", False), ("Donau", False)]),
    
    ("Auf welchem Kontinent liegt Brasilien?", "Geographie", "Leicht",
     [("Südamerika", True), ("Afrika", False), ("Asien", False), ("Nordamerika", False)]),
    
    # GEOGRAPHIE - MITTEL
    ("Welches ist das größte Land der Welt nach Fläche?", "Geographie", "Mittel",
     [("Russland", True), ("Kanada", False), ("China", False), ("USA", False), ("Brasilien", False)]),
    
    ("Welche Stadt ist die Hauptstadt von Australien?", "Geographie", "Mittel",
     [("Canberra", True), ("Sydney", False), ("Melbourne", False), ("Brisbane", False)]),
    
    ("Wie viele Länder grenzen an Deutschland?", "Geographie", "Mittel",
     [("9", True), ("7", False), ("8", False), ("10", False), ("6", False)]),
    
    ("Welcher Berg ist der höchste Europas?", "Geographie", "Mittel",
     [("Mont Blanc", True), ("Matterhorn", False), ("Zugspitze", False), ("Monte Rosa", False)]),
    
    ("In welchem Land liegt die Wüste Sahara hauptsächlich?", "Geographie", "Mittel",
     [("Algerien", True), ("Ägypten", False), ("Marokko", False), ("Tunesien", False)]),
    
    # GEOGRAPHIE - SCHWER
    ("Welches ist das kleinste Land der Welt?", "Geographie", "Schwer",
     [("Vatikanstadt", True), ("Monaco", False), ("San Marino", False), ("Liechtenstein", False)]),
    
    ("Wie heißt die Hauptstadt von Kasachstan?", "Geographie", "Schwer",
     [("Astana", True), ("Almaty", False), ("Taschkent", False), ("Bischkek", False)]),
    
    ("Welcher Fluss ist der längste der Welt?", "Geographie", "Schwer",
     [("Nil", True), ("Amazonas", False), ("Jangtsekiang", False), ("Mississippi", False)]),
    
    # GESCHICHTE - LEICHT
    ("In welchem Jahr fiel die Berliner Mauer?", "Geschichte", "Leicht",
     [("1989", True), ("1990", False), ("1988", False), ("1991", False)]),
    
    ("Wer war der erste Bundeskanzler Deutschlands?", "Geschichte", "Leicht",
     [("Konrad Adenauer", True), ("Willy Brandt", False), ("Helmut Kohl", False), ("Ludwig Erhard", False)]),
    
    ("In welchem Jahr begann der Zweite Weltkrieg?", "Geschichte", "Leicht",
     [("1939", True), ("1940", False), ("1938", False), ("1941", False)]),
    
    ("Wer entdeckte Amerika im Jahr 1492?", "Geschichte", "Leicht",
     [("Christoph Kolumbus", True), ("Amerigo Vespucci", False), ("Ferdinand Magellan", False), ("Vasco da Gama", False)]),
    
    ("Welches Reich herrschte im antiken Rom?", "Geschichte", "Leicht",
     [("Römisches Reich", True), ("Griechisches Reich", False), ("Persisches Reich", False), ("Byzantinisches Reich", False)]),
    
    # GESCHICHTE - MITTEL
    ("In welchem Jahr wurde die Bundesrepublik Deutschland gegründet?", "Geschichte", "Mittel",
     [("1949", True), ("1945", False), ("1950", False), ("1948", False)]),
    
    ("Wer war der erste Mensch auf dem Mond?", "Geschichte", "Mittel",
     [("Neil Armstrong", True), ("Buzz Aldrin", False), ("Juri Gagarin", False), ("Michael Collins", False)]),
    
    ("Wie lange dauerte der Hundertjährige Krieg?", "Geschichte", "Mittel",
     [("116 Jahre", True), ("100 Jahre", False), ("99 Jahre", False), ("110 Jahre", False)]),
    
    ("In welchem Jahr endete der Erste Weltkrieg?", "Geschichte", "Mittel",
     [("1918", True), ("1919", False), ("1917", False), ("1920", False)]),
    
    # GESCHICHTE - SCHWER
    ("Wann wurde das Grundgesetz der Bundesrepublik Deutschland verkündet?", "Geschichte", "Schwer",
     [("23. Mai 1949", True), ("8. Mai 1949", False), ("1. Juli 1949", False), ("3. Oktober 1949", False)]),
    
    ("Wer war der letzte Kaiser des Deutschen Reiches?", "Geschichte", "Schwer",
     [("Wilhelm II", True), ("Wilhelm I", False), ("Friedrich III", False), ("Otto von Bismarck", False)]),
    
    # NATURWISSENSCHAFTEN - LEICHT
    ("Wie viele Planeten hat unser Sonnensystem?", "Naturwissenschaften", "Leicht",
     [("8", True), ("9", False), ("7", False), ("10", False)]),
    
    ("Welches Gas atmen Menschen ein?", "Naturwissenschaften", "Leicht",
     [("Sauerstoff", True), ("Kohlendioxid", False), ("Stickstoff", False), ("Helium", False)]),
    
    ("Bei welcher Temperatur gefriert Wasser?", "Naturwissenschaften", "Leicht",
     [("0°C", True), ("10°C", False), ("-10°C", False), ("5°C", False)]),
    
    ("Wie viele Beine hat eine Spinne?", "Naturwissenschaften", "Leicht",
     [("8", True), ("6", False), ("10", False), ("4", False)]),
    
    ("Welches Organ pumpt Blut durch den Körper?", "Naturwissenschaften", "Leicht",
     [("Herz", True), ("Lunge", False), ("Leber", False), ("Niere", False)]),
    
    ("Was ist H2O?", "Naturwissenschaften", "Leicht",
     [("Wasser", True), ("Salz", False), ("Zucker", False), ("Sauerstoff", False)]),
    
    # NATURWISSENSCHAFTEN - MITTEL
    ("Welcher Planet ist der größte in unserem Sonnensystem?", "Naturwissenschaften", "Mittel",
     [("Jupiter", True), ("Saturn", False), ("Neptun", False), ("Uranus", False)]),
    
    ("Was ist die Lichtgeschwindigkeit (ungefähr)?", "Naturwissenschaften", "Mittel",
     [("300.000 km/s", True), ("150.000 km/s", False), ("500.000 km/s", False), ("200.000 km/s", False)]),
    
    ("Wie heißt der größte Knochen im menschlichen Körper?", "Naturwissenschaften", "Mittel",
     [("Oberschenkelknochen", True), ("Oberarmknochen", False), ("Schienbein", False), ("Wirbelsäule", False)]),
    
    ("Welches Element hat das Symbol 'Au'?", "Naturwissenschaften", "Mittel",
     [("Gold", True), ("Silber", False), ("Aluminium", False), ("Kupfer", False)]),
    
    # NATURWISSENSCHAFTEN - SCHWER
    ("Wie viele Chromosomen hat der Mensch?", "Naturwissenschaften", "Schwer",
     [("46", True), ("44", False), ("48", False), ("42", False)]),
    
    ("Was ist die chemische Formel von Kochsalz?", "Naturwissenschaften", "Schwer",
     [("NaCl", True), ("KCl", False), ("CaCl2", False), ("MgCl2", False)]),
    
    # SPORT - LEICHT
    ("Wie viele Spieler hat eine Fußballmannschaft auf dem Feld?", "Sport", "Leicht",
     [("11", True), ("10", False), ("12", False), ("9", False)]),
    
    ("In welcher Stadt fanden die Olympischen Spiele 2012 statt?", "Sport", "Leicht",
     [("London", True), ("Peking", False), ("Rio de Janeiro", False), ("Athen", False)]),
    
    ("Welche Farbe haben die Tore beim Handball?", "Sport", "Leicht",
     [("Weiß", True), ("Gelb", False), ("Rot", False), ("Blau", False)]),
    
    ("Wie viele Ringe hat das olympische Symbol?", "Sport", "Leicht",
     [("5", True), ("4", False), ("6", False), ("7", False)]),
    
    ("In welcher Sportart gibt es einen 'Homerun'?", "Sport", "Leicht",
     [("Baseball", True), ("Basketball", False), ("Football", False), ("Cricket", False)]),
    
    # SPORT - MITTEL
    ("Wer gewann die Fußball-WM 2014?", "Sport", "Mittel",
     [("Deutschland", True), ("Brasilien", False), ("Argentinien", False), ("Spanien", False)]),
    
    ("Wie lang ist ein Marathon?", "Sport", "Mittel",
     [("42,195 km", True), ("40 km", False), ("45 km", False), ("50 km", False)]),
    
    ("In welchem Land wurde Golf erfunden?", "Sport", "Mittel",
     [("Schottland", True), ("England", False), ("USA", False), ("Irland", False)]),
    
    ("Wie viele Grand-Slam-Turniere gibt es im Tennis?", "Sport", "Mittel",
     [("4", True), ("3", False), ("5", False), ("6", False)]),
    
    # SPORT - SCHWER
    ("Wer hat die meisten olympischen Goldmedaillen gewonnen?", "Sport", "Schwer",
     [("Michael Phelps", True), ("Usain Bolt", False), ("Carl Lewis", False), ("Mark Spitz", False)]),
    
    ("In welchem Jahr fanden die ersten modernen Olympischen Spiele statt?", "Sport", "Schwer",
     [("1896", True), ("1900", False), ("1892", False), ("1888", False)]),
    
    # KUNST & KULTUR - LEICHT
    ("Wer malte die Mona Lisa?", "Kunst & Kultur", "Leicht",
     [("Leonardo da Vinci", True), ("Michelangelo", False), ("Raffael", False), ("Donatello", False)]),
    
    ("In welcher Stadt steht das Kolosseum?", "Kunst & Kultur", "Leicht",
     [("Rom", True), ("Athen", False), ("Paris", False), ("Madrid", False)]),
    
    ("Wie viele Saiten hat eine normale Gitarre?", "Kunst & Kultur", "Leicht",
     [("6", True), ("5", False), ("7", False), ("8", False)]),
    
    ("Welcher Komponist schrieb die 'Mondscheinsonate'?", "Kunst & Kultur", "Leicht",
     [("Ludwig van Beethoven", True), ("Wolfgang Amadeus Mozart", False), ("Johann Sebastian Bach", False), ("Franz Schubert", False)]),
    
    # KUNST & KULTUR - MITTEL
    ("Wer schrieb 'Romeo und Julia'?", "Kunst & Kultur", "Mittel",
     [("William Shakespeare", True), ("Charles Dickens", False), ("Oscar Wilde", False), ("Jane Austen", False)]),
    
    ("In welchem Museum hängt die Mona Lisa?", "Kunst & Kultur", "Mittel",
     [("Louvre", True), ("Prado", False), ("Uffizien", False), ("British Museum", False)]),
    
    ("Wie heißt der berühmte schiefe Turm in Italien?", "Kunst & Kultur", "Mittel",
     [("Turm von Pisa", True), ("Turm von Venedig", False), ("Turm von Rom", False), ("Turm von Florenz", False)]),
    
    # KUNST & KULTUR - SCHWER
    ("Wer komponierte 'Die vier Jahreszeiten'?", "Kunst & Kultur", "Schwer",
     [("Antonio Vivaldi", True), ("Johann Sebastian Bach", False), ("Georg Friedrich Händel", False), ("Claudio Monteverdi", False)]),
    
    ("In welchem Jahr wurde die Sixtinische Kapelle fertiggestellt?", "Kunst & Kultur", "Schwer",
     [("1512", True), ("1510", False), ("1515", False), ("1520", False)]),
    
    # TECHNOLOGIE - LEICHT
    ("Was bedeutet 'WWW' im Internet?", "Technologie", "Leicht",
     [("World Wide Web", True), ("World Web Wide", False), ("Wide World Web", False), ("Web World Wide", False)]),
    
    ("Welche Firma entwickelte das iPhone?", "Technologie", "Leicht",
     [("Apple", True), ("Samsung", False), ("Nokia", False), ("Google", False)]),
    
    ("Was ist Windows?", "Technologie", "Leicht",
     [("Ein Betriebssystem", True), ("Ein Browser", False), ("Eine Programmiersprache", False), ("Ein Prozessor", False)]),
    
    ("Wofür steht 'USB'?", "Technologie", "Leicht",
     [("Universal Serial Bus", True), ("United Serial Bus", False), ("Universal System Bus", False), ("Unique Serial Bus", False)]),
    
    # TECHNOLOGIE - MITTEL
    ("In welchem Jahr wurde Google gegründet?", "Technologie", "Mittel",
     [("1998", True), ("1996", False), ("2000", False), ("1995", False)]),
    
    ("Wer gilt als Erfinder des World Wide Web?", "Technologie", "Mittel",
     [("Tim Berners-Lee", True), ("Bill Gates", False), ("Steve Jobs", False), ("Mark Zuckerberg", False)]),
    
    ("Was bedeutet 'AI' in der Technologie?", "Technologie", "Mittel",
     [("Artificial Intelligence", True), ("Automated Intelligence", False), ("Advanced Intelligence", False), ("Applied Intelligence", False)]),
    
    # TECHNOLOGIE - SCHWER
    ("In welcher Programmiersprache ist Linux hauptsächlich geschrieben?", "Technologie", "Schwer",
     [("C", True), ("Java", False), ("Python", False), ("C++", False)]),
    
    ("Wann wurde das erste iPhone vorgestellt?", "Technologie", "Schwer",
     [("2007", True), ("2006", False), ("2008", False), ("2005", False)]),
    
    # UNTERHALTUNG - LEICHT
    ("Welcher Film gewann 2020 den Oscar für den besten Film?", "Unterhaltung", "Leicht",
     [("Parasite", True), ("1917", False), ("Joker", False), ("Once Upon a Time in Hollywood", False)]),
    
    ("In welcher Stadt spielt die Serie 'Friends'?", "Unterhaltung", "Leicht",
     [("New York", True), ("Los Angeles", False), ("Chicago", False), ("Boston", False)]),
    
    ("Wie heißt der Zauberer in 'Der Herr der Ringe'?", "Unterhaltung", "Leicht",
     [("Gandalf", True), ("Dumbledore", False), ("Merlin", False), ("Saruman", False)]),
    
    ("Welche Farbe hat Batmans Umhang?", "Unterhaltung", "Leicht",
     [("Schwarz", True), ("Blau", False), ("Grau", False), ("Dunkelblau", False)]),
    
    # UNTERHALTUNG - MITTEL
    ("Wer spielte Iron Man in den Marvel-Filmen?", "Unterhaltung", "Mittel",
     [("Robert Downey Jr.", True), ("Chris Evans", False), ("Chris Hemsworth", False), ("Mark Ruffalo", False)]),
    
    ("Wie heißt die Heimatwelt von Superman?", "Unterhaltung", "Mittel",
     [("Krypton", True), ("Asgard", False), ("Themyscira", False), ("Metropolis", False)]),
    
    # UNTERHALTUNG - SCHWER
    ("In welchem Jahr wurde der erste Harry-Potter-Film veröffentlicht?", "Unterhaltung", "Schwer",
     [("2001", True), ("2000", False), ("2002", False), ("1999", False)]),
    
    # POLITIK - LEICHT
    ("Wer ist aktuell Bundeskanzler von Deutschland?", "Politik", "Leicht",
     [("Olaf Scholz", True), ("Angela Merkel", False), ("Christian Lindner", False), ("Robert Habeck", False)]),
    
    ("Wie viele Bundesländer hat Deutschland?", "Politik", "Leicht",
     [("16", True), ("15", False), ("17", False), ("14", False)]),
    
    ("In welcher Stadt ist der Sitz der deutschen Bundesregierung?", "Politik", "Leicht",
     [("Berlin", True), ("Bonn", False), ("München", False), ("Hamburg", False)]),
    
    # POLITIK - MITTEL
    ("Wie oft wird der Bundestag gewählt?", "Politik", "Mittel",
     [("Alle 4 Jahre", True), ("Alle 5 Jahre", False), ("Alle 3 Jahre", False), ("Alle 6 Jahre", False)]),
    
    ("Wer ist das Staatsoberhaupt in Deutschland?", "Politik", "Mittel",
     [("Bundespräsident", True), ("Bundeskanzler", False), ("Bundestagspräsident", False), ("Ministerpräsident", False)]),
    
    # POLITIK - SCHWER
    ("Wie viele Mitglieder hat der Deutsche Bundestag mindestens?", "Politik", "Schwer",
     [("598", True), ("500", False), ("600", False), ("550", False)]),
]

    
    


# Fragen in Datenbank einfügen
# Ensure categories from `meine_fragen` exist in Kategorie table
categories = set(k for _, k, _, _ in meine_fragen)
for cat in categories:
    cursor.execute("INSERT OR IGNORE INTO Kategorie (Bezeichnung) VALUES (?)", (cat,))
conn.commit()

# Hole Kategorie-IDs
cursor.execute("SELECT KategorieID, Bezeichnung FROM Kategorie")
kat_map = {name: id for id, name in cursor.fetchall()}

# Hole Schwierigkeits-IDs  
cursor.execute("SELECT SchwierigkeitID, Bezeichnung FROM Schwierigkeitsgrad")
diff_map = {name: id for id, name in cursor.fetchall()}

for frage_text, kategorie, schwierigkeit, antworten in meine_fragen:
    kat_id = kat_map[kategorie]
    diff_id = diff_map[schwierigkeit]
    
    # Frage einfügen
    cursor.execute(
        "INSERT INTO Frage (FrageText, KategorieID, SchwierigkeitID) VALUES (?, ?, ?)",
        (frage_text, kat_id, diff_id)
    )
    frage_id = cursor.lastrowid
    
    # Antworten einfügen
    for antwort_text, ist_richtig in antworten:
        cursor.execute(
            "INSERT INTO Antwort (AntwortText, IstRichtig, FrageID) VALUES (?, ?, ?)",
            (antwort_text, ist_richtig, frage_id)
        )
    
    print(f"✓ Frage hinzugefügt: {frage_text[:50]}...")

conn.commit()
conn.close()
print(f"\n✅ {len(meine_fragen)} Fragen erfolgreich hinzugefügt!")