import requests

token = 'EAATuwXmexQEBRf9E1wTFiiCKiIZAo5OTGyuIAigStuonb67ZAlEVsFZADjUE5ZC8xuo2duaSnZCZCz4DBsJkZCpLHDQq565OvvWYARjmF7avsz9RkKcxQAoMlzA319RArB1wZCEuEPQumHZCA0eQMih9vZCLBL0aI7tNPU47ruBzAZBNSZBS4zWlAp8RzKcQtBeBETyFMZBqcTlGo6YWjgVzI0YUA5VjbvFcpxAA35ZBbJtBHpzwpyxyoiq1gUhZBxZCxI9evFV9Pq9BmoEdnvCTeeynDKzo0ZAL5ggZDZD'

resp = requests.get(
    'https://graph.facebook.com/v19.0/me',
    params={'access_token': token, 'fields': 'id,name'}
)
print(resp.text)
