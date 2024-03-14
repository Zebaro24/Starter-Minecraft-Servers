# Minecraft Manager Bot

A Telegram bot for managing Minecraft servers running in Docker containers.
Start, stop, check player counts, and send RCON commands — all from Telegram.

## Features

- **Start / Stop** Minecraft server containers via the Telegram bot
- **Live status** — online players list with real-time mcstatus ping
- **RCON** — send any in-game command directly from Telegram
- **Easy scaling** — add a new server in two files, no code changes needed
- **Docker-native** — servers run as `itzg/minecraft-server` containers
- **CI/CD** — GitHub Actions pipelines for linting, type checking, and deployment

## Project Structure

```
.
├── app/
│   ├── main.py                  # Entry point
│   ├── config/
│   │   ├── settings.py          # Pydantic settings (env vars)
│   │   └── servers.py           # Server registry — add new servers here
│   ├── bot/
│   │   ├── bot.py               # Bot + Dispatcher setup
│   │   ├── keyboards.py         # Reply and inline keyboards
│   │   └── handlers/
│   │       ├── commands.py      # /start /servers /help
│   │       └── server.py        # Status, start/stop, RCON, FSM
│   └── servers/
│       ├── manager.py           # Docker SDK + mcstatus integration
│       ├── models.py            # ServerStatus, ServerInfo, PlayerInfo
│       └── rcon.py              # Async RCON client (stdlib only)
├── .github/workflows/
│   ├── ci.yml                   # Lint, type check, security audit
│   └── cd.yml                   # Build image → GHCR → SSH deploy
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone and configure

```bash
git clone https://github.com/your-user/starter-minecraft-servers.git
cd starter-minecraft-servers

cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_ID=your_telegram_user_id
RCON_PASSWORD=your_strong_password
```

> The `RCON_PASSWORD` must match the value in `docker-compose.yml`. The bot reads it from the env file automatically.

### 2. Start everything

```bash
docker compose up -d
```

This starts the Telegram bot and the Minecraft server. The first launch will download the modpack, which can take several minutes.

### 3. Open Telegram

Send `/start` to your bot. The server buttons will appear in the menu.

## Bot Commands

| Command    | Description          |
|------------|----------------------|
| `/start`   | Welcome message      |
| `/servers` | Show server list     |
| `/help`    | Help and usage guide |

**Admin-only actions** (restricted to `TELEGRAM_ADMIN_ID`):
- Start / Stop a server
- Send RCON commands

Anyone can view the server status and player list.

## Adding a New Server

**Step 1** — add a service to `docker-compose.yml`:

```yaml
mc-survival:
  image: itzg/minecraft-server
  container_name: mc-survival
  restart: unless-stopped
  networks:
    - mc-net
  ports:
    - "25566:25565"
  environment:
    EULA: "TRUE"
    TYPE: "PAPER"
    VERSION: "1.21"
    MEMORY: "4G"
    ENABLE_RCON: "true"
    RCON_PORT: "25575"
    RCON_PASSWORD: "${RCON_PASSWORD}"
  volumes:
    - ./data/survival:/data
```

**Step 2** — add an entry to `app/config/servers.py`:

```python
ServerConfig(
    id="survival",
    name="Survival",
    container_name="mc-survival",
    host="mc-survival",
    port=25566,
    rcon_port=25575,
),
```

That's it. Restart the bot and the new server appears in the menu.

## CI/CD

### CI (`ci.yml`) — runs on every push/PR to `main`/`master`

| Job          | Tools                         |
|--------------|-------------------------------|
| Lint         | black, isort, flake8          |
| Type check   | mypy                          |
| Security     | bandit, safety                |

### CD (`cd.yml`) — runs on version tags (`v*`)

1. Builds the bot Docker image
2. Pushes to GitHub Container Registry (`ghcr.io`)
3. Copies `docker-compose.yml` to the server via SCP
4. Pulls the new image and restarts the bot via SSH

#### Required GitHub secrets

| Secret                 | Description                        |
|------------------------|------------------------------------|
| `TELEGRAM_BOT_TOKEN`   | Telegram bot token                 |
| `TELEGRAM_ADMIN_ID`    | Your Telegram user ID              |
| `RCON_PASSWORD`        | RCON password for all MC servers   |
| `SERVER_HOST`          | Deployment server IP or hostname   |
| `SERVER_USER`          | SSH username                       |
| `SSH_PRIVATE_KEY`      | SSH private key                    |

#### Deploy a new version

```bash
git tag v1.0.0
git push origin v1.0.0
```

The pipeline builds, pushes, and deploys automatically.

## Local Development

```bash
# Install dependencies
poetry install

# Run the bot locally (needs Docker + .env)
poetry run python -m app.main

# Lint
poetry run black app
poetry run isort app
poetry run flake8 app

# Type check
poetry run mypy app

# Security
poetry run bandit -r app
poetry run safety check
```
