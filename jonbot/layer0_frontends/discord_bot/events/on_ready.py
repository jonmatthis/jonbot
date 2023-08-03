from jonbot.layer0_frontends.discord_bot.discord_main import discord_client


@discord_client.event
async def on_ready():
    print(f'We have logged in as {discord_client.user}')
