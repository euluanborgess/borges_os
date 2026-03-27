import sqlite3

def rescue_token():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    # Order by rowid because ID is UUID
    cursor.execute("SELECT id, access_token FROM ad_accounts WHERE status='PENDING' ORDER BY rowid DESC LIMIT 1")
    row = cursor.fetchone()
    if row and row[1]:
        token = row[1]
        print(f"RESGATADO! Token length: {len(token)}")
        
        with open("tmp/meta_token.txt", "w") as f:
            f.write(token)
            
    else:
        print("Token NOT RESCUED.")
    conn.close()

if __name__ == "__main__":
    rescue_token()
