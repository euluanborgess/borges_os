import requests

page_token = "EAAMrjDxZBgRcBRH08GpkMKKEZBZClt8P8f77gXlZCKXneNhiiqXi7g6d259EMxEbt6nZCWcdCNStZBMytSK7icnHB2t2dTtrJUhUvmcqIDJKcQzMmcX05S4PGtjZBlZChB5mJHZC4GhSEMNdTyDdnpOyfaEuuspMk4SUZBAo2ADcudBklu9exZCaJqs3KmZCtEBCvc8AaFbxasIZD"

# IGSID capturado nos logs recentes do webhook
sender_id = "1295356032454924"

print("Tentando buscar o perfil do IGSID com o Page Token atualizado...")
url = f"https://graph.facebook.com/v19.0/{sender_id}?fields=name,profile_pic&access_token={page_token}"
res = requests.get(url)

print(f"Status: {res.status_code}")
print(res.json())
