import os
import shutil
import json
import re
from typing import List, Tuple

import py7zr
import discord
import yaml
from dotenv import load_dotenv
from logger import getLogger, set_global_logging_level

set_global_logging_level('DEBUG')
l = getLogger("main")

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FLASH_GAMES_CHANNEL = int(os.getenv('FLASH_GAMES_CHANNEL'))
OTHER_GAMES_CHANNEL = int(os.getenv('OTHER_GAMES_CHANNEL'))
ANIMATIONS_CHANNEL = int(os.getenv('ANIMATIONS_CHANNEL'))
AUDITIONS_CHANNEL = int(os.getenv('AUDITIONS_CHANNEL'))
CURATOR_LOUNGE_CHANNEL = int(os.getenv('CURATOR_LOUNGE_CHANNEL'))
AUDITION_CHAT_CHANNEL = int(os.getenv('AUDITION_CHAT_CHANNEL'))

client = discord.Client()


@client.event
async def on_ready():
    l.info(f"{client.user} connected")


@client.event
async def on_message(message: discord.Message):
    await check_curations(message)


def curation_validator(filename: str) -> Tuple[List, List]:
    errors: List = []
    warnings: List = []

    # process archive
    archive = py7zr.SevenZipFile(filename, mode='r')
    filenames = archive.getnames()
    archive.extractall()
    archive.close()

    # check files
    uuid_folder_regex = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    content_folder_regex = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/content$")
    meta_regex = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\/meta\.(yaml|txt)$")
    logo_regex = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\/logo\.(png|jpg|jpeg)$")
    ss_regex = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\/ss\.(png|jpg|jpeg)$")
    uuid_folder = [match for match in filenames if uuid_folder_regex.match(match) is not None]
    content_folder = [match for match in filenames if content_folder_regex.match(match) is not None]
    meta = [match for match in filenames if meta_regex.match(match) is not None]
    logo = [match for match in filenames if logo_regex.match(match) is not None]
    ss = [match for match in filenames if ss_regex.match(match) is not None]

    props: dict = {}
    if not uuid_folder:
        errors.append("Root folder format is invalid. It should be a UUIDv4.")
    if not content_folder:
        errors.append("Content folder not found.")
    if not logo:
        errors.append("Logo file is either missing or its filename is incorrect.")
    if not ss:
        errors.append("Screenshot file is either missing or its filename is incorrect.")

    # process meta
    if not meta:
        errors.append("Missing meta file! Are you curating using Flashpoint Core?")
    else:
        # TODO check meta file extension properly
        with open(meta[0]) as meta_file:
            try:
                props: dict = yaml.safe_load(meta_file)
            except yaml.YAMLError:  # If this is being called, it's a meta .txt
                break_index: int = 0
                while break_index != -1:
                    props, break_index = parse_lines_until_multiline(meta_file.readlines(), props,
                                                                     break_index)
                    props, break_index = parse_multiline(meta_file.readlines(), props, break_index)

        # TODO replace these string boolifications with something more sensible
        title: tuple[str, bool] = ("Title", bool(props["Title"]))
        # developer: tuple[str, bool] = ("Developer", bool(props["Developer"]))

        release_date: tuple[str, bool] = ("Release Date", bool(props["Release Date"]))
        if release_date[1]:
            date_string = props["Release Date"]
            regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            if not regex.match(date_string):
                errors.append("Release date is incorrect. Release dates should always be in `YYYY-MM-DD` format.")

        language_properties: tuple[str, bool] = ("Languages", bool(props["Languages"]))
        if language_properties[1]:
            with open("language-codes.json") as f:
                list_of_language_codes: list[dict] = json.load(f)
                language_str: str = props["Languages"]
                languages = language_str.split(";")
                languages = [x.strip(' ') for x in languages]
                language_codes = []
                for x in list_of_language_codes:
                    language_codes.append(x["alpha2"])
                for language in languages:
                    if language not in language_codes:
                        if language == "sp":
                            errors.append("The correct ISO 639-1 language code for Spanish is `es`, not `sp`.")
                        elif language == "ge":
                            errors.append("The correct ISO 639-1 language code for German is `de`, not `ge`.")
                        elif language == "jp":
                            errors.append("The correct ISO 639-1 language code for Japanese is `ja`, not `jp`.")
                        elif language == "kr":
                            errors.append("The correct ISO 639-1 language code for Korean is `ko`, not `kr`.")
                        elif language == "ch":
                            errors.append("The correct ISO 639-1 language code for Chinese is `zh`, not `ch`.")
                        elif language == "iw":
                            errors.append("The correct ISO 639-1 language code for Hebrew is `he`, not `iw`.")
                        elif language == "cz":
                            errors.append("The correct ISO 639-1 language code for Czech is `cs`, not `cz`.")
                        elif language == "pe":
                            errors.append("The correct ISO 639-1 language code for Farsi is `fa`, not `pe`.")
                        else:
                            errors.append(f"Code `{language}` is not a valid ISO 639-1 language code.")

        tag: Tuple[str, bool] = ("Tags", bool(props["Tags"]))
        source: Tuple[str, bool] = ("Source", bool(props["Source"]))
        status: Tuple[str, bool] = ("Status", bool(props["Status"]))
        launch_command: Tuple[str, bool] = ("Launch Command", bool(props["Launch Command"]))
        application_path: Tuple[str, bool] = ("Application Path", bool(props["Application Path"]))

        # TODO check description?
        # description: Tuple[str, bool] = ("Description", bool(props["Original Description"]))
        # if description[1] is False and (
        #         bool(props["Curation Notes"]) or bool(props["Game Notes"])):
        #     reply += "Make sure you didn't put your description in the notes section.\n"

        if "https" in props["Launch Command"]:
            errors.append("Found `https` in launch command. All launch commands must use `http` instead of `https`.")
        mandatory_props: List[Tuple[str, bool]] = [title, language_properties, source, launch_command, tag, status, application_path]

        # TODO check optional props?
        # optional_props: list[tuple[str, bool]] = [developer, release_date, tag, description]
        # if not all(optional_props[1]): for x in optional_props: if x[1] is False: reply += x[0] +
        # "is missing, but not necessary. Add it if you can find it, but it's okay if you can't.\n"

        tags: List[str] = props["Tags"].split(";")
        tags: List[str] = [x.strip(' ') for x in tags]
        with open('tags.txt') as file:
            contents = file.read()
            for tag in tags:
                if tag not in contents:
                    warnings.append(f"Tag `{tag}` is not a known tag.")
        if not all(mandatory_props[1]):
            for prop in mandatory_props:
                if prop[1] is False:
                    errors.append(f"Property `{prop[0]}` is missing.")

    for filename in filenames:
        shutil.rmtree(filename, True)

    return errors, warnings


