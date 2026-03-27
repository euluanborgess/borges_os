import sqlite3
import json

def inject():
    conn = sqlite3.connect('borges_os.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, integrations FROM tenants")
    for row in cursor.fetchall():
        t_id = row[0]
        if "de634e" not in t_id:
            continue
            
        integrations = json.loads(row[1]) if row[1] else {}
        integrations["instagram_page_token"] = "EAAMrjDxZBgRcBRCEnXLFWtwoKxvFtSe4m1zuPSND1OfX9HSwthHKMRGws5NCbTzrM3w0ieCHLpiiRiK4UNoMjc77uuBizQFZA6FvZAwds36MsfE1CLZAMwNl9Mwrci5SWkRpJcUvPamfLZCIRoESjGeErPwGvkZCZCp13hhxCgMWShpqf9gA3mLdZCtMnoZBcZAYPQAt8ZD"
        integrations["instagram_page_id"] = "109826838567470"
        
        new_json = json.dumps(integrations)
        cursor.execute("UPDATE tenants SET integrations = ? WHERE id = ?", (new_json, t_id))
        print(f"Force Injected Page Token to Tenant {t_id}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inject()
