import os
from decimal import Decimal

import discord
from discord.ext import commands
from discord.utils import get

import sizebot.digilogger as logger
from sizebot.globalsb import folder, readhexcode, regenhexcode
from sizebot.globalsb import isFeetAndInchesAndIfSoFixIt, getlet, getnum, toSV, toWV
from sizebot.globalsb import sizebotuser_roleid
from sizebot.globalsb import nickupdate


# Add newlines and join into one string
def lines(items):
    return "".join(item + "\n" for item in items)


async def addUserRole(member):
    role = get(member.guild.roles, id=sizebotuser_roleid)
    if role is None:
        logger.warn(f"Sizebot user role {sizebotuser_roleid} not found in guild {member.guild.id}")
        return
    await member.add_roles(role, reason="Registered as sizebot user")


async def removeUserRole(member):
    role = get(member.guild.roles, id=sizebotuser_roleid)
    if role is None:
        logger.warn(f"Sizebot user role {sizebotuser_roleid} not found in guild {member.guild.id}")
        return
    await member.remove_roles(role, reason="Unregistered as sizebot user")


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx, nick: str, display: str, currentheight: str, baseheight: str, baseweight: str, units: str, species: str = None):
        # Registers a user for SizeBot.

        # Fix feet and inches.
        currentheight = isFeetAndInchesAndIfSoFixIt(currentheight)
        baseheight = isFeetAndInchesAndIfSoFixIt(baseheight)

        # Extract values and units.
        chu = getlet(currentheight)
        bhu = getlet(baseheight)
        bwu = getlet(baseweight)
        currentheight = getnum(currentheight)
        baseheight = getnum(baseheight)
        baseweight = getnum(baseweight)

        # Convert floats to decimals.
        currentheight = Decimal(currentheight)
        baseheight = Decimal(baseheight)
        baseweight = Decimal(baseweight)

        readable = "CH {0}, CHU {1}, BH {2}, BHU {3}, BW {4}, BWU {5}".format(currentheight, chu, baseheight, bhu, baseweight, bwu)
        logger.warn("New user attempt! Nickname: {0}, Display: {1}".format(nick, display))
        print(readable)

        # Already registered.
        if os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            await ctx.send("""Sorry! You already registered with SizeBot.
    To unregister, use the `&unregister` command.""", delete_after=10)
            logger.warn("User already registered on user registration: {1}.".format(ctx.message.author))
            return

        # Invalid size value.
        if (currentheight <= 0 or
                baseheight <= 0 or
                baseweight <= 0):
            logger.warn("Invalid size value.")
            await ctx.send("All values must be an integer greater than zero.", delete_after=5)
            return

        # Invalid display value.
        if display.lower() not in ["y", "n"]:
            logger.warn("display was {0}, must be Y or N.".format(display))
            return

        # Invalid unit value.
        if units.lower() not in ["m", "u"]:
            logger.warn("units was {0}, must be M or U.".format(units))
            await ctx.send("Units must be `M` or `U`.", delete_after=5)
            return

        # Success.
        if species is None:
            species = "None"

        # Make an array of string items, one per line.
        output = lines([
            f"{nick}",
            f"{display}",
            f"{toSV(currentheight, chu)}",
            f"{toSV(baseheight, bhu)}",
            f"{toWV(baseweight, bwu)}",
            "1.0",
            f"{units}",
            f"{species}"
        ])

        with open(folder + '/users/' + str(ctx.message.author.id) + '.txt', "w") as userfile:
            try:
                userfile.write(output)
            except UnicodeDecodeError():
                logger.warn("Unicode in nick or species.")
                await ctx.send("<@{0}> Unicode error! Please don't put Unicode characters in your nick or species.".format(ctx.message.author.id))
                return

        await addUserRole(ctx.message.author)

        logger.warn("Made a new user: {0}!".format(ctx.message.author))
        print(output)
        await ctx.send("Registered <@{0}>. {1}.".format(ctx.message.author.id, readable), delete_after=5)

    @register.error
    async def register_handler(self, ctx, error):
        # Check if required argument is missing.
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("""Not enough variables for `register`.
    Use `&register [nick] [display (Y/N)] [currentheight] [baseheight] [baseweight] [M/U]`.""", delete_after=30)

    @commands.command()
    async def unregister(self, ctx, code=None):
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
            logger.warn("User {0} not registered with SizeBot, but tried to unregister anyway.".format(ctx.message.author.id))
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
            return

        if code is None:
            regenhexcode()
            await ctx.send("""To unregister, use the `&unregister` command and the following code.
    `{0}`""".format(readhexcode()), delete_after=30)
            return

        if code != readhexcode():
            logger.warn("User {0} tried to unregister, but said the wrong hexcode.".format(ctx.message.author.id))
            await ctx.send("Incorrect code. You said: `{0}`. The correct code was: `{1}`. Try again.".format(code, readhexcode()), delete_after=10)
            return

        logger.warn("User {0} successfully unregistered.".format(ctx.message.author.id))
        await ctx.send("Correct code! Unregistered {0}".format(ctx.message.author.name), delete_after=5)
        os.remove(folder + "/users/" + str(ctx.message.author.id) + ".txt")

        await removeUserRole(ctx.message.author)

    @commands.Cog.listener()
    async def on_message(self, m):
        await nickupdate(m.author)


# Necessary.
def setup(bot):
    bot.add_cog(RegisterCog(bot))
