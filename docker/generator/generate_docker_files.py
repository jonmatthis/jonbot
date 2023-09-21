from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader


def create_dockerfile(bot_name: str):
    file_loader = FileSystemLoader('docker')  # assuming the templates are in the docker folder
    env = Environment(loader=file_loader)

    template_folder = Path().cwd() / "templates"
    docker_template_path = template_folder / "Dockerfile.template"
    template = env.get_template(str(docker_template_path))

    output = template.render(bot_name=bot_name)

    with open(f'../Dockerfile.{bot_name}', 'w') as f:
        f.write(output)


def create_docker_compose(bot_names: List[str]):
    file_loader = FileSystemLoader('docker')  # assuming the templates are in the docker folder
    env = Environment(loader=file_loader)

    template = env.get_template('templates/docker-compose.template.yml')

    services = {
        bot_name: {'build': {'context': '..', 'dockerfile': f'docker/Dockerfile.{bot_name}'}, 'depends_on': ['api']} for
        bot_name in bot_names}

    output = template.render(services=services)

    with open('../docker-compose.yml', 'w') as f:
        f.write(output)


if __name__ == '__main__':
    from jonbot.system.environment_variables import BOT_NICK_NAMES

    bot_names = BOT_NICK_NAMES
    for bot_name in bot_names:
        create_dockerfile(bot_name)
    create_docker_compose(bot_names)
