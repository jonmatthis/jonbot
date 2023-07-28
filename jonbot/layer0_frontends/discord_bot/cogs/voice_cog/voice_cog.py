import random

from discord import client
from discord.app_commands import commands
import discord
import logging

from discord.ext.commands import Cog, Context, before_invoke

from jonbot.layer0_frontends.discord_bot.cogs.voice_cog.native_voice_client import NativeVoiceClient

log = logging.getLogger(__name__)


class VoiceCog(Cog):
    """
    A cog that handles voice recording in Discord.
    """
    @commands.command()
    async def join(self, ctx: Context) -> None:
        """
        Command to make the bot join the voice channel.
        """
        try:
            channel: discord.VoiceChannel = ctx.author.voice.channel
            if ctx.voice_client is not None:
                return await ctx.voice_client.move_to(channel)
            await channel.connect(cls=NativeVoiceClient)
            await ctx.invoke(client.get_command('record_audio'))
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name='record_audio')
    async def record_audio(self, ctx: Context) -> None:
        """
        Command to make the bot start recording in the voice channel.
        """
        try:
            ctx.voice_client.record(lambda e: print(f"Exception: {e}"))
            await ctx.send("Started recording. Use !stop to stop recording.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    async def stop(self, ctx: Context) -> None:
        """
        Command to make the bot stop recording in the voice channel and save the audio.
        """
        try:
            if not ctx.voice_client.is_recording():
                return
            await ctx.send('Stopping the recording')

            wav_bytes = await ctx.voice_client.stop_record()
            filename = f"{str(random.randint(0, 999999))}.wav"
            with open(filename, 'wb') as audio_file:
                audio_file.write(wav_bytes)
            await ctx.voice_client.disconnect()
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @before_invoke
    async def ensure_voice(self, ctx) -> None:
        """
        A function that ensures the bot is in a voice channel before recording.
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect(cls=NativeVoiceClient)
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()