import yaml

bot_tokens = {
    "bot_1": 33423,
    "bot_2": 2832,
    "bot_3": 324525,
}

base_service = {
    'build': {
        'context': '.',
        'dockerfile': 'Dockerfile.discord',
    },
    'depends_on': [
        'api'
    ],
}

services = {
    'api': {
        'build': {
            'context': '.',
            'dockerfile': 'Dockerfile.api',
        },
        'ports': ['8091:8091']
    }
}

for bot_name, token in bot_tokens.items():
    service = base_service.copy()
    service['environment'] = {
        'BOT_TOKEN': token
    }
    services[bot_name] = service

compose_data = {
    'version': '3.7',
    'services': services,
}

with open('docker-compose_og.yml', 'w') as f:
    yaml.dump(compose_data, f, default_flow_style=False)
