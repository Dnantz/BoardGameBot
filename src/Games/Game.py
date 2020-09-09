from abc import ABC, abstractmethod
# Base game class


class Game(ABC):

    requiredPlayers: int
    description: str

    @abstractmethod
    async def setup(self, *args):
        pass

    @abstractmethod
    async def play(self, ctx, bot, *args):
        pass
