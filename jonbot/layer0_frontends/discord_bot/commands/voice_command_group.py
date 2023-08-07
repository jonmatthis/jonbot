from enum import Enum

import discord

voice_command_group = discord.SlashCommandGroup("voice", description="Commands related to voice channels")
voice_connections = {}


@voice_command_group.command()
async def join(ctx: discord.ApplicationContext):
    """Join the voice channel!"""
    global voice_connections
    if ctx.author.voice:
        voice_channel_to_join = ctx.author.voice.channel
    else:
        voice_channel_to_join = ctx.guild.voice_channels[0]

    await voice_channel_to_join.connect()

    await ctx.respond("Joined!")
    voice_connections[ctx.guild.id] = ctx.guild.voice_client
    return voice_channel_to_join


@voice_command_group.command()
async def leave_voice(ctx: discord.ApplicationContext):
    """Leave the voice channel!"""
    voice_client: discord.VoiceClient = ctx.voice_client

    if not voice_client:
        return await ctx.respond("I'm not in a voice channel right now")

    await voice_client.disconnect()

    await ctx.respond("Left!")


VOICE_RECORDING_PREFIX = "Finished! Recorded audio for"


async def finished_callback(sink, channel: discord.TextChannel):
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
    await sink.vc.disconnect()
    files = [
        discord.File(audio.file, f"{user_id}.{sink.encoding}")
        for user_id, audio in sink.audio_data.items()
    ]
    await channel.send(
        f"{VOICE_RECORDING_PREFIX} {' '.join(recorded_users)}.", files=files
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


@voice_command_group.command()
async def start_recording(ctx: discord.ApplicationContext, sink: Sinks):
    """Record your voice!"""
    global voice_connections
    if not ctx.author.voice:
        return await ctx.respond("You're not in a voice channel!")

    voice_connection = voice_connections.get(ctx.guild.id, None)

    if not voice_connection:
        raise Exception("I'm not in a voice channel right now")

    voice_connection.start_recording(
        sink.value,
        finished_callback,
        ctx.channel,
    )

    await ctx.channel.send("The recording has started!")


@voice_command_group.command()
async def stop(ctx: discord.ApplicationContext):
    """Stop recording."""
    if ctx.guild.id in voice_connections:
        voice_connection = voice_connections[ctx.guild.id]
        voice_connection.stop_recording()
        del voice_connections[ctx.guild.id]
        await ctx.delete()
    else:
        await ctx.respond("Not recording in this guild.")
