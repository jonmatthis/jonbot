import copy

import yaml

bot_nick_names = [
    "jonbot",
    "golembot",
]

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

for bot_nick_name in bot_nick_names:
    service = copy.deepcopy(base_service)
    service['environment'] = {
        'BOT_NICK_NAME': bot_nick_name
    }
    services[bot_nick_name] = service

compose_data = {
    'version': '3.7',
    'services': services,
}

with open('docker-compose.yml', 'w') as f:
    yaml.dump(compose_data, f, default_flow_style=False, Dumper=yaml.SafeDumper)
