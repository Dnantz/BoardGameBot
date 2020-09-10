from src.Games.Game import Game
import numpy as np
import discord
from discord.ext.commands import Context
from asyncio import TimeoutError
import re
import random


def create():
    return Gomoku()


class Gomoku(Game):
    description = "Line up 5 in a row to win."

    BLANK_SQUARE = "🟫"
    WHITE_PIECE = "⚪"
    BLACK_PIECE = "⚫"

    requiredPlayers = 1
    players = []
    playerNames = []
    turn = False  # use bool as 0 and 1

    should_do_ai_move: bool

    gameboard = np.array(0)
    header: str
    message: discord.Message

    async def setup(self, ctx: Context, *args):
        try:
            p2 = ctx.message.mentions[0].nick if ctx.message.mentions[0].nick else ctx.message.mentions[0].name
            self.players = [ctx.author, ctx.message.mentions[0]]
            self.should_do_ai_move = False
        except IndexError:
            await ctx.channel.send("So you wish to challenge me...")
            p2 = ctx.me.nick if ctx.me.nick else ctx.me.name
            self.players = [ctx.author, ctx.me]
            self.should_do_ai_move = True
        self.message = await ctx.channel.send("Setting up game...")
        p1 = ctx.author.nick if ctx.author.nick else ctx.author.name
        self.playerNames = [p1, p2]

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
        await self.message.edit(content=display)

    def move_check(self, m: discord.Message):
        valid = (
                m.channel == self.message.channel
                and m.author == self.players[int(self.turn)]
                and (re.match("([a-m])([1-9]|1[0-5])", m.content.lower()))
        )
        return valid

    # region AI
    def get_neighbors(self, coords):
        neighbors = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (
                        (i == 0 and j == 0) or
                        coords[0] + i < 1 or coords[1] + j < 1
                        or coords[0] + i > 13 or coords[1] + j > 13
                ):
                    continue
                if self.gameboard[coords[0] + i, coords[1] + j] != self.BLANK_SQUARE:
                    neighbors.append([coords[0] + i, coords[1] + j])
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
                            count = 2
                            # row of 2 so far
                            # are there 3 more pieces in this direction
                            direction = np.array(neighbor) - np.array([i, j])
                            for k in range(2, 5):
                                if (
                                        i + direction[0] * k > 13 or j + direction[1] * k > 13
                                        or i + direction[0] * k < 1 or j + direction[1] * k < 1
                                ):
                                    break
                                if self.gameboard[i + direction[0] * k, j + direction[1] * k] == piece:
                                    count += 1
                                else:
                                    break
                            if count == 5:
                                # print("win found from {0} in direction {1}".format([i, j], direction))
                                return True
        return False

    def evaluate_move(self, pos, color):
        enemy_color: str
        if color:
            color = self.BLACK_PIECE
            enemy_color = self.WHITE_PIECE
        else:
            color = self.WHITE_PIECE
            enemy_color = self.BLACK_PIECE
        value = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                count = 0
                if (i == 0 and j == 0) or pos[0] + i < 1 or pos[1] + j < 1 or pos[0] + i > 13 or pos[1] + j > 13:
                    continue
                if self.gameboard[pos[0] + i, pos[1] + j] == self.BLANK_SQUARE:
                    continue  # nothing in this direction
                elif self.gameboard[pos[0] + i, pos[1] + j] == color:
                    # this is our own piece
                    direction = np.array([pos[0] + i, pos[1] + j]) - np.array(pos)
                    for k in range(1, 5):
                        if (
                                pos[0] + direction[0] * k > 13 or pos[1] + direction[1] * k > 13
                                or pos[0] + direction[0] * k < 1 or pos[1] + direction[1] * k < 1
                        ):
                            break
                        if self.gameboard[pos[0] + direction[0] * k, pos[1] + direction[1] * k] == color:
                            count += 1
                        else:
                            break
                    value += pow(10, count)
                    if count == 4:
                        # this will be the winning move
                        value += 9000
                else:
                    # this is the opponent's piece
                    direction = np.array([pos[0] + i, pos[1] + j]) - np.array(pos)
                    for k in range(1, 5):
                        if (
                                pos[0] + direction[0] * k > 13 or pos[1] + direction[1] * k > 13
                                or pos[0] + direction[0] * k < 1 or pos[1] + direction[1] * k < 1
                        ):
                            break
                        if self.gameboard[pos[0] + direction[0] * k, pos[1] + direction[1] * k] == enemy_color:
                            count += 1
                        else:
                            break
                    value += 2 * pow(10, count) if count > 1 else 0
                    # puts more weight on blocking other moves, if 2+ pieces stacked
        return value

    def do_ai_move(self, color=True):
        best_move = None  # [coords, value]
        possible_moves = self.get_moves()
        for move in possible_moves:
            value = self.evaluate_move(move, color)
            # print("Value of move at " + str(move) + ": " + str(value))
            if not best_move:
                # assign first move evaluated to best move
                best_move = [move, value]
            else:
                if value > best_move[1]:
                    best_move = [move, value]
                elif value == best_move[1]:
                    # RNG!
                    if random.choice([0, 1]):
                        best_move = [move, value]
        final_move = best_move[0]
        # print("Placing piece at" + str(final_move))
        self.gameboard[final_move[0], final_move[1]] = self.BLACK_PIECE if color else self.WHITE_PIECE

    async def bot_game(self, ctx: Context):
        # setup
        self.message = await ctx.channel.send("Simulating game...")
        async with ctx.channel.typing():

            self.playerNames = ["White", "Black"]
            self.header = "AI game"

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

            # game
            game_won = False
            while not game_won and self.get_moves():
                self.do_ai_move(self.turn)
                game_won = self.check_for_winner()
                self.turn = not self.turn

        # draw final board and declare winner
        display = self.header + "\n"
        # the board
        for i in range(self.gameboard.shape[0]):
            for j in range(self.gameboard.shape[1]):
                display += self.gameboard[j, i]
            display += "\n"
        if self.check_for_winner():
            display += "{0} Wins!".format(self.playerNames[not self.turn])
        else:
            # ran out of moves
            display += "The game was a draw."
        await self.message.edit(content=display)

    # endregion

    async def play(self, ctx, bot, *args):
        await self.setup(ctx, args)
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
                coords = [int(ord(msg.content[0]) - 96), int(msg.content[1:])]
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
            if self.should_do_ai_move and not game_won:
                self.do_ai_move()
            else:
                self.turn = not self.turn

        # draw final board and declare winner
        display = self.header + "\n"
        # the board
        for i in range(self.gameboard.shape[0]):
            for j in range(self.gameboard.shape[1]):
                display += self.gameboard[j, i]
            display += "\n"
        if self.check_for_winner():
            display += "{0} Wins!".format(self.playerNames[not self.turn])
        else:
            # ran out of moves
            display += "The game was a draw."
        await self.message.edit(content=display)
