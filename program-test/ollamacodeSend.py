import requests
from ollama import Ollama

# 1️⃣ Fetch HTML
url = input("Enter URL: ")
r = requests.get(url)
html_code = r.text

# 2️⃣ Connect to Ollama and load your local model
ollama = Ollama()
model_name = "phishing-detector"  # replace with your Ollama model name

# 3️⃣ Send HTML to Ollama model
prompt = f"Analyze this HTML and detect if it is phishing:\n\n{html_code[:1000]}"
response = ollama.generate(model=model_name, prompt=prompt)

# 4️⃣ Print the model's output
print(response.text)
