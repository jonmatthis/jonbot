import logging
import os
from copy import deepcopy
from datetime import datetime

import discord
from discord import Forbidden
from discord.ext import commands

from chatbot.discord_bot.cogs.thread_scraper_cog.message_anonymizer import anonymize_message
from chatbot.discord_bot.cogs.thread_scraper_cog.thread_stats import ThreadStats
from chatbot.mongo_database.mongo_database_manager import MongoDatabaseManager
from chatbot.student_info.find_student_name import find_student_info, get_initials
from chatbot.student_info.load_student_info import load_student_info
from chatbot.system.environment_variables import get_admin_users
from chatbot.system.filenames_and_paths import get_thread_backups_collection_name

logger = logging.getLogger(__name__)

logging.getLogger('discord').setLevel(logging.INFO)


class ThreadScraperCog(commands.Cog):
    def __init__(self,
                 bot: discord.Bot,
                 mongo_database_manager: MongoDatabaseManager):
        self.bot = bot
        self.mongo_database_manager = mongo_database_manager
        self.student_info = load_student_info()

    @discord.slash_command(name='scrape_threads', description='(ADMIN ONLY) Scrape all threads in the current server')
    @discord.option(name="timestamp_backup",
                    description="Whether or not add a timestamp to the backup filename",
                    input_type=bool,
                    default=True)
    @discord.option(name="full_server_backup",
                    description="Whether or not to backup the entire server",
                    input_type=bool,
                    default=True)
    async def scrape_threads(self,
                             ctx: discord.ApplicationContext,
                             timestamp_backup: bool = True,
                             full_server_backup: bool = True,
                             ):

        total_thread_count = 0

        collection_name = get_thread_backups_collection_name(server_name=ctx.guild.name)

        anonymized_collection_name = "anonymized_" + collection_name

        # Make sure we're only responding to the admin users
        if not ctx.user.id in get_admin_users():
            logger.info(f"User {ctx.user_id} is not an admin user")
            return

        status_message = await ctx.author.send(
            f"Starting thread scraping process for server: {ctx.guild.name} on {datetime.now().isoformat()}\n___________\n")

        channels = await self.get_channels(ctx, full_server_backup)
        thread_count_per_channel = {}
        for channel in channels:
            if not isinstance(channel, discord.TextChannel):
                continue
            threads = await self.get_list_of_threads(channel)
            if len(threads) == 0:
                logger.info(f"No threads in channel: {channel.name}")
                continue

            thread_count_per_channel[channel.name] = 0
            for thread in threads:  # Loop through each thread
                thread_stats = ThreadStats(bot_id=self.bot.user.id)
                anonymized_thread_stats = ThreadStats(bot_id=self.bot.user.id)

                total_thread_count += 1
                thread_count_per_channel[channel.name] += 1

                saving_thread_string = f"{total_thread_count}: Channel:`{str(channel)}`:{thread.jump_url}"
                logger.info(saving_thread_string)

                status_message = await self.send_status_message_update(ctx, saving_thread_string, status_message)

                thread_owner_username = thread.name.split("'")[0]
                student_discord_username, \
                    student_name, \
                    student_uuid = find_student_info(
                    thread_owner_username)

                mongo_query = {
                    "_student_name": student_name,
                    "_student_username": student_discord_username,
                    "_student_uuid": student_uuid,
                    "_student_initials": get_initials(name=student_name),
                    "server_name": ctx.guild.name,
                    "thread_title": thread.name,
                    "thread_id": thread.id,
                    "thread_url": thread.jump_url,
                    "created_at": thread.created_at,
                    "channel": channel.name,
                }

                anonymized_mongo_query = deepcopy(mongo_query)
                anonymized_mongo_query["_student_name"] = "REDACTED"
                anonymized_mongo_query["_student_username"] = "REDACTED"
                anonymized_mongo_query["thread_title"] = "REDACTED"

                async for message in thread.history(limit=None, oldest_first=True):
                    thread_stats.update(message)
                    anonymized_thread_stats.update(anonymize_message(message))
                    message_author_str = str(message.author)

                    message_content = message.content
                    if message_content == '':
                        continue

                    message_update_package = {
                        'human': message.author.bot == self.bot.user.id,
                        'author': message_author_str,
                        'author_id': message.author.id,
                        'user_id': message.author.id,
                        'content': message_content,
                        'jump_url': message.jump_url,
                        'created_at': message.created_at,
                        'id': message.id,
                        'reactions': [str(reaction) for reaction in message.reactions],
                        'parent_message_id': message.reference.message_id if message.reference else '',
                    }

                    anonymized_message_update_package = deepcopy(message_update_package)
                    anonymized_message_update_package['author'] = "REDACTED"
                    anonymized_message_update_package['author_id'] = "REDACTED"
                    anonymized_message_update_package['user_id'] = "REDACTED"
                    anonymized_message_update_package['content'] = anonymize_message(message).content

                    thread_stats_dict = thread_stats.dict()
                    thread_as_list_of_strings = deepcopy(thread_stats_dict['thread_as_list_of_strings'])
                    thread_as_one_string = deepcopy(thread_stats_dict['thread_as_one_string'])
                    del thread_stats_dict['thread_as_list_of_strings']
                    del thread_stats_dict['thread_as_one_string']

                    anonymized_thread_stats_dict = anonymized_thread_stats.dict()
                    anonymized_thread_as_list_of_strings = deepcopy(
                        anonymized_thread_stats_dict['thread_as_list_of_strings'])
                    anonymized_thread_as_one_string = deepcopy(anonymized_thread_stats_dict['thread_as_one_string'])
                    del anonymized_thread_stats_dict['thread_as_list_of_strings']
                    del anonymized_thread_stats_dict['thread_as_one_string']

                    await self.mongo_database_manager.upsert(
                        collection=collection_name,
                        query=mongo_query,
                        data={"$addToSet": {"messages": message_update_package},
                              "$set": {"thread_as_list_of_strings": thread_as_list_of_strings,
                                       "thread_as_one_string": thread_as_one_string,
                                       "thread_statistics": thread_stats_dict,
                                       }
                              }
                    )
                    await self.mongo_database_manager.upsert(
                        collection=anonymized_collection_name,
                        query=anonymized_mongo_query,
                        data={"$addToSet": {"messages": anonymized_message_update_package},
                              "$set": {"thread_as_list_of_strings": anonymized_thread_as_list_of_strings,
                                       "thread_as_one_string": anonymized_thread_as_one_string,
                                       "thread_statistics": anonymized_thread_stats_dict,
                                       }
                              }
                    )

        file_name = f"{ctx.guild.name}_thread_backup_{datetime.now().isoformat(sep='_')}.json"
        database_backup_path = os.getenv("PATH_TO_COURSE_DATABASE_BACKUPS")
        if database_backup_path is None:
            raise Exception("PATH_TO_COURSE_DATABASE_BACKUPS not set in .env file")

        save_path = os.path.join(database_backup_path, file_name)
        await self.mongo_database_manager.save_json(collection_name=collection_name, save_path=save_path)

        await status_message.edit(content=f"Finished saving {total_thread_count} threads")
        print(f"Finished saving {total_thread_count} threads")

    async def send_status_message_update(self, ctx, saving_thread_string, status_message):
        update_status_message_string = status_message.content + f"\n{saving_thread_string}"
        number_of_characters_in_status_message = len(update_status_message_string)
        print(f"Number of characters in status message: {number_of_characters_in_status_message}")
        if number_of_characters_in_status_message >= 1900:
            print(f"Sending new message because {number_of_characters_in_status_message} characters")
            status_message = await ctx.author.send(
                "`--2000 character limit reached, sending new message--`")
            update_status_message_string = f"---\n{saving_thread_string}"
        status_message = await  status_message.edit(content=update_status_message_string)
        return status_message

    async def get_channels(self, ctx, full_server_backup):
        if full_server_backup:
            channels = await ctx.guild.fetch_channels()
            logger.info(f"Saving all threads in server: {ctx.guild.name}")
        else:
            channels = [ctx.channel]
            logger.info(f"Saving all threads in channel: {ctx.channel.name}")
        return channels

    async def get_list_of_threads(self, channel: discord.TextChannel):
        threads = []
        try:
            async for message in channel.history():
                if message.thread:
                    if not message.thread in threads:
                        threads.append(message.thread)
        except Forbidden:
            logger.info(f"Could not access channel: {channel.name}")
            pass
        return threads

    def determine_if_green_check_present(self, message: discord.Message):
        reactions = message.reactions
        green_check_emoji_present = False

        if len(reactions) > 0:
            for reaction in reactions:
                if reaction.emoji == '✅':
                    print(message.content)
                    green_check_emoji_present = True
                    break

        if "Successfully sent summary" in message.content:
            # i forgot that I also put the checkmark on the "Successfully sent summary" message, but those dont count for this purpose
            green_check_emoji_present = False

        return green_check_emoji_present
