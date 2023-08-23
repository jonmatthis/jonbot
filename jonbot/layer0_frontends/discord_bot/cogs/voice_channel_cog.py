import asyncio
from enum import Enum

import discord

from jonbot.layer0_frontends.discord_bot.handlers.should_process_message import (
    FINISHED_VOICE_RECORDING_PREFIX,
)


class Sinks(Enum):
    mp3 = discord.sinks.MP3Sink()
    wav = discord.sinks.WaveSink()
    pcm = discord.sinks.PCMSink()
    ogg = discord.sinks.OGGSink()
    mka = discord.sinks.MKASink()
    mkv = discord.sinks.MKVSink()
    mp4 = discord.sinks.MP4Sink()
    m4a = discord.sinks.M4ASink()


class VoiceChannelCog(discord.Cog):
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.voice_client_connections = {}
        self.status_message = {}
        self.bot = bot

    @discord.slash_command(
        name="join", description="Commands related to voice channels"
    )
    async def join(self, ctx: discord.ApplicationContext):
        """Join the voice channel!"""
        if ctx.author.voice:
            voice_channel_to_join = ctx.author.voice.channel
        else:
            voice_channel_to_join = ctx.guild.voice_channels[0]

        await voice_channel_to_join.connect()

        self.status_message[ctx.guild_id] = await ctx.channel.send("Joined!")
        self.voice_client_connections[ctx.guild.id] = ctx.guild.voice_client

    @discord.slash_command(name="leave", description="Leave the voice channel")
    async def leave_voice(self, ctx: discord.ApplicationContext):
        """Leave the voice channel!"""
        voice_client: discord.VoiceClient = self.voice_client_connections.get(
            ctx.guild.id, None
        )
        if not voice_client:
            return await ctx.respond("I'm not in a voice channel right now")

        await voice_client.disconnect()

        try:
            del self.voice_client_connections[ctx.guild.id]
        except KeyError:
            pass

    @discord.slash_command(
        name="start", description="Start recording audio from the voice channel"
    )
    @discord.option(
        name="sink", description="The format to record in", required=True, choices=Sinks
    )
    @discord.option(
        name="duration",
        description="The duration to record for (sec)",
        required=False,
        type=int,
    )
    async def start_recording(
        self, ctx: discord.ApplicationContext, sink: Sinks, duration: int = 10
    ):
        """Record your voice!"""

        if not ctx.author.voice:
            return await ctx.respond("You're not in a voice channel!")

        voice_connection = self.voice_client_connections.get(ctx.guild.id, None)

        if not voice_connection:
            raise Exception("I'm not in a voice channel right now")

        voice_connection.start_recording(
            sink.value,
            self.finished_callback,
            ctx.channel,
        )

        self.status_message[ctx.guild_id] = await ctx.channel.send(
            "The recording has started!"
        )

        if duration is not None:
            for wait_sec in range(duration):
                await asyncio.sleep(1)
                await self.status_message[ctx.guild_id].edit(
                    content=f"The recording has started! {duration - wait_sec} seconds remaining."
                )

            await self.stop(ctx)

    @discord.slash_command(
        name="stop", description="Stop recording audio from the voice channel"
    )
    async def stop(
        self,
        ctx: discord.ApplicationContext,
    ):
        """Stop recording."""
        if ctx.guild.id in self.voice_client_connections:
            voice_connection = self.voice_client_connections[ctx.guild.id]
            voice_connection.stop_recording()
            del self.voice_client_connections[ctx.guild.id]

        else:
            await ctx.respond("Not recording in this guild.")

    async def finished_callback(self, sink, channel: discord.TextChannel):
        recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
        await sink.vc.disconnect()
        files = [
            discord.File(audio.file, f"{user_id}.{sink.encoding}")
            for user_id, audio in sink.audio_data.items()
        ]
        reply_message = await channel.send(
            f"{FINISHED_VOICE_RECORDING_PREFIX} {' '.join(recorded_users)}.",
            files=files,
        )

        await self.bot.handle_message(message=reply_message)
