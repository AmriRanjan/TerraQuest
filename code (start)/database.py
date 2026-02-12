import sqlite3
import hashlib
import os

class Database():
    def __init__(self):
        self.make_tables() # ensure tables exist as soon as Database object is created

    def connect(self):
        # open a connection to the sqlite 3 database file
        self.connection = sqlite3.connect("code (start)/TerraQuestDB.db")
        self.cursor = self.connection.cursor()
        # allow foreign keys to work by stating syntax PRAGMA
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def make_tables(self):
        # create all database tables if they do not already exist by opening connection with our database file
        self.connect()

        # the users table
        self.cursor.execute("""

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                score INTEGER DEFAULT 0
            );
                        
        """)

        # the trainers table
        self.cursor.execute("""

            CREATE TABLE IF NOT EXISTS trainers (
                user_id INTEGER NOT NULL,
                trainer_id TEXT NOT NULL,
                PRIMARY KEY (user_id,trainer_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
                        
        """)

        # the monsters table and ON DELETE CASCADE ensures monsters are deleted if user is removed for relational integrity
        self.cursor.execute("""

            CREATE TABLE IF NOT EXISTS monsters (
                monster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                health INTEGER NOT NULL,
                energy INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
                        
        """)

        self.close_connection()
    
    def close_connection(self):
        # whenever this is called, save any changes to the DB and close the connection fully with cursor
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    # USER queries

    def user_exists(self,username):
        # a method to check if the user already exists by the username
        self.connect()
        self.cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
        row = self.cursor.fetchone()
        self.close_connection()

        # returns True if a matching username was found
        return row is not None
    
    def register(self,username,password):
        # hash the password before it is stored by applying the hash library's sha256 algorithm
        hash_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.connect()
        self.cursor.execute("INSERT INTO users (username,password_hash, score) VALUES (?,?,0)", (username,hash_password))
        self.close_connection()
        return
    
    def login(self,username, password):
        # verify login by comparing hash values
        pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.connect()
        self.cursor.execute("SELECT password_hash FROM users WHERE username=?",(username,))
        row = self.cursor.fetchone()
        self.close_connection()

        # if the username doesn't exist, login fails
        if row is None:
            return False
        
        # else, we return the result of comparing the stored_hash of this username and password account with the entered details
        stored_hash = row[0]
        return stored_hash == pw_hash

    def get_userid(self, username):
        # retrieve the user's unique ID using their username
        self.connect() 
        self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
        row = self.cursor.fetchone()
        self.close_connection()
        return int(row[0]) if row else None
    
    def get_score(self,username):
        # Grabs user's score
        self.connect()
        self.cursor.execute("SELECT score from users WHERE username=?",(username,))
        row = self.cursor.fetchone()
        self.close_connection()
        return int(row[0]) if row else None

    def update_score(self,username,new_score):
        # Updates user's score after battles or events
        self.connect()
        self.cursor.execute("UPDATE users SET score = ? WHERE username = ?", (new_score, username))    
        self.close_connection()

    def get_leaderboard(self,limit):
        # Grabs top scores and orders them descending
        # limits the results by 10
        self.connect()
        self.cursor.execute("SELECT username, score FROM users ORDER BY score desc, username ASC LIMIT ?", (limit,))
        rows = self.cursor.fetchall()
        self.close_connection()

        return rows
    
    
    # TRAINER queries:

    def add_defeated_trainer(self,user_id, trainer_id):
        self.connect()
        self.cursor.execute("INSERT OR IGNORE INTO trainers (user_id,trainer_id) VALUES (?,?)", (user_id,trainer_id))
        self.close_connection()


    def get_trainers_defeated(self, user_id):
        self.connect()
        self.cursor.execute("SELECT trainer_id FROM trainers WHERE user_id = ? ORDER BY trainer_id", (user_id,))
        rows = self.cursor.fetchall()
        self.close_connection()
        return [r[0] for r in rows]


    # MONSTER queries

    def add_monster(self, user_id, name, level, xp, health, energy):
        # add monsters linked to specific user
        self.connect()
        self.cursor.execute("INSERT INTO MONSTERS (user_id,name,level,xp, health, energy) VALUES (?,?,?,?,?,?)", (user_id,name,level,xp, health, energy))

        # store the monster's unique ID for future updates
        monster_id = self.cursor.lastrowid
        self.close_connection()
        return int(monster_id)
    
    def get_monsters(self,user_id):
        # retrieve all the monsters owned by a user
        # order them to ensure consistent display
        self.connect()
        self.cursor.execute("SELECT monster_id, name, level, xp, health, energy FROM MONSTERS WHERE user_id = ? ORDER BY monster_id", (user_id,))
        rows = self.cursor.fetchall()
        self.close_connection()
        return rows
    
    def update_monster(self, monster_id, level, xp, health, energy):
        # update a unique monster's level and experience after matches
        self.connect()
        self.cursor.execute("UPDATE monsters SET level = ?, xp = ?, health = ?, energy = ? WHERE monster_id = ?", (level, xp, health, energy, monster_id))
        self.close_connection()
