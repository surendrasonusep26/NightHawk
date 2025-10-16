import requests

url = input("Enter URL: ")

r = requests.get(url)

print(r.text)