async def check_curations(message: discord.Message):
    if len(message.attachments) != 1:
        return

    is_flash_game = message.channel.id == FLASH_GAMES_CHANNEL
    is_other_game = message.channel.id == OTHER_GAMES_CHANNEL
    is_animation = message.channel.id == ANIMATIONS_CHANNEL
    is_audition = message.channel.id == AUDITIONS_CHANNEL

    # TODO disable
    is_curator_lounge = message.channel.id == CURATOR_LOUNGE_CHANNEL

    if not (is_flash_game or is_other_game or is_animation or is_audition or is_curator_lounge):
        return

    attachment = message.attachments[0]
    archive_filename: str = attachment.filename
    if not archive_filename.endswith('7z'):
        return

    l.debug(f"detected message '{message.id}' with 7z attachment '{archive_filename}'")
    l.debug(f"downloading attachment '{attachment.id}' - '{archive_filename}'...")
    await attachment.save(archive_filename)

    curation_errors, curation_warnings = curation_validator(archive_filename)

    # archive cleanup
    os.remove(archive_filename)

    # format reply
    final_reply: str = ""
    if len(curation_errors) > 0 or len(curation_warnings) > 0:
        author: discord.Member = message.author
        final_reply += author.mention + " Your curation has some problems:\n"
    if len(curation_errors) > 0:
        await message.add_reaction('🚫')
        for curation_error in curation_errors:
            final_reply += f"🚫 {curation_error}\n"

    if len(curation_warnings) > 0:
        await message.add_reaction('⚠️')
        for curation_warning in curation_warnings:
            final_reply += f"⚠️ {curation_warning}\n"

    if len(final_reply) > 0:
        reply_channel: discord.TextChannel = client.get_channel(CURATOR_LOUNGE_CHANNEL)
        if is_flash_game or is_other_game or is_animation:
            reply_channel = client.get_channel(CURATOR_LOUNGE_CHANNEL)
        elif is_audition:
            reply_channel = client.get_channel(AUDITION_CHAT_CHANNEL)
        l.info("sending reply to message '{message.id}' : '" + final_reply.replace('\n', ' ') + "'")
        await reply_channel.send(final_reply)
    else:
        await message.add_reaction('🤖')


def parse_lines_until_multiline(lines: List[str], d: dict, starting_number: int):
    break_number: int = -1
    for idx, line in enumerate(lines[starting_number:]):
        if '|' not in line:
            split: List[str] = line.split(":")
            split: List[str] = [x.strip(' ') for x in split]
            d.update({split[0]: split[1]})
        else:
            break_number = idx
            break
    return d, break_number


def parse_multiline(lines: List[str], d: dict, starting_number: int):
    break_number = -1
    key: str = ""
    val: str = ""
    for idx, line in enumerate(lines[starting_number:]):
        if idx is starting_number:
            split = line.split(':')
            split = [x.strip(' ') for x in split]
            key = split[0]
        else:
            if line.startswith('\t'):
                line = line.strip(" \t")
                val += line
            else:
                break_number = idx
                break
    d.update({key: val})
    return d, break_number


client.run(TOKEN)
