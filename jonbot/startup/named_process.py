import multiprocessing

from jonbot import get_jonbot_logger

logger = get_jonbot_logger()


class NamedProcess(multiprocessing.Process):
    def __init__(self, *args, name=None, **kwargs):
        logger.trace(f"Creating process with name: {name}")
        super().__init__(*args, **kwargs)
        self.custom_name = name

    def run(self):
        # Set the process name (visible in system tools like top/htop on Unix)
        # Note: This step is optional
        if self.custom_name:
            multiprocessing.current_process().name = self.custom_name
        logger.trace(f"Starting process with name: {self.custom_name}")
        super().run()
