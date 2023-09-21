from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader


def create_dockerfile(bot_name: str,
                      template_folder: str,
                      save_folder: str):
    file_loader = FileSystemLoader(str(template_folder))
    env = Environment(loader=file_loader)

    docker_template_filename = "Dockerfile.template"
    docker_template_path = Path(template_folder) / docker_template_filename
    if not docker_template_path.exists():
        raise FileNotFoundError(f"Could not find the Dockerfile template at {str(docker_template_path)}")
    template = env.get_template(str(docker_template_filename))

    output = template.render(bot_name=bot_name)

    docker_filename = f"Dockerfile.{bot_name}"
    with open(str(Path(save_folder) / docker_filename), 'w') as f:
        f.write(output)


def create_docker_compose(bot_names: List[str],
                          template_folder: str,
                          save_folder: str):
    file_loader = FileSystemLoader(template_folder)  # assuming the templates are in the docker folder
    env = Environment(loader=file_loader)

    template = env.get_template('docker-compose.template.yml')

    services = {
        bot_name: {'build': {'context': '..',
                             'dockerfile': f'docker/Dockerfile.{bot_name}'},
                   'depends_on': ['api']} for bot_name in bot_names}

    output = template.render(services=services)

    with open(str(Path(save_folder) / "docker-compose.yml"), 'w') as f:
        f.write(output)


def generate_docker_files():
    parent_folder = Path(__file__).parent
    template_folder = parent_folder / 'templates'
    save_folder = parent_folder.parent / 'docker_per_bot'
    if not template_folder.exists():
        raise FileNotFoundError(f"Could not find the template folder at {str(template_folder)}")
    save_folder.mkdir(parents=True, exist_ok=True)
    bot_names = BOT_NICK_NAMES
    for bot_name in bot_names:
        create_dockerfile(bot_name=bot_name,
                          template_folder=str(template_folder),
                          save_folder=str(save_folder))
    create_docker_compose(bot_names=bot_names,
                          template_folder=str(template_folder),
                          save_folder=str(save_folder))


if __name__ == '__main__':
    from jonbot.system.environment_variables import BOT_NICK_NAMES

    generate_docker_files()
