from hello_world.greeter import say_hello
from hello_world.template import greet
from hello_world.utils import load_config, save_config

# Test greeter
say_hello("Test User")

# Test template
print(greet("Test User"))

# Test utils
config_path = "test_config.json"
config_data = {"key": "value"}
save_config(config_path, config_data)
loaded_config = load_config(config_path)
print(loaded_config)
