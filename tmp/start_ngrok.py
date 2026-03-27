from pyngrok import ngrok
import time

try:
    public_url = ngrok.connect(8000)
    print("NGROK URL:", public_url.public_url)
    with open("ngrok_url.txt", "w") as f:
        f.write(public_url.public_url)
    
    # Keep alive
    for i in range(3600):
        time.sleep(1)
except Exception as e:
    print("Error:", e)
