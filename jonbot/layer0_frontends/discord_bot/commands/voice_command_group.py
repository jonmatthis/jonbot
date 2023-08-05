import discord

voice_command_group = discord.SlashCommandGroup("voice", description="Commands related to voice channels")

@voice_command_group.command()
async def join(ctx: discord.ApplicationContext):
    """Join the voice channel!"""
    voice_channel_to_join = ctx.author.voice

    if not voice_channel_to_join:
        voice_channel_to_join = ctx.guild.voice_channels[0]

    await voice_channel_to_join.channel.connect()

    await ctx.respond("Joined!")


@voice_command_group.command()
async def leave(ctx: discord.ApplicationContext):
    """Leave the voice channel!"""
    voice_client: discord.VoiceClient = ctx.voice_client

    if not voice_client:
        return await ctx.respond("I'm not in a voice channel right now")

    await voice_client.disconnect()

    await ctx.respond("Left!")
