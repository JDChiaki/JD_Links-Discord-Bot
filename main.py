import discord
import os
from discord.ext import commands
import json
import random
from music import Player
from keep_alive import keep_alive

client = commands.Bot(command_prefix='~')
client.remove_command('help')


@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))


@client.command(pass_context=True, aliases=['hp', 'h', 'HELP', 'HP', 'H'])
async def help(ctx):
	chiaki = await client.fetch_user(os.environ['CHIAKI_ID'])
	help_txt = open('help.txt').read()
	hp_em = discord.Embed(title="Hello!",
	                      description=help_txt.format(client),
	                      color=0x252c8e)
	hp_em.set_author(name=chiaki.display_name, icon_url=chiaki.avatar_url)
	hp_em.set_thumbnail(
	    url=
	    "https://i.pinimg.com/originals/6d/37/9d/6d379d65271a4b92b4a22f49d7d0ad47.webp"
	)
	await ctx.send(embed=hp_em)


@client.command(pass_context=True, aliases=['dl', 'd', 'DOWNLOAD', 'DL', 'D'])
async def download(ctx, *args):
	keys = open('keys.txt').read().splitlines()
	args = [x.lower() for x in args]
	chiaki = await client.fetch_user(os.environ['CHIAKI_ID'])
	try:
		anime = keys.index(args[0]) + 1
		ep = int(args[1])
		if args[0] in keys:
			links = open(f'links/{args[0]}.txt').read().splitlines()
			if ep != 0:
				try:
					if links[ep] != 'No Data Yet':
						link_em = discord.Embed(
						    title=f"{keys[anime]} Episode {args[1]}",
						    url=links[ep],
						    description=
						    f"click to download :point_up: :point_up: \nIf the link is broken, DM {chiaki.mention} and ask for help~",
						    color=0x252c8e)
					else:
						link_em = discord.Embed(
						    title="No Data Yet!",
						    description=
						    f"Maybe next week\nidk. ask {chiaki.mention}",
						    color=0x252c8e)
					link_em.set_thumbnail(url=links[0])
					link_em.set_footer(text="Link requested by: {}".format(
					    ctx.author.display_name),
					                   icon_url=ctx.author.avatar_url)
					await ctx.send(embed=link_em)
				except IndexError:
					indxer_em = discord.Embed(
					    title=
					    f"{keys[anime]} has only {len(links)-1} Episodes!",
					    color=0x000000)
					indxer_em.set_author(name=chiaki.display_name,
					                     icon_url=chiaki.avatar_url)
					indxer_em.set_thumbnail(url=links[0])
					file = discord.File("er_gifs/mafumafu-cute.gif")
					indxer_em.set_image(url="attachment://mafumafu-cute.gif")
					await ctx.send(embed=indxer_em, file=file)
			else:
				ep0_em = discord.Embed(
				    title=f"{keys[anime]} has no Episode 0!", color=0x000000)
				ep0_em.set_author(name=chiaki.display_name,
				                  icon_url=chiaki.avatar_url)
				ep0_em.set_thumbnail(url=links[0])
				file = discord.File("er_gifs/mafumafu-neko.gif")
				ep0_em.set_image(url="attachment://mafumafu-neko.gif")
				await ctx.send(embed=ep0_em, file=file)
	except:
		askhp_em = discord.Embed(
		    title="Invalid command!",
		    description=
		    f"If you need help, type `~help` or DM {chiaki.mention}!",
		    color=0x252c8e)
		await ctx.send(embed=askhp_em)


@client.command(pass_context=True, aliases=['PIC'])
async def pic(ctx, *args):
	args = [x.lower() for x in args]
	chiaki = await client.fetch_user(os.environ['CHIAKI_ID'])
	with open('pics.json', 'r', encoding='utf-8') as picsjson:
		ani_ch_pic = json.load(picsjson)
		anis = list(ani_ch_pic.keys())
		ani_ch, chs, pics = {}, [], []
		for a in list(ani_ch_pic.values()):
			chs = chs + list(a.keys())
			for b in list(a.values()):
				pics = pics + b
		for a in ani_ch_pic:
			ani_ch.update({a: list(ani_ch_pic[a].keys())})
		chslo = [x.lower() for x in chs]
		anilo = [x.lower() for x in anis]
		chtf, ch, ani = False, str, str
		for a in chslo:
			if any(b in a for b in args):
				ch = chs[chslo.index(a)]
				for c in ani_ch:
					if ch in ani_ch[c]:
						ani = c
						break
				chtf = True
				break
		if chtf is False:
			for a in anilo:
				if any(b in a for b in args):
					ani = anis[anilo.index(a)]
					ch = random.choice(ani_ch[ani])
					break
		try:
			pic_em = discord.Embed(title=f"{ani}\n{ch}", color=0x252c8e)
			pic_em.set_image(url=f"{random.choice(ani_ch_pic[ani][ch])}")
			pic_em.set_footer(text="photo requested by: {}".format(
			    ctx.author.display_name),
			                  icon_url=ctx.author.avatar_url)
			await ctx.send(embed=pic_em)
		except:
			await ctx.send(f'No Data! Ask more to {chiaki.mention}')

async def setup():
    await client.wait_until_ready()
    client.add_cog(Player(client))

client.loop.create_task(setup())
keep_alive()
client.run(os.environ['TOKEN'])
