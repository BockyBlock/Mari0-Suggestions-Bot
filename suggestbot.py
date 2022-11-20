import discord
from discord.ext import commands

import os
from config import ConfigManager

class SuggestBot(commands.Bot):
	def __setitem__(self, key, value):
		setattr(self, key, value)
	def __getitem__(self, key):
		return getattr(self, key)

	def __init__(self, debug_guilds, offline=False):
		self.offline = offline
		if debug_guilds:
			self.debug_guilds = debug_guilds
		else:
			self.debug_guilds = []
		super().__init__(command_prefix="sb!", intents=discord.Intents.all())

	async def setup_hook(self):
		if not self.offline:
			self.CON = ConfigManager(self, "guild")

			for filename in os.listdir('./cogs'):
				if filename.endswith('.py'):
					await self.load_extension(f'cogs.{filename[:-3]}')

		if len(self.debug_guilds) > 0:
			for guild in self.debug_guilds:
				await self.tree.sync(guild=guild)
		else:
			await self.tree.sync()
			
	async def on_ready(self):
		print(f"Hello World!")
		await self.CON.ready()