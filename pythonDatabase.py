import sqlite3
import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "listings.db")

def queryDatabase(db_path):
    with sqlite3.connect(db_path) as db:

        cursor = db.cursor()

        empType = input("enter the employment type (Part-time, Casual, Contract): ")
        if empType == "stop":
            return False
        print("fields: Job_Title,Company_Name,Location,Employment_Type,Responsibilities,Qualifications,Benefits,Work_Schedule,Industry_Tag")
        fields = input("enter the fields to search for: ")

        result = cursor.execute(f"select {fields} from listings where Employment_Type like '%{empType}%';")
        #result = cursor.execute("SELECT * from listings;")
        imported = [b[0:len(fields)] for b in result.fetchall()] #0: the number of arguments returned.
        for line in imported:
            print(line)
        return True

def main():
    active = True
    while(active):
        status = queryDatabase(db_path)
        if status == False:
            active = False

if __name__ == "__main__":
    main()