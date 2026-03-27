import requests

def test_reply():
    page_token = "EAAMrjDxZBgRcBRCEnXLFWtwoKxvFtSe4m1zuPSND1OfX9HSwthHKMRGws5NCbTzrM3w0ieCHLpiiRiK4UNoMjc77uuBizQFZA6FvZAwds36MsfE1CLZAMwNl9Mwrci5SWkRpJcUvPamfLZCIRoESjGeErPwGvkZCZCp13hhxCgMWShpqf9gA3mLdZCtMnoZBcZAYPQAt8ZD"
    page_id = "109826838567470" # ID vazado pela debug
    ig_sid = "6741197482560089" # ID do Lead
    
    url = f"https://graph.facebook.com/v19.0/me/messages"
    # Actually, the endpoint is POST /me/messages or POST /{page_id}/messages ?
    # Instagram messaging strictly uses v19.0/{page_id}/messages ALWAYS with recipient={id}.
    # Wait, docs say: POST /v19.0/{page-id}/messages or just /me/messages because we use Page Token!
    
    payload = {
        "recipient": {"id": ig_sid},
        "message": {"text": "Teste NATIVO de envio de volta pelo Borges OS usando o Page Token absoluto!!"}
    }
    params = {"access_token": page_token}
    
    print("Sending Direct Message with Page Token...")
    res = requests.post(f"https://graph.facebook.com/v19.0/{page_id}/messages", json=payload, params=params)
    print(res.status_code, res.text)
    
    # Just in case, let's also test /me/messages
    print("Testing /me/messages...")
    res2 = requests.post(f"https://graph.facebook.com/v19.0/me/messages", json=payload, params=params)
    print(res2.status_code, res2.text)

if __name__ == "__main__":
    test_reply()
