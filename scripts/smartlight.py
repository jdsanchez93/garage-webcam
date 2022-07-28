import requests

def setSmartLight(apiUrl, data):
    response = requests.put(apiUrl, json=data)
    print(response.status_code)
    print(response.content)
    return response