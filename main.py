import discord
import os
from discord.ext import commands
from keep_alive import keep_alive

client = commands.Bot(command_prefix = ['~', '-'])
client.remove_command('help')

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))

@client.command(pass_context = True , aliases=['hp', 'h', 'HELP', 'HP', 'H'])
async def help(ctx):
	chiaki = await client.fetch_user(559408261116461067)
	help_txt = open('help.txt').read()
	hp_em=discord.Embed(title="Hello!", description=help_txt.format(client), color=0x252c8e)
	hp_em.set_author(name=chiaki.display_name, icon_url=chiaki.avatar_url)
	hp_em.set_thumbnail(url="https://i.pinimg.com/originals/6d/37/9d/6d379d65271a4b92b4a22f49d7d0ad47.webp")
	await ctx.send(embed=hp_em)

@client.command(pass_context = True , aliases=['dl', 'd', 'DOWNLOAD', 'DL', 'D'])
async def download(ctx, *arg):
	keys = open('keys.txt').read().splitlines()
	arg = [x.lower() for x in arg]
	chiaki = await client.fetch_user(559408261116461067)
	try:
		anime = keys.index(arg[0]) + 1
		ep = int(arg[1])
		if arg[0] in keys:
			links = open(f'links/{arg[0]}.txt').read().splitlines()
			try:
				if links[ep] != 'No Data Yet':
					link_em = discord.Embed(title=f"{keys[anime]} Episode {arg[1]}", url=links[ep], description=f"click to download :point_up: :point_up: \nIf the link is broken, DM {chiaki.mention} and ask for help~", color=0x252c8e)
				else:
					link_em = discord.Embed(title="No Data Yet!", description=f"Maybe next week\nidk. ask {chiaki.mention}", color=0x252c8e)
				link_em.set_thumbnail(url=links[0])
				link_em.set_footer(text="Link requested by: {}".format(ctx.author.display_name), icon_url=ctx.author.avatar_url)
				await ctx.send(embed=link_em)
			except IndexError:
				indxer_em = discord.Embed(title=f"{keys[anime]} has only {len(links)-1} Episodes!", color=0x000000)
				indxer_em.set_author(name=chiaki.display_name, icon_url=chiaki.avatar_url)
				file = discord.File("mafumafu-cute.gif")
				indxer_em.set_image(url="attachment://mafumafu-cute.gif")
				await ctx.send(embed=indxer_em, file=file)
	except:
		askhp_em = discord.Embed(title="Invalid command!", description=f"If you need help, type `~help` or DM {chiaki.mention}!", color=0x252c8e)
		await ctx.send(embed=askhp_em)
	
keep_alive()
my_secret = os.environ['TOKEN']
client.run(my_secret)