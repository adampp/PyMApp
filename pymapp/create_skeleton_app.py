

def create_skeleton(
    class_name: str,
    filename: str,
    config_filename: str = "config.json"
):
    with open(filename, 'w') as class_fid:
        class_fid.write(
f"""
import os
import pymapp

CONFIG_LOCATION = os.path.dirname(__file__)

class {class_name}(pymapp.MApp):
    def __init__(self):
        super().__init__(os.path.join(CONFIG_LOCATION, "{config_filename}"))
    
    def run(self):
        pass
"""
        )
    
    with open(config_filename, 'w') as config_fid:
        config_fid.write(
"""
{
    "log": {
        "clear_all_logs_on_startup": true,
        "use_stdout": true,
        "directory": "./logs/",
        "filename": "log.log",
        "filter_level": "DEBUG",
        "max_bytes": 2000000,
        "backup_count": 10,
        "queue_timeout_seconds": 0.1
    },
    "Watchdog": {
        "check_period_seconds": 5
    },
}
"""
        )