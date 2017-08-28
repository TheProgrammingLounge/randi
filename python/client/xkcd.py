import sys
import discord
import logging
import asyncio
import json
import random

PATH = dict ()
try:
    with open (sys.argv [1]) as path_file:
        PATH = json.load (path_file)
except IndexError: #FileNotFoundError
    print ('Usage: python {} path/to/xkcd.path.json.priv'.format (sys.argv [0]))
    exit (1)
except FileNotFoundError:
    print ('Unable to open file: {}'.format (sys.argv[1]))
    exit (2)

sys.path.insert (0, PATH['lib'])
try:
    import client_helpers as CLIENT
except ModuleNotFoundError:
    print ('Error: Module client_helpers not found in path.')
    exit (2)

JSON = PATH['json']
# Yep you should rename your config.json and append priv to it
# This way you won't add even more private stuff on github
CONFIG = JSON + "xkcd.config.json.priv"
INDEX = JSON + "xkcd.index.json"
REF = JSON + "xkcd.references.json"
BL = JSON + "xkcd.common.json"

logging.basicConfig (level = logging.INFO)

wame_config = dict ()
xkcd_index = dict ()
xkcd_refs = dict ()

wame_config = CLIENT.loadJson (CONFIG)
xkcd_index = CLIENT.loadJson (INDEX)
xkcd_refs = CLIENT.loadJson (REF)
blk_list = CLIENT.loadJson (BL)

wame_help = discord.Embed \
        (title = wame_config['help']['title'], \
        colour = discord.Colour(0x123654), \
        url = wame_config['help']['url'], \
        description = wame_config['help']['description'])
wame_help.set_footer (text = wame_config['help']['footer'], \
        icon_url = wame_config['help']['icon_url'])

Wame = discord.Client ()
wgame = discord.Game (name = wame_config['game'])

@Wame.event
async def on_ready ():
    await Wame.change_presence (game = wgame)
    bug_channel = Wame.get_channel (wame_config['report_channel'])
    CLIENT.greet (Wame, channel = bug_channel)

@Wame.event
async def on_message (message):
    if not message.content.startswith (wame_config['prefix']):
        if Wame.user.mentioned_in(message) and not message.mention_everyone \
                and not len(message.content.split("@here")) > 1 \
                and len(message.mentions) == 1:
                    await Wame.send_message \
                            (message.channel, embed = wame_help)
    else:
        args = await CLIENT.parse_args (message.content, wame_config['prefix'])
        command = args[0]
        args = args[1:]
        logging.info ('\nFull mess: {}\nCommand  : {}\nArgs     : {}'\
                .format (message.content, command, args))

        if command == 'xkcd':
            tmp = await Wame.send_message (message.channel, 'Searching...')

            if len (args) is 0:
                embed_comic = await CLIENT.random_embed (xkcd_refs)
                await Wame.edit_message (tmp, ' ', embed = embed_comic)
            else:
                result = await CLIENT.search \
                    (' '.join(args), xkcd_index, xkcd_refs, blk_list)
                # 0 == comic found
                if result['status'] == 0:
                    # Create embed
                    embed_comic = await \
                            CLIENT.create_embed (result['comic'])
                    await Wame.edit_message (tmp, ' ', embed = embed_comic)
                else:
                    # It hasn't been found, too bad
                    not_found = discord.Embed (description =
                        "_I found nothing. I'm so sawry and sad :(_. \
                    \nReply with **`random`** for a surprise\n", \
                    colour = (0x000000))
                    await Wame.edit_message (tmp, " ", embed = not_found)
                    msg = await Wame.wait_for_message \
                            (author = message.author, \
                            content = "random", timeout = 20)
                    if (msg):
                        embed_comic = await CLIENT.random_embed (xkcd_refs)
                        await Wame.send_message \
                                (message.channel, embed = embed_comic)
                    else:
                        await Wame.edit_message (tmp, "Timeout")
        elif command == 'random':
            embed_comic = await CLIENT.random_embed (xkcd_refs)
            await Wame.send_message (message.channel, embed = embed_comic)
        elif command == 'latest':
            online_latest = await CLIENT.get_online_xkcd ()
            
            if online_latest['status'] is 0: 
                embed_comic = await \
                        CLIENT.create_embed(online_latest)
            else:
                local_latest = xkcd_refs[str(max(list(xkcd_refs.keys ())))]
                embed_comic = await \
                        CLIENT.create_embed (local_latest)
            await Wame.send_message (message.channel, embed = embed_comic)
        elif command == 'report':
            bug_channel = Wame.get_channel (wame_config['report_channel'])
            embed_report = await CLIENT.report_embed (message, \
                    {'type': 'User', 'color': (0xff0000), 'client': Wame})
            report = await Wame.send_message (bug_channel, embed = embed_report)
            await Wame.pin_message (report)
        elif command == 'help':
            await Wame.send_message (message.channel, \
                    embed = wame_help)

Wame.run (wame_config['token'])
