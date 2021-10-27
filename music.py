import asyncio
import json
import discord
import youtube_dl
import pafy
from discord.ext import commands
from pytube import Playlist


async def qu(ctx, song, po):
    paf = pafy.new(song)
    title = paf.title
    channel = paf.author
    duration = paf.duration
    thumbnail = paf.thumb

    em = discord.Embed(title=f'{title}', colour=discord.Colour.random(), url=song)
    em.set_author(icon_url=ctx.author.avatar_url, name='Add to queue')
    em.set_thumbnail(url=thumbnail)
    em.add_field(name='Channel', value=channel, inline=True)
    em.add_field(name='Duration', value=f'{duration}', inline=True)
    em.set_footer(text=f'Position in queue\n{po}')
    await ctx.send(embed=em)


async def get_prefix(guild: discord.Guild):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(guild.id)]


class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.song_queue2 = {}
        self.np = {}
        self.loop = {}
        self.ctx = {}

        self.setup()

    def setup(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []
            self.song_queue2[guild.id] = []
            self.loop[guild.id] = False
            self.np[guild.id] = ['', '']
            self.ctx[guild.id] = None

    async def check_queue(self, ctx):
        try:
            ctx.voice_client.stop()
        except AttributeError:
            pass
        if self.loop[ctx.guild.id] is True:
            return await self.play_song(ctx, self.np[ctx.guild.id][0])
        if len(self.song_queue[ctx.guild.id]) > 0:
            await self.play_song(ctx, list(self.song_queue[ctx.guild.id][0].keys())[0])
            self.song_queue[ctx.guild.id].pop(0)

    async def serch_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(
            {"format": "bestaudio", "quiet": True}).extract_info(f"ytsearch{amount}:{song}", download=False,
                                                                 ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0:
            return None
        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        paf = pafy.new(song)
        url = paf.getbestaudio().url
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 1
        self.np[ctx.guild.id][0] = song
        self.np[ctx.guild.id][1] = ctx.author.id
        await ctx.send(f'**Now playing** :notes: `{paf.title}`')

    async def ex_plys(self, ctx, song):
        plys = Playlist(song)
        queue_len = len(self.song_queue[ctx.guild.id])
        if queue_len < 30:
            for song in plys:
                song = {song: ctx.author.id}
                self.song_queue[ctx.guild.id].append(song)
                self.song_queue2[ctx.guild.id].append(song)
            em = discord.Embed(title=plys.title, url=plys.playlist_url, colour=discord.Colour.random())
            em.set_author(icon_url=ctx.author.avatar_url, name='Added to the queue')
            em.add_field(inline=True, name='Position in the queue', value=f'{queue_len+1}')
            em.add_field(inline=True, name='Enqueued', value=f'`{plys.length}` songs')
            thumb = pafy.new(plys[0]).bigthumbhd
            em.set_thumbnail(url=thumb)
            await ctx.send(embed=em)
            if ctx.voice_client.source is None:
                await self.play_song(ctx, plys[0])
        else:
            await ctx.send('**Queue limit reached!**')

    @commands.command(aliases=['connect', 'j'])
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send(':x: **You have to be in a voice channel to use this command.**')
        if ctx.voice_client is not None:
            self.ctx[ctx.guild.id] = ctx
            return await ctx.voice_client.move_to(ctx.author.voice.channel)
        self.ctx[ctx.guild.id] = ctx
        await ctx.author.voice.channel.connect()

    @commands.command(aliases=['dc', 'dis', 'disconnect'])
    async def leave(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send(':x: **I am not connected to a voice channel.**\n Type `^join` to get me in one')
        if ctx.author.voice.channel.id == ctx.voice_client.channel.id:
            await ctx.voice_client.disconnect()
            self.song_queue[ctx.guild.id] = []
            self.song_queue2[ctx.guild.id] = []
            self.loop[ctx.guild.id] = False
            self.np[ctx.guild.id] = ['', '']
            return await ctx.send(':mailbox_with_no_mail: **Successfully disconnected**')
        else:
            await ctx.send(':x: **You have to join the same voice channel with me to use this command**')

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, song=None):
        if song is None:
            em = discord.Embed(title=':x: **Invalid usage**', description='`^play <link or query>`',
                               colour=discord.Colour.red())
            return await ctx.send(embed=em)
        if ctx.author.voice is None:
            return await ctx.send(':x: **You have to be in a voice channel to use this command.**')
        if ctx.voice_client is None:
            self.ctx[ctx.guild.id] = ctx
            await ctx.author.voice.channel.connect()
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send(':x: **You have to join the same voice channel with me to use this command**')
        if 'playlist?list=' in song:
            return await self.ex_plys(ctx, song)
        if not ('youtube.com/watch?' in song or 'https://youtu.be/' in song):
            await ctx.send(f':musical_note: Searching :mag_right: `{song}`')

            result = await self.serch_song(1, song, get_url=True)

            if result is None:
                return await ctx.send(':x: **No matches**')

            song = result[0]
            song2 = {song: ctx.author.id}
            self.song_queue2[ctx.guild.id].append(song2)

        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 30:
                song = {song: ctx.author.id}
                self.song_queue[ctx.guild.id].append(song)
                self.song_queue2[ctx.guild.id].append(song)
                qu_op = queue_len + 1
                return await qu(ctx, list(song.keys())[0], qu_op)
            else:
                return await ctx.send("up to 10")

        await self.play_song(ctx, song)

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) == 0:
            em = discord.Embed(title='There is currently no queue', colour=discord.Colour.random())
            return await ctx.send(embed=em)
        paf = pafy.new(self.np[ctx.guild.id][0])
        npby_id = None
        for song in self.song_queue2[ctx.guild.id]:
            if self.np[ctx.guild.id][0] == list(song.keys())[0]:
                npby_id = song[self.np[ctx.guild.id][0]]
        npby = await self.bot.fetch_user(npby_id)
        em = discord.Embed(title=f'Queue for {ctx.guild.name}',
                           description=f'__Now playing:__\n[{paf.title}]({self.np[ctx.guild.id][0]}) | `{paf.duration}'
                                       f'\nRequested by: {npby.name}#{npby.discriminator}'
                                       f'`\n\n__Queue__\n',
                           colour=discord.Colour.random())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            paf = pafy.new(list(url.keys())[0])
            rqby = await self.bot.fetch_user(list(url.values())[0])
            em.description += f'`{i}.` [{paf.title}]({list(url.keys())[0]}) | `{paf.duration}`\n' \
                              f'`Requested by: {rqby.name}#{rqby.discriminator}`\n\n'
            i += 1
        a = ''
        if self.loop[ctx.guild.id] is True:
            a = '✔'
        elif self.loop[ctx.guild.id] is False:
            a = '❌'
        em.set_footer(icon_url=ctx.author.avatar_url, text=f'Loop: {a} | Total: {len(self.song_queue[ctx.guild.id])}\n'
                                                           f'Thanks for using Chiaki\'s bot UwU')
        await ctx.send(embed=em)

    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send(':x: **I am not connected to a voice channel.**\n Type `^join` to get me in one')
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send(':x: **You have to join the same voice channel with me to use this command**')

        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}",
                             description="**80% of the voice channel must vote to skip for it to pass.**",
                             colour=discord.Colour.random())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.send(
            embed=poll)  # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705")  # yes
        await poll_msg.add_reaction(u"\U0001F6AB")  # no

        await asyncio.sleep(5)  # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)

        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user != self.bot.user:
                        member = await ctx.guild.fetch_member(user.id)
                        if member.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted:
                            votes[reaction.emoji] += 1

                            reacted.append(user.id)

        skip = False
        embed = discord.Embed
        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (
                    votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79:  # 80% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful",
                                      description="***Voting to skip the current song was succesful, skipping now.***",
                                      colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed",
                                  description="*Voting to skip the current song has failed.*\n\n**Voting failed, "
                                              "the vote requires at least 80% of the members to skip.**",
                                  colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            await ctx.send(':fast_forward: ***Skipped*** :thumbsup:')
            self.loop[ctx.guild.id] = False
            await self.check_queue(ctx)

    @commands.command()
    async def loop(self, ctx):
        if self.loop[ctx.guild.id] is False:
            self.loop[ctx.guild.id] = True
            return await ctx.send(':repeat_one: **Enabled!**')
        if self.loop[ctx.guild.id] is True:
            self.loop[ctx.guild.id] = False
            return await ctx.send(':repeat_one: **Disabled!**')

    @commands.command(aliases=['stop'])
    async def pause(self, ctx):
        ctx.voice_client.pause()
        await ctx.send('**Paused** :pause_button:')

    @commands.command()
    async def resume(self, ctx):
        ctx.voice_client.resume()
        await ctx.send(':play_pause: **Resuming**')

    @commands.command(aliases=['clrq'])
    @commands.has_permissions(manage_channels=True)
    async def clearqueue(self, ctx):
        self.song_queue[ctx.guild.id] = []
        self.loop[ctx.guild.id] = False
        await ctx.send('***Queue cleared!***')

    @commands.command(aliases=['r'])
    async def remove(self, ctx, arg):
        try:
            arg = int(arg)
        except ValueError:
            em = discord.Embed(description=':x: ***Invalid command***\n`^remove <index>`',
                               colour=discord.Colour.random())
            return await ctx.send(embed=em)
        paf = pafy.new(list(self.song_queue[ctx.guild.id][arg - 1].keys())[0])
        self.song_queue[ctx.guild.id].pop(arg - 1)
        em = discord.Embed(description=f'Removed `{paf.title}`', colour=discord.Colour.random())
        em.set_footer(icon_url=ctx.author.avatar_url, text=f'Removed by {ctx.author.name}#{ctx.author.discriminator}')
        await ctx.send(embed=em)

    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx):
        paf = pafy.new(self.np[ctx.guild.id][0])
        em = discord.Embed(title=f'{paf.title}', url=self.np[ctx.guild.id][0], colour=discord.Colour.random())
        em.set_thumbnail(url=paf.thumb)
        em.add_field(name='Channel', value=paf.author, inline=True)
        em.add_field(name='Duration', value=paf.duration, inline=True)
        npby_id = None
        for song in self.song_queue2[ctx.guild.id]:
            if self.np[ctx.guild.id][0] == list(song.keys())[0]:
                npby_id = song[self.np[ctx.guild.id][0]]
        npby = await self.bot.fetch_user(npby_id)
        em.set_footer(icon_url=npby.avatar_url, text=f'Requsted by: {npby.name}#{npby.discriminator}')
        await ctx.send(embed=em)

    @commands.command(aliases=['fs'])
    @commands.has_permissions(manage_channels=True)
    async def forceskip(self, ctx):
        await ctx.send(':fast_forward: ***Forceskipped*** :thumbsup:')
        self.loop[ctx.guild.id] = False
        await self.check_queue(ctx)

    @forceskip.error
    async def fs_permission_error(self, error, ctx):
        if isinstance(error, commands.MissingPermissions):
            em = discord.Embed(description=f'{ctx.author.name}! '
                                           f'You must have `Maanage Channels` permissions to use this command',
                               colour=discord.Colour.red())
            await ctx.send(embed=em)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, _):
        if member != self.bot.user:
            for client in self.bot.voice_clients:
                if client.channel == before.channel:
                    if len(client.channel.members) == 1:
                        if client.channel.members[0] == self.bot.user:
                            await asyncio.sleep(30.0)
                            if len(client.channel.members) == 1:
                                if client.channel.members[0] == self.bot.user:
                                    await client.disconnect()
                                    await self.ctx[member.guild.id].send('**Disconnected cuz '
                                                                         'I feels lonely** :crying_cat_face: ')
