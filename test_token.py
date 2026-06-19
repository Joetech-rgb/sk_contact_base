import os, requests
from dotenv import load_dotenv
load_dotenv()

token = 'EAATuwXmexQEBRf9E1wTFiiCKiIZAo5OTGyuIAigStuonb67ZAlEVsFZADjUE5ZC8xuo2duaSnZCZCz4DBsJkZCpLHDQq565OvvWYARjmF7avsz9RkKcxQAoMlzA319RArB1wZCEuEPQumHZCA0eQMih9vZCLBL0aI7tNPU47ruBzAZBNSZBS4zWlAp8RzKcQtBeBETyFMZBqcTlGo6YWjgVzI0YUA5VjbvFcpxAA35ZBbJtBHpzwpyxyoiq1gUhZBxZCxI9evFV9Pq9BmoEdnvCTeeynDKzo0ZAL5ggZDZD'
phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')

url = f'https://graph.facebook.com/v19.0/{phone_id}/messages'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

for lang in ['en', 'en_GB', 'en_US']:
    print(f'Trying: {lang}')
    payload = {
        'messaging_product': 'whatsapp',
        'to': '233540191971',
        'type': 'template',
        'template': {
            'name': 'welcome_registration',
            'language': {'code': lang},
            'components': [{'type': 'body', 'parameters': [
                {'type': 'text', 'text': 'Joseph'},
                {'type': 'text', 'text': '30'},
            ]}]
        }
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    print('Status:', resp.status_code, '|', resp.text)
    if resp.status_code == 200:
        print('SUCCESS with lang:', lang)
        break
