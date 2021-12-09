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
# Extracts all sent messages within time period in stream
async def stream_messages(bdk):
    logging.debug("extracting messages")
    messages = await bdk.messages().list_messages(args.stream, since=args.since)
    return messages


# Sorts messages by who sent it, identifier keys are tupled (uid, email)
async def sent_messages(messages):
    logging.debug("sorting user sent messages")
    sorted_messages = {}

    try:
        for message in messages:
            try:
                sorted_messages[(str(message.user.user_id).strip(), message.user.email)].append(message)
            except:
                sorted_messages[(str(message.user.user_id).strip(), message.user.email)] = [message]
        return sorted_messages
    except:
        return []


# Sorts messages by who has read them, identifier keys are tupled (uid, email)
async def read_messages(bdk, messages):
    logging.debug("sorting user read messages")
    sorted_messages = {}

    try:
        for message in messages:
            status = await bdk.messages().get_message_status(message.message_id)
            for readers in status["read"]:
                try:
                    sorted_messages[(str(readers.user_id).strip(), readers.email)].append(message)
                except:
                    sorted_messages[(str(readers.user_id).strip(), readers.email)] = [message]
        return sorted_messages
    except:
        return []


async def write_stream_data(bdk):
    results_file = open("results.txt", "w")
    unfiltered_room_members = (await bdk.streams().list_stream_members(args.stream))["members"].value
    room_members = {}

    # Extracting userID and their email from account information
    for member_info in unfiltered_room_members:
        user_info = member_info["user"]["email"]
        user_id = str(member_info["user"]["user_id"]).strip()
        room_members[user_id] = user_info

    all_stream_messages = await stream_messages(bdk)
    user_sent_messages = await sent_messages(all_stream_messages)
    user_read_messages = await read_messages(bdk, all_stream_messages)

    # Header & Room Member Info
    logging.debug("writing data")
    results_file.write("StreamID: " + args.stream)
    results_file.write(
        "\nActivity in stream since " +
        str((datetime.datetime.utcfromtimestamp(round(int(args.since) / 1000))).strftime('%Y-%m-%d %H:%M:%S')) +
        "\n\nRoom members:\n"
    )

    for uid in room_members:
        results_file.write(uid + "\t" + room_members[uid] + "\n")

    # Writing users who might have interacted with room but are no longer members
    for user in user_sent_messages:
        if user[0] not in room_members.keys():
            room_members[user[0]] = user[1]

    for user in user_read_messages:
        if user[0] not in room_members.keys():
            room_members[user[0]] = user[1]

    results_file.write(
        "\n\nUsers who interacted with stream:\n"
    )
    for uid in room_members:
        results_file.write(uid + "\t" + room_members[uid] + "\n")

    # Total message sent/read stats
    logging.debug("Writing Total User Stats")
    results_file.write("\n\nTotal messages sent:\n\n")
    logging.debug("\tWriting Total Sent Stats")
    for uid in room_members:
        try:
            results_file.write("\t" + uid + '\t| ' + str(len(user_sent_messages[(uid, room_members[uid])])) + '\n')
        except Exception as e:
            logging.debug("exception triggered: " + str(e) + "\t| Expected if user has not sent any messages")
            results_file.write("\t" + uid + '\t| 0\n')

    results_file.write("\nTotal messages read:\n\n")
    logging.debug("\tWriting Total Read Stats")
    for uid in room_members:
        try:
            results_file.write("\t" + uid + '\t| ' + str(len(user_read_messages[(uid, room_members[uid])])) + '\n')
        except Exception as e:
            logging.debug("exception triggered: " + str(e) + "\t| Expected if user has not read any messages")
            results_file.write("\t" + uid + '\t| 0\n')

    # Individual messages sent/read
    logging.debug("Writing User Sent/Read Messages")
    results_file.write("\n\nMessages sent: \n")
    logging.debug("\tWriting User Sent Messages")
    for uid in room_members:
        results_file.write('\n\t' + uid + ':\n')
        try:
            for i in user_sent_messages[(uid, room_members[uid])]:
                results_file.write('\t\t' + str(i.message_id) + '\n')
        except Exception as e:
            logging.debug("exception triggered: " + str(e) + "\t| Expected if user has not sent any messages")
            results_file.write('\t\t--\n')

    results_file.write("\n\nMessages read: \n")
    logging.debug("\tWriting User Read Messages")
    for uid in room_members:
        results_file.write('\n\t' + uid + ':\n')
        try:
            for i in user_read_messages[(uid, room_members[uid])]:
                results_file.write('\t\t' + str(i.message_id) + '\n')
        except Exception as e:
            logging.debug("exception triggered: " + str(e) + "\t| Expected if user has not read any messages")
            results_file.write('\t\t--\n')


async def run():
    try:
        config = BdkConfigLoader.load_from_file(args.config)
    except Exception as e:
        logging.debug("Config Error: " + str(e))
        quit()
    async with SymphonyBdk(config) as bdk:
        await write_stream_data(bdk)


try:
    logging.info("Running bot application...")
    asyncio.run(run())

except KeyboardInterrupt:
    logging.info("Ending bot application")
