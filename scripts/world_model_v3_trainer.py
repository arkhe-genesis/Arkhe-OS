import requests

def fetch_prometheus_data(prometheus_url, query, start, end, step='60s'):
    resp = requests.get(f'{prometheus_url}/api/v1/query_range', params={
        'query': query, 'start': start, 'end': end, 'step': step
    })
    return resp.json()['data']['result']

# Mock trainer script execution for completeness
if __name__ == "__main__":
    pass
