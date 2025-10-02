# Tiltfile for Argus Agent development workflow
# https://docs.tilt.dev/

# Load environment variables from .env file
import os

# Check if .env exists
if not os.path.exists('.env'):
    fail('.env file not found! Run: make setup')

# Simple dotenv loader
for line in str(read_file('.env')).splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    if '=' in line:
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.putenv(key, value)

# Generate ConfigMap from .env
def create_configmap():
    return blob("""
apiVersion: v1
kind: ConfigMap
metadata:
  name: argus-config
  namespace: argus-dev
data:
  PYTHONUNBUFFERED: "1"
  PYTHONDONTWRITEBYTECODE: "1"
  MCP_SERVER_URL: "http://argus-mcp-server:8002/mcp/"
""")

# Generate Secret from .env
def create_secret():
    import os
    openai_key = os.getenv('OPENAI_API_KEY', '')
    google_key = os.getenv('GOOGLE_API_KEY', '')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
    es_host = os.getenv('ES_HOST', '')
    es_user = os.getenv('ES_USER', '')
    es_password = os.getenv('ES_PASSWORD', '')

    return blob("""
apiVersion: v1
kind: Secret
metadata:
  name: argus-secrets
  namespace: argus-dev
type: Opaque
stringData:
  OPENAI_API_KEY: "%s"
  GOOGLE_API_KEY: "%s"
  ANTHROPIC_API_KEY: "%s"
  ES_HOST: "%s"
  ES_USER: "%s"
  ES_PASSWORD: "%s"
""" % (openai_key, google_key, anthropic_key, es_host, es_user, es_password))

# Load Kubernetes YAML
k8s_yaml('k8s/dev/namespace.yaml')
k8s_yaml(create_configmap())
k8s_yaml(create_secret())
k8s_yaml('k8s/dev/mcp-server-deployment.yaml')
k8s_yaml('k8s/dev/app-deployment.yaml')
k8s_yaml('k8s/dev/services.yaml')
k8s_yaml('k8s/dev/pvc.yaml')

# Build MCP Server Docker image
docker_build(
    'argus-mcp-server',
    context='.',
    dockerfile='Dockerfile.dev',
    live_update=[
        # Sync Python files for hot reload
        sync('./tools', '/app/tools'),
        sync('./prompts', '/app/prompts'),
        sync('./config', '/app/config'),
        # Restart process on changes
        run('echo "Files updated, uvicorn will auto-reload"'),
    ],
    only=[
        './tools',
        './prompts',
        './config',
        './requirements.txt',
    ]
)

# Build Main App Docker image
docker_build(
    'argus-app',
    context='.',
    dockerfile='Dockerfile.dev',
    live_update=[
        # Sync Python files for hot reload
        sync('./app', '/app/app'),
        sync('./prompts', '/app/prompts'),
        sync('./config', '/app/config'),
        sync('./main.py', '/app/main.py'),
        # Restart process on changes
        run('echo "Files updated, uvicorn will auto-reload"'),
    ],
    only=[
        './app',
        './main.py',
        './prompts',
        './config',
        './requirements.txt',
    ]
)

# Port forward services for local access
k8s_resource(
    'argus-mcp-server',
    port_forwards=['8002:8002', '5679:5678'],
    labels=['backend']
)

k8s_resource(
    'argus-app',
    port_forwards=['8000:8000', '5678:5678'],
    labels=['backend'],
    resource_deps=['argus-mcp-server']
)

# Custom button to run tests
local_resource(
    'run-tests',
    cmd='docker-compose run --rm app pytest -v',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['tests']
)

# Custom button to format code
local_resource(
    'format-code',
    cmd='docker-compose run --rm app black .',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['dev-tools']
)

# Custom button to lint code
local_resource(
    'lint-code',
    cmd='docker-compose run --rm app ruff check .',
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    labels=['dev-tools']
)

# Watch for config changes and restart pods
watch_file('config/models.json')
watch_file('config/settings.json')

# Set default update mode to avoid accidental deployments
update_settings(max_parallel_updates=2)

print("""
╔═══════════════════════════════════════════════════╗
║   Argus Agent - Development Environment Ready     ║
╚═══════════════════════════════════════════════════╝

Services:
  • Main App:    http://localhost:8000
  • MCP Server:  http://localhost:8002
  • Debug Ports: 5678 (app), 5679 (mcp-server)

Manual Actions:
  • run-tests:   Run pytest test suite
  • format-code: Format code with black
  • lint-code:   Lint code with ruff

Press 'space' to open Tilt UI
""")
