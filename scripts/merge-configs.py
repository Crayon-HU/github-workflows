import json
import os
import collections.abc
from glob import glob
import hcl2

# Get workflow inputs
#config_directory = '${{ inputs.config_directory }}'
config_directory = os.getenv('CONFIG_DIRECTORY')
print(f"Config directory: {config_directory}")
workspace = os.getenv('GITHUB_WORKSPACE')

# Helper function to load and validate JSON configuration
def load_json(pattern):
    configs = []
    for file_path in glob(pattern, recursive=True):
        print(f"Found JSON file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
                configs.append(config)
                print(f"Loaded JSON configuration from {file_path}: {config}")
        except json.JSONDecodeError as e:
            print(f"JSON syntax error in {file_path}: {e}")
            exit(1)
    return configs

# Helper function to load tfvars configuration
def load_tfvars(pattern):
    configs = []
    for file_path in glob(pattern, recursive=True):
        print(f"Found tfvars file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                config = hcl2.load(f)
                configs.append(config)
                print(f"Loaded tfvars configuration from {file_path}: {config}")
        except Exception as e:
            print(e.message)
            exit(1)
    return configs

def deep_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

# Paths to JSON file patterns
override_pattern = os.path.join(workspace, 'config_override', config_directory, '*.json')
config_pattern = os.path.join(workspace, 'config-repo', 'config', config_directory, '*.json')
local_pattern = os.path.join(workspace, 'config', config_directory, '*.json')

print(f"Override pattern: {override_pattern}")
print(f"Config pattern: {config_pattern}")
print(f"Local pattern: {local_pattern}")

# Load and validate configurations
local_configs_for_json = load_json(local_pattern)
configs_for_json = load_json(config_pattern)
override_configs_for_json = load_json(override_pattern)

# Paths to tfvars file patterns
override_pattern_for_tfvars = os.path.join(workspace, 'config_override', config_directory, '*.tfvars')
config_pattern_for_tfvars = os.path.join(workspace, 'config-repo', 'config', config_directory, '*.tfvars')
local_pattern_for_tfvars = os.path.join(workspace, 'config', config_directory, '*.tfvars')

print(f"Override pattern for tfvars: {override_pattern_for_tfvars}")
print(f"Config pattern for tfvars: {config_pattern_for_tfvars}")
print(f"Local pattern for tfvars: {local_pattern_for_tfvars}")

# Load and validate configurations
local_configs_for_tfvars = load_tfvars(local_pattern_for_tfvars)
configs_for_tfvars = load_tfvars(config_pattern_for_tfvars)
override_configs_for_tfvars = load_tfvars(override_pattern_for_tfvars)

local_configs = local_configs_for_json + local_configs_for_tfvars
configs = configs_for_json + configs_for_tfvars
override_configs = override_configs_for_json + override_configs_for_tfvars

# Merge configurations
merged_config = {}
all_configs = local_configs + configs + override_configs
for config in all_configs:
    merged_config = deep_update(merged_config, config)
print(f"Merged configuration: {json.dumps(merged_config, indent=4)}")

# Write terraform.tfvars.json
tfvars_path = os.path.join(os.environ['GITHUB_WORKSPACE'], 'terraform.tfvars.json')
with open(tfvars_path, 'w') as f:
    json.dump(merged_config, f, indent=2)

print(f"Terraform variables have been written to {tfvars_path}")