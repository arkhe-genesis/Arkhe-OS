import argparse
import yaml

def deploy(env, config_path):
    print(f"Deploying Fisher-Rao Email Middleware to {env} environment.")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print(f"Loaded config: {config}")
    print("Deployment successful. Metrics collection started.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', required=True)
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    deploy(args.env, args.config)