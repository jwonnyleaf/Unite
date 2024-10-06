from .database import Database as DB
from .assassins import Assassins
from .guilds import Guilds


class Database(DB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.assassins = Assassins(self)
        self.guilds = Guilds(self)
