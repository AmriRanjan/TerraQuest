import sqlite3
import hashlib
import os


class Database():
    def __init__(self):
        self.make_tables()

    def connect(self):
        self.connection = sqlite3.connect("code (start)/TerraQuestDB.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def make_tables(self):
        self.connect()
        self.cursor.execute("""

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                score INTEGER DEFAULT 0
            );
                        
        """)

        self.cursor.execute("""

            CREATE TABLE IF NOT EXISTS trainers (
                user_id INTEGER NOT NULL,
                trainer_id INTEGER NOT NULL,
                PRIMARY KEY (user_id,trainer_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
                        
        """)

        self.cursor.execute("""

            CREATE TABLE IF NOT EXISTS monsters (
                monster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
                        
        """)


        self.close_connection()
    
    def close_connection(self):
        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    # USER queries

    def user_exists(self,username):
        self.connect()
        self.cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username))
        row = self.cursor.fetchone()
        self.close_connection()
        return row is not None
    
    def register(self,username,password):
        hash_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.connect()
        self.cursor.execute("INSERT INTO users (username,password_hash, score) VALUES (?,?,0)", (username,hash_password))
        user_id = self.cursor.lastrowid
        self.close_connection()
        return int(user_id)
    
    def login(self,username, password):
        pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.connect()
        self.cursor.execute("SELECT password_hash FROM users WHERE username=?",(username))
        row = self.cursor.fetchone()
        self.close_connection()

        if row is None:
            return False
        stored_hash = row[0]
        return stored_hash == pw_hash

    def get_userid(self, username):
        self.connect() 
        self.cursor.execute("SELECT user_id FROM users WHERE username=?", (username))
        row = self.cursor.fetchone()
        self.close_connection()
        return int(row[0]) if row else None
    
    def get_score(self,username):
        # Grabs user's score
        self.connect()
        self.cursor.execute("SELECT score from users WHERE username=?",(username))
        row = self.cursor.fetchone()
        self.close_connection()
        return int(row[0]) if row else None

    def update_score(self,username,new_score):
        # Updates user's score
        self.connect()
        self.cursor.execute("UPDATE users SET score = ? WHERE username = ?", (new_score, username))    
        self.close_connection()

    def get_leaderboard(self,limit):
        # Grabs top scores
        self.connect()
        self.cursor.execute("SELECT username, score FROM users ORDER BY score desc, username ASC LIMIT ? ", (limit))
        rows = self.cursor.fetchall()
        self.close_connection()
        return rows
    
    
    # TRAINER queries:

    
    

    # MONSTER queries

    def add_monster(self, user_id, name, level, xp):
        self.connect()
        self.cursor.execute("INSERT INTO MONSTERS (user_id,name,level,xp), VALUES (?,?,?,?)", (user_id,name,level,xp))
        monster_id = self.cursor.lastrowid
        self.close_connection()
        return int(monster_id)
    
    def get_monsters(self,user_id):
        self.connect()
        self.cursor.execute("SELECT monster_id, name, level, xp FROM MONSTERS WHERE user_id = ? ORDER BY monster_id", (user_id))
        rows = self.cursor.fetchall()
        self.close_connection()
        return rows
    
    def update_monster(self, monster_id, level, xp):
        self.connect()
        self.cursor.execute("UPDATE monsters SET level = ?, xp = ? WHERE monster_id = ?", (level, xp, monster_id))
        self.close_connection()


# class database():
#     def __init__(self):
#         self.create_table() 

#     def open_connection(self):
#         self.sqlite_connection = sqlite3.connect("Bat Rush/Code/BatRushLDB.db")
#         self.cursor = self.sqlite_connection.cursor() # Obtains the SQL cursor

#     def close_connection(self):
#         self.cursor.close()
#         self.sqlite_connection.close()

#     def create_table(self):
#         self.open_connection() # Open connection 
#         self.cursor.execute("CREATE TABLE IF NOT EXISTS LEADERBOARD(UserID INTEGER PRIMARY key AUTOINCREMENT,username VARCHAR(255),pass VARCHAR(255),score INTEGER DEFAULT 0);")
#         self.close_connection() # Close connection

#     def insert(self, user_name, password, score):
#         self.open_connection()
#         self.cursor.execute("Insert into LEADERBOARD VALUES (?,?, ?, ?)", (None,user_name,password,score)) # Insert username, password and score
#         self.sqlite_connection.commit() # Ensure changes save
#         self.close_connection()
    

#     def display(self):
#         self.open_connection()
#         self.cursor.execute("Select * from LEADERBOARD")
#         result = self.cursor.fetchall() 
#         for row in result: # Iterate through each row returned
#             print(row)
#             print("\n")
#         self.close_connection()

#     def login(self, username, password):
#         if self.username_exists(username): # Check user is already logged in
#             return False
#         self.open_connection()
#         query = ("Select pass from LEADERBOARD WHERE username = ?")
#         param = (username,)
#         self.cursor.execute(query,param) # Pass query and parameter to execute
#         stored_password = self.cursor.fetchone()[0] # Fetch first data item (the password)
#         self.close_connection()
#         if stored_password == hashlib.sha256(password.encode()).hexdigest():
#             return True
#         else:
#             return False
        
#     def fetch_score(self,username):
#         self.open_connection()
#         query = "Select score from LEADERBOARD WHERE username = ?"
#         param = (username,)
#         self.cursor.execute(query,param)
#         score = self.cursor.fetchone()[0] # Select first data item (the score)
#         self.close_connection()
#         return score

#     def username_exists(self, username):
#         self.open_connection()
#         query = "Select COUNT(username) from LEADERBOARD WHERE username = ?"
#         param = (username,) 
#         self.cursor.execute(query,param)
#         count = self.cursor.fetchone()[0] # Obtain no. of common usernames
#         self.close_connection()
#         if count == 0: # If username is unique
#             return True
#         else:
#             return False
        
#     def update_score(self,score,username):
#         self.open_connection()
#         query = "Update LEADERBOARD set score = ? WHERE username = ?"
#         self.cursor.execute(query,(score,username))
#         self.sqlite_connection.commit() # Ensure changes are saved
#         self.close_connection()
#         return score
    
#     def fetch_LDBdata(self):
#         self.open_connection()
#         query = "Select username, score from LEADERBOARD ORDER BY score desc"
#         self.cursor.execute(query)
#         result = self.cursor.fetchall()
#         self.close_connection()
#         return result
