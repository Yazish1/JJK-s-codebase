import pandas as pd

# Load dataset and standardize columns
jobs_postings = pd.read_csv(r"C:\Users\yazis\Documents\hackathon\dataset.csv", encoding='latin1')
jobs_postings.columns = [col.lower().strip() for col in jobs_postings.columns]

# Matching function
def find_matching_jobs(user_interests, jobs_df):
    matches = []

    for _, row in jobs_df.iterrows():
        # Split each field into words using spaces
        title_words = str(row["job title"]).lower().split()
        industry_words = str(row["industry tag"]).lower().split()
        responsibilities_words = str(row["responsibilities"]).lower().split()

        matched = False
        for interest in user_interests:
            interest_lower = interest.lower()
            if (interest_lower in title_words 
                or interest_lower in industry_words 
                or interest_lower in responsibilities_words):
                matched = True
                break


        if matched:
            matches.append(row)

    return pd.DataFrame(matches)

# Test user interests
user_interests = ["IT", "Marketing"]

matched_jobs = find_matching_jobs(user_interests, jobs_postings)

# Print results using correct lowercase column names
print("Matched jobs for user interests:")
print(matched_jobs[['job title', 'company name', 'industry tag']])
