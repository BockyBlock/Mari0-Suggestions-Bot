import discord
import discord.ext.commands as CM
import discord.app_commands as AC
from discord import Interaction as Itr

import time, asyncio
from random import choice
from typing import Literal

from suggestbot import SuggestBot
from suggestions import createSuggestion

class MainCog(CM.Cog):
	def __init__(self, client:SuggestBot):
		self.client = client

	@AC.command(name="ping", description="Check the Bot and API latency.")
	async def ping(self, itr:Itr):
		start_time = time.time()
		await itr.response.send_message("Testing Ping...", ephemeral=True)
		apitime = time.time()-start_time
		await itr.edit_original_response(content="Ping Pong motherfliper!```\nBOT: {:.2f} seconds\nAPI: {:.2f} seconds\n```".format(self.client.latency, apitime))

	@AC.command(name="info", description="Everything you need to know about the bot.")
	async def info(self, itr:Itr):
		content = '''
			This is a Discord version of the Mari0 Suggestion Twitter Bot created by NH1507.
			Suggestions from this bot are compleatly randomised, from the enemies and objects to the grammer and formating.

			**Get started by running /generate!**

			> [Twitter Version](https://twitter.com/Mari0AE_Bot)
			> [Aidan's Server](https://discord.gg/KXrDUZfBpq)
		'''
		embed = discord.Embed(title="Hey! I'm the Mari0 Suggestion Bot!", description=content, color=discord.Color.brand_red())
		await itr.response.send_message(embed=embed, ephemeral=True)

	###

	@AC.command(name="add-suggestions", description="Add objects to the lists for this server.")
	async def add_suggestions(self, itr:Itr, group:Literal["Names", "Games", "Enemies", "People", "Powerups"]="Enemies", suggestion:str=None):
		if not suggestion:
			await itr.response.send_message("The Suggestion field is required, try again!", ephemeral=True)

		valuename = "custom_" + group.lower()
		grouplist = self.client.CON.get_value(itr.guild, valuename)
		grouplist.append(suggestion)
		await self.client.CON.set_value(itr.guild, valuename, grouplist)
		
		embed = discord.Embed(title=f"Added '{suggestion}' to the `{group}` list!", color=discord.Color.brand_red())
		await itr.response.send_message(embed=embed)

	@AC.command(name="remove-suggestions", description="Remove objects from the lists for this server. (Make sure suggestion is exactly the same!)")
	async def remove_suggestions(self, itr:Itr, group:Literal["Names", "Games", "Enemies", "People", "Powerups"]="Enemies", suggestion:str=None):
		if not suggestion:
			await itr.response.send_message("The Suggestion field is required, try again!", ephemeral=True)

		valuename = "custom_" + group.lower()
		grouplist:list = self.client.CON.get_value(itr.guild, valuename)
		if suggestion in grouplist:
			grouplist.remove(suggestion)
		await self.client.CON.set_value(itr.guild, valuename, grouplist)

		embed = discord.Embed(title=f"Removed '{suggestion}' from the `{group}` list!", color=discord.Color.brand_red())
		await itr.response.send_message(embed=embed)

	@AC.command(name="list-suggestions", description="List objects from all the lists for this server.")
	async def list_suggestions(self, itr:Itr):
		page = 0
		pages = []
		pagesidx = {}
		values = self.client.CON.get_group(itr.guild)
		first = None
		for name in values:
			truename = self.client.CON.get_help(name)
			if name in values and len(values[name]) > 0:
				pages.append( discord.Embed(title=f"All custom `{truename}` in the list:", description="```\n- " + '\n- '.join(values[name]) + "```", color=discord.Color.brand_red()) )
				pagesidx[truename] = len(pages)-1
				if not first:
					first = truename

		if len(pages) == 0:
			return await itr.response.send_message("No custom suggestions added yet, try adding some with /add-suggestions!")

		def getView(group=None, timeout=False):
			view = discord.ui.View(timeout=None)

			options = []
			for name in values:
				truename = self.client.CON.get_help(name)
				if name in values and len(values[name]) > 0:
					if group == truename:
						options.append( discord.SelectOption(label=truename, default=True) )
					else:
						options.append( discord.SelectOption(label=truename) )

			view.add_item(discord.ui.Select(options=options, custom_id="select", disabled=timeout))
			return view
		
		await itr.response.send_message(embed=pages[page], view=getView(first))
		MSG = await itr.original_response()

		def check(checkitr:Itr):
			try:
				return (checkitr.message.id == MSG.id)
			except:
				return False
		while True:
			try:
				butitr:Itr = await self.client.wait_for("interaction", timeout=90, check=check)
				if butitr.user == itr.user:
					await butitr.response.defer()
					page = pagesidx[butitr.data["values"][0]]
					await itr.edit_original_response(embed=pages[page], view=getView(butitr.data["values"][0]))
				else:
					await butitr.response.send_message("Hmmmmm sussy.", ephemeral=True)
			except asyncio.TimeoutError:
				return await itr.edit_original_response(view=getView(True))

	###

	@AC.command(name="generate", description="Gaenerate some suggestions.")
	@AC.describe(mode="If the sugegstions returned will show big images (up to 4) or thumbnails (only 1)", logs="If older suggestions are saved to a thread.")
	async def generate(self, itr:Itr, mode:Literal["Simple", "Full"]="Simple", logs:Literal["Enabled", "Disabled"]="Enabled"):
		THREAD:discord.Thread|None = None
		page = 0
		pages = [self.createSuggestion(itr, mode)]

		def getView(timeout=False):
			first = (page == 0)
			view = discord.ui.View(timeout=None)
			view.add_item(discord.ui.Button(label="<-", style=discord.ButtonStyle.blurple, custom_id="left", disabled=(first or timeout)))
			view.add_item(discord.ui.Button(label=f"{page+1}/{len(pages)}", style=discord.ButtonStyle.gray, custom_id="display", disabled=True))
			view.add_item(discord.ui.Button(label="->", style=discord.ButtonStyle.blurple, custom_id="right", disabled=timeout))
			view.add_item(discord.ui.Button(label=f"-", style=discord.ButtonStyle.gray, custom_id="blank1", disabled=True, row=1))
			view.add_item(discord.ui.Button(label="x", style=discord.ButtonStyle.red, custom_id="close", disabled=timeout, row=1))
			view.add_item(discord.ui.Button(label=f"-", style=discord.ButtonStyle.gray, custom_id="blank2", disabled=True, row=1))
			return view
		
		await itr.response.send_message("```css\n[ KEEP IN MIND THIS IS IN BETA, SEVERAL IMAGES ARE MISSING AND PROMPTS ARE LIMITED ]\n```", embeds=pages[page], view=getView())
		MSG = await itr.original_response()

		def check(checkitr:Itr):
			try:
				return (checkitr.message.id == MSG.id)
			except:
				return False
		while True:
			try:
				butitr:Itr = await self.client.wait_for("interaction", timeout=90, check=check)
				if butitr.user == itr.user:
					await butitr.response.defer()
					if butitr.data["custom_id"] == "left":
						page -= 1
						if page < 0:
							page = len(pages)-1
							
					elif butitr.data["custom_id"] == "right":
						page += 1
						if page > len(pages)-1:
							pages.append(self.createSuggestion(itr, mode))
							if logs == "Enabled":
								if not THREAD:
									THREAD = await MSG.create_thread(name=f"Older Suggestions ({MSG.id})", auto_archive_duration=60)
								await THREAD.send(content=f"Page {page}:", embeds=pages[page-1])

					elif butitr.data["custom_id"] == "close":
						if logs == "Enabled":
							await THREAD.send(content=f"Page {len(pages)}:", embeds=pages[len(pages)-1])
						return await itr.edit_original_response(view=getView(True))

					await itr.edit_original_response(embeds=pages[page], view=getView())
				else:
					await butitr.response.send_message("Hmmmmm sussy.", ephemeral=True)
			except asyncio.TimeoutError:
				if logs == "Enabled" and THREAD:
					await THREAD.send(content=f"Page {len(pages)}:", embeds=pages[len(pages)-1])
				return await itr.edit_original_response(view=getView(True))

	def createSuggestion(self, itr:Itr, mode):
		values = self.client.CON.get_group(itr.guild)
		suggestion, images = createSuggestion(itr, values)
		if mode == "Simple":
			embed = discord.Embed(title="New suggestion fresh from the oven:", description=suggestion, color=discord.Color.brand_red())
			if len(images) > 0: embed.set_thumbnail(url=images[0])
			return [embed]
		elif mode == "Full":
			url = 'https://youtube.com/@Aid0n'
			embed1 = discord.Embed(title="New suggestion fresh from the oven:", description=suggestion, url=url, color=discord.Color.brand_red())
			if len(images) > 0: embed1.set_image(url=images[0])
			embed2 = discord.Embed(title="na", url=url)
			if len(images) > 1: embed2.set_image(url=images[1])
			embed3 = discord.Embed(title="na", url=url)
			if len(images) > 2: embed3.set_image(url=images[2])
			embed4 = discord.Embed(title="na", url=url)
			if len(images) > 3: embed4.set_image(url=images[3])
			return [embed1,embed2,embed3,embed4]

async def setup(client:SuggestBot):
	await client.add_cog(MainCog(client), guilds=client.debug_guilds)