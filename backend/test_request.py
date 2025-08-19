import requests

url = "http://127.0.0.1:8080/generate"
data = {
    "date": "1972-12-06",
    "time": "01:25",
    "city": "Mykolaiv",
    "country": "Ukraine"
}

response = requests.post(url, json=data)

if response.status_code == 200:
    print("Сервер відповів успішно!")
    result = response.json()
    print(result)
else:
    print("Помилка:", response.status_code)