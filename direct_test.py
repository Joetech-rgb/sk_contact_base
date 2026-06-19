import requests

token = 'EAATuwXmexQEBRf9E1wTFiiCKiIZAo5OTGyuIAigStuonb67ZAlEVsFZADjUE5ZC8xuo2duaSnZCZCz4DBsJkZCpLHDQq565OvvWYARjmF7avsz9RkKcxQAoMlzA319RArB1wZCEuEPQumHZCA0eQMih9vZCLBL0aI7tNPU47ruBzAZBNSZBS4zWlAp8RzKcQtBeBETyFMZBqcTlGo6YWjgVzI0YUA5VjbvFcpxAA35ZBbJtBHpzwpyxyoiq1gUhZBxZCxI9evFV9Pq9BmoEdnvCTeeynDKzo0ZAL5ggZDZD'
phone_id = '1139832449206067'

url = f'https://graph.facebook.com/v19.0/{phone_id}/messages'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Test both number formats
for number in ['233530611837', '233540191971']:
    print(f'Testing: {number}')
    payload = {
        'messaging_product': 'whatsapp',
        'to': number,
        'type': 'template',
        'template': {
            'name': 'welcome_registration',
            'language': {'code': 'en'},
            'components': [{'type': 'body', 'parameters': [
                {'type': 'text', 'text': 'Joseph'},
                {'type': 'text', 'text': '31'},
            ]}]
        }
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    print('Status:', resp.status_code)
    print('Response:', resp.text)
    print()
