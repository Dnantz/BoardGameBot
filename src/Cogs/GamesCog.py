from discord.ext import commands
from discord.ext.commands import Context
import src.Games.Game
import src.Games


class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx: Context, game: str = None, *args):
        if game:
            try:
                game = game.lower().capitalize()
                game = src.Games.gamelist[game]
                g = game.create()

                await g.play(ctx, self.bot, *args)
            except KeyError:
                await ctx.channel.send("Game not recognized!")
        else:
            await ctx.channel.send("You need to specify what you want to play!")