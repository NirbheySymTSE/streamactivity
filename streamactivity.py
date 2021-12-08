#!/usr/bin/env python3
import asyncio
import argparse
import datetime
import time
import logging.config
from pathlib import Path

from symphony.bdk.core.config.loader import BdkConfigLoader
from symphony.bdk.core.symphony_bdk import SymphonyBdk

# Configure logging
current_dir = Path(__file__).parent
logging_conf = Path.joinpath(current_dir, 'resources', 'logging.conf')
logging.config.fileConfig(logging_conf, disable_existing_loggers=False)

# Arg parsing & Setup the configuration loading
parser = argparse.ArgumentParser()
parser.add_argument("--config", help="Config yaml file to be used")
parser.add_argument(
    "--since", default=str((round(time.time()) - 604800) * 1000),
    help="Messages sent since this timestamp (epoch) will be returned"
)
parser.add_argument("--stream", help="Please provide the conversationID of the chat being monitored")
args = parser.parse_args()
# Epoch Seconds to Millisecond Conversion
if len(args.since) <= 10: args.since = str(int(args.since) * 1000)


# ZD 34318
async def stream_messages(bdk):
    logging.debug("extracting messages")
    messages = await bdk.messages().list_messages(args.stream, since=args.since)
    return messages


async def sent_messages(messages):
    logging.debug("sorting user messages")
    sorted_messages = {}

    try:
        for message in messages:
            sender_id = str(message.user.user_id).strip()
            try:
                sorted_messages[sender_id].append(message)
            except:
                sorted_messages[sender_id]=[message]
        return sorted_messages
    except:
        return []


async def read_messages(bdk, messages):
    logging.debug("counting read messages")
    sorted_messages = {}

    try:
        for message in messages:
            message_id = message.message_id
            status = await bdk.messages().get_message_status(message_id)
            for readers in status["read"]:
                reader = readers.user_id
                try:
                    sorted_messages[reader].append(message)
                except:
                    sorted_messages[reader] = [message]
        return sorted_messages
    except:
        return []


async def write_stream_data(bdk):
    results_file = open("results.txt", "w")
    unfiltered_room_members = (await bdk.streams().list_stream_members(args.stream))["members"].value
    room_members = {}

    # Extracting userID and their email from account information
    for member_info in unfiltered_room_members:
        uid = str(member_info["user"]["user_id"])
        email = member_info["user"]["email"]
        room_members[uid] = email

    all_stream_messages = await stream_messages(bdk)
    user_sent_messages = await sent_messages(all_stream_messages)
    user_read_messages = await read_messages(bdk, all_stream_messages)

    # Header & Room Member Info
    results_file.write("StreamID: " + args.stream)
    results_file.write(
        "\nActivity in stream since " +
        str((datetime.datetime.utcfromtimestamp(round(int(args.since) / 1000))).strftime('%Y-%m-%d %H:%M:%S')) +
        "\n\nRoom members:\n"
    )

    for uid in room_members:
        results_file.write(uid + "\t" + room_members[uid] + "\n")

    # Total message sent/read stats
    results_file.write("\n\nTotal messages sent:\n\n")
    for uid in room_members:
        try:
            results_file.write("\t" + uid + '\t| ' + str(len(user_sent_messages[uid])) + '\n')
        except:
            results_file.write("\t" + uid + '\t| 0\n')

    results_file.write("\nTotal messages read:\n\n")
    for uid in room_members:
        try:
            results_file.write("\t" + uid + '\t| ' + str(len(user_read_messages[uid])) + '\n')
        except:
            results_file.write("\t" + uid + '\t| 0\n')

    # Individual messages sent/read
    results_file.write("\n\nMessages sent: \n")
    for uid in room_members:
        results_file.write('\n\t' + uid + ':\n')
        try:
            for i in user_sent_messages[uid]:
                results_file.write('\t\t' + str(i.message_id) + '\n')
        except:
            results_file.write('\t\t--\n')

    results_file.write("\n\nMessages read: \n")
    for uid in room_members:
        results_file.write('\n\t' + uid + ':\n')
        try:
            for i in user_read_messages[uid]:
                results_file.write('\t\t' + str(i.message_id) + '\n')
        except:
            results_file.write('\t\t--\n')


async def run():
    config = BdkConfigLoader.load_from_file(args.config)
    async with SymphonyBdk(config) as bdk:
        await write_stream_data(bdk)


try:
    logging.info("Running bot application...")
    asyncio.run(run())

except KeyboardInterrupt:
    logging.info("Ending bot application")
