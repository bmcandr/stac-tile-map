from api.main import app
from magnum import Magnum


handler = Magnum(app, lifespan="off")
