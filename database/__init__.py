from .database import Database as DB
from .assassins import Assassins

class Database(DB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.assassins = Assassins(self)