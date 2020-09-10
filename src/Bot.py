from discord.ext import commands
from src.Cogs.GamesCog import GamesCog


bot = commands.Bot(command_prefix='!', case_insensitive=False)


@bot.event
async def on_ready():
    # import cogs
    # TODO: do this dynamically
    bot.add_cog(GamesCog(bot))
    print('Logged on as {0}!'.format(bot.user))

    # print a list of connected servers
    print("Connected servers:")
    for g in bot.guilds:
        print(g.name)


@bot.event
async def on_command_error(ctx, e):
    if e == commands.CommandNotFound:
        pass
    else:
        raise e
bot.run(open("key").read())
