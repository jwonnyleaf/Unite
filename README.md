Unite
==========

[![](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/release/python-3110/) [![](https://img.shields.io/badge/discord.py-v2.4.0-blue)](https://github.com/Rapptz/discord.py)

A modern, easy to use, multi-purpose Discord bot.

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file. There is a provided .env.sample file for reference.

`DISCORD_TOKEN`

`DISCORD_GUILD`

### Setting Up a Discord Bot Token for Development
To run the bot in your local environment, you will need to create a Discord bot and obtain a Bot Token. Follow the steps below to create a bot and set up your .env file.

#### Step 1: Create a Discord Application
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click on the **New Application** button in the top-right corner
3. Provide a name for your application (e.g. Unite-Johnny), assign it to **Personal** and click **Create**

#### Step 2: Retrieve the Bot Token
1. Under the **Bot** tab, you'll find a **TOKEN** section. Click **Reset Token** and then **Copy** to copy your bot's token to your clipboard.
* This token is very important, and **you should never share it publicly**. It is what allows your bot to authenticate with Discord's Application
**Important:** If it is ever compromised, reset it immediately to prevent unauthorized access to your bot.

### Step 3: Add Bot Token to the .env File
1. Inside the project directory you should find a `.env.example` file. Rename this file to `.env` or create a new `.env` file.
2. Inside the `.env` file, paste the Bot Token from earlier to the following line
    ```bash
    DISCORD_TOKEN=bot-token-here
    ```


## Run Locally

Clone the Project

```bash
  git clone https://github.com/jwonnyleaf/Unite
```

Go to the Project Directory

```bash
  cd Unite
```

Install Packages

```bash
  pip install -r requirements.txt
```

Start the Bot

```bash
  python launcher.py
```

## Running Tests

To run tests, run the following command

```bash
  pytest
```

