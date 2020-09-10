from src.Games.Game import Game
import numpy as np
import discord
from discord.ext.commands import Context
from asyncio import TimeoutError
import re


def create():
    return Gomoku()


class Gomoku(Game):

    description = "Line up 5 in a row to win."

    BLANK_SQUARE = "🟫"
    WHITE_PIECE = "⚪"
    BLACK_PIECE = "⚫"

    requiredPlayers = 2
    players = []
    playerNames = []
    turn = False  # use bool as 0 and 1

    gameboard = np.array(0)
    header: str
    message: discord.Message

    async def setup(self, ctx: Context, *args):
        if not ctx.message.mentions[0]:
            await ctx.channel.send("Not enough players! you need 2 players for this game.")
            raise IndexError()

        self.message = await ctx.channel.send("Setting up game...")
        # TODO: shuffle who goes first
        p1 = ctx.author.nick if ctx.author.nick else ctx.author.name
        p2 = ctx.message.mentions[0].nick if ctx.message.mentions[0].nick else ctx.message.mentions[0].name
        self.playerNames = [p1, p2]
        self.players = [ctx.author, ctx.message.mentions[0]]

        self.header = "{0}{1} | {2}{3}".format(
            self.WHITE_PIECE, self.playerNames[0], self.playerNames[1], self.BLACK_PIECE
        )

        # region board setup
        # set a blank board
        self.gameboard = np.full((14, 14), self.BLANK_SQUARE, dtype=object)

        self.gameboard[0, 0] = ":o2:"
        # number edges
        self.gameboard[0, 1] = ":one:"
        self.gameboard[0, 2] = ":two:"
        self.gameboard[0, 3] = ":three:"
        self.gameboard[0, 4] = ":four:"
        self.gameboard[0, 5] = ":five:"
        self.gameboard[0, 6] = ":six:"
        self.gameboard[0, 7] = ":seven:"
        self.gameboard[0, 8] = ":eight:"
        self.gameboard[0, 9] = ":nine:"
        self.gameboard[0, 10] = ":keycap_ten:"
        self.gameboard[0, 11] = ":one:"
        self.gameboard[0, 12] = ":two:"
        self.gameboard[0, 13] = ":three:"

        self.gameboard[1, 0] = ":regional_indicator_a:"
        self.gameboard[2, 0] = ":regional_indicator_b:"
        self.gameboard[3, 0] = ":regional_indicator_c:"
        self.gameboard[4, 0] = ":regional_indicator_d:"
        self.gameboard[5, 0] = ":regional_indicator_e:"
        self.gameboard[6, 0] = ":regional_indicator_f:"
        self.gameboard[7, 0] = ":regional_indicator_g:"
        self.gameboard[8, 0] = ":regional_indicator_h:"
        self.gameboard[9, 0] = ":regional_indicator_i:"
        self.gameboard[10, 0] = ":regional_indicator_j:"
        self.gameboard[11, 0] = ":regional_indicator_k:"
        self.gameboard[12, 0] = ":regional_indicator_l:"
        self.gameboard[13, 0] = ":regional_indicator_m:"

        # starting center piece
        self.gameboard[7, 7] = self.BLACK_PIECE

        # endregion

    async def draw_board(self):
        # p1 vs p2 message
        display = self.header + "\n"
        # the board
        for i in range(self.gameboard.shape[0]):
            for j in range(self.gameboard.shape[1]):
                display += self.gameboard[j, i]
            display += "\n"
        # whose turn is it anyway
        display += "{0}'s turn".format(self.playerNames[int(self.turn)])
        # print(display)
        # print(len(display))
        await self.message.edit(content=display)

    def move_check(self, m: discord.Message):
        valid = (
            m.channel == self.message.channel
            and m.author == self.players[int(self.turn)]
            and (re.match("([a-m])([1-9]|1[0-5])", m.content.lower()))
        )
        return valid

    def get_neighbors(self, coords):
        neighbors = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (i == 0 and j == 0) or coords[0]+i < 1 or coords[1]+j < 1:
                    continue
                try:
                    if self.gameboard[coords[0]+i, coords[1]+j] != self.BLANK_SQUARE:
                        neighbors.append([coords[0]+i, coords[1]+j])
                except IndexError:
                    pass
        return neighbors

    def get_moves(self):
        coords = []
        for i in range(1, self.gameboard.shape[0]):
            for j in range(1, self.gameboard.shape[1]):
                if self.gameboard[i, j] == self.WHITE_PIECE or self.gameboard[i, j] == self.BLACK_PIECE:
                    continue  # there is a piece here, can't put another piece
                else:
                    if self.get_neighbors([i, j]):  # this space is empty with at least 1 piece nearby
                        coords.append([i, j])
        return coords

    def check_for_winner(self):
        for i in range(1, self.gameboard.shape[0]):
            for j in range(1, self.gameboard.shape[1]):
                # if there is a piece at this location
                if self.gameboard[i, j] == self.WHITE_PIECE or self.gameboard[i, j] == self.BLACK_PIECE:
                    piece = self.gameboard[i, j]  # the type of piece to check for
                    # check neighbors for matching pieces
                    for neighbor in self.get_neighbors([i, j]):
                        if self.gameboard[neighbor[0], neighbor[1]] == piece:
                            # are there 4 more pieces in this direction
                            direction = np.array(neighbor) - np.array([i, j])
                            count = 0
                            for k in range(1, 5):
                                if self.gameboard[i + direction[0] * k, j + direction[1] * k] == piece:
                                    count += 1
                                else:
                                    break
                                if count > 3:
                                    return True
        return False

    async def play(self, ctx, bot, *args):
        try:
            await self.setup(ctx, args)
        except IndexError:
            return
        game_won = False

        while not game_won:
            await self.draw_board()
            # get move from user
            valid_move = False
            while not valid_move:
                try:
                    msg = await bot.wait_for('message', timeout=300, check=self.move_check)
                except TimeoutError:
                    ctx.channel.send("{0} took too long to make a move, {1} wins by default.").format(
                        self.playerNames[self.turn], self.playerNames[not self.turn])
                    break
                # ord converts letter to ascii, a=97, b=98, ...
                coords = [int(ord(msg.content[0])-96), int(msg.content[1:])]
                good_moves = self.get_moves()
                if coords in good_moves:
                    valid_move = True
                else:
                    bad_move_msg = await ctx.channel.send("You can't place a piece at " + msg.content + " currently.")
                    await bad_move_msg.delete(delay=5)
                await msg.delete()
            piece = self.BLACK_PIECE if self.turn else self.WHITE_PIECE
            self.gameboard[coords[0], coords[1]] = piece
            game_won = self.check_for_winner()
            self.turn = not self.turn

        # draw final board and declare winner
        display = self.header + "\n"
        # the board
        for i in range(self.gameboard.shape[0]):
            for j in range(self.gameboard.shape[1]):
                display += self.gameboard[j, i]
            display += "\n"
        display += "{0} Wins!".format(self.playerNames[not self.turn])
        await self.message.edit(content=display)
