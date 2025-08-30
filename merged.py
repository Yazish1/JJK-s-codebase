import pandas as pd
import os
import sqlite3

# Paths to files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "listings.db")

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class DatabaseManagement:
    def __init__(self, db_path):
        self.db_path = db_path
        self.tableexists()

    def tableexists(self):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            cursor.execute(
                '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
            ''')
            db.commit()
    
    def create_user(self, user):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                               (user.username, user.password))
                db.commit()
                print(f"User '{user.username}' created successfully.")
                return True
            except sqlite3.IntegrityError:
                print("Error: User already exists.")
                return False
            
    def autheticate_user(self, username, password):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
    
    def get_userjobs(self, username):
        with sqlite3.connect(self.db_path) as db:
            job_postings_df = pd.read_sql_query("SELECT * FROM listings", db)
        return job_postings_df
    

    def matched_jobs(self, user_interests, jobs_df):
        if jobs_df.empty:
            return pd.DataFrame()
        
        jobs_df.columns = [col.lower().strip() for col in jobs_df.columns]
        matches = []

        for _, row in jobs_df.iterrows():
            title_words = str(row.get("job_title", "")).lower().split()
            industry_words = str(row.get("industry_tag", "")).lower().split()
            responsibilities_words = str(row.get("responsibilities", "")).lower().split()

            matched = False
            for interest in user_interests:
                interest_lower = interest.lower()
                
                # Check if the interest is a word in the title
                if interest_lower in title_words:
                    matched = True
                    break
                
                # Check if the interest is a word in the industry tag
                if interest_lower in industry_words:
                    matched = True
                    break

                # Check if the interest is a word in the responsibilities
                if interest_lower in responsibilities_words:
                    matched = True
                    break
            
            if matched:
                matches.append(row)

        return pd.DataFrame(matches)

def main():
    db_manager = DatabaseManagement(db_path)
    user_id = None
    
    while True: # Main application loop
        if user_id is None:
            # Login section
            username = input("Please enter your username (or 'exit' to quit): ").strip()
            if username.lower() == "exit":
                return
            
            password = input("Enter your password: ").strip()
            if password.lower() == "exit":
                return

            user_id = db_manager.autheticate_user(username, password)
            
            if user_id is None:
                with sqlite3.connect(db_path) as db:
                    cursor = db.cursor()
                    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
                    user_exists = cursor.fetchone()

                if user_exists:
                    print("Invalid password. Please try again.")
                else:
                    print(f"User '{username}' does not exist. Would you like to create an account?")
                    permission = input("Enter 'yes' or 'no': ").strip()
                    if permission.lower() == "yes":
                        if db_manager.create_user(User(username, password)):
                            print("Account created. Please log in with your new credentials.")
                        else:
                            # Re-prompt for login
                            continue
                    else:
                        # Re-prompt for login
                        continue
            else:
                print("Login success.")
                print("Welcome back.")
        
        else:
            # Job search section
            print("\nEnter your job interests (e.g., IT, Marketing), separated by commas. Type 'exit' to quit.")
            user_inst = input("Interests: ").strip()
            
            if user_inst.lower() == "exit":
                print("Exiting job search.")
                return

            user_interests = [i.strip() for i in user_inst.split(",")]
            
            if not user_interests or user_interests == ['']:
                print("No interests entered. Please try again.")
                continue

            alljobs_df = db_manager.get_userjobs(username)
            matched = db_manager.matched_jobs(user_interests, alljobs_df)

            print("Matching jobs:")
            if not matched.empty:
                print("Job title, Company, Location, Benefits") # Header line
                for index, row in matched.iterrows():
                    # Format the output into a single string for each row
                    print(f"**{row['job_title']}**, {row['company_name']}, {row['location']}, {row['benefits']}")
            else:
                print("No matching jobs found.")
            
            while True:
                employment_type = input("\nEnter employment type: 'Part-time', 'Casual', 'Contract' or 'continue' to search again: ").strip()
                if employment_type.lower() == "exit":
                    print("Exiting job search.")
                    return
                
                if employment_type.lower() == "continue":
                    break
                
                if employment_type.lower() not in ["part-time", "casual", "contract"]:
                    print("Invalid input. Please enter a valid option.")
                    continue

                with sqlite3.connect(db_path) as db:
                    cursor = db.cursor()
                    result = cursor.execute("SELECT Job_Title, Company_Name, Location, Employment_Type FROM listings WHERE Employment_Type LIKE ?", ('%' + employment_type + '%',))
                    rows = result.fetchall()
                
                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("No jobs for this employment type.")

if __name__ == "__main__":
    main()