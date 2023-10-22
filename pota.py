import requests
import json
import enum 

SPOT_URL="https://api.pota.app/spot/"

class Mode(enum.Enum):
    SSB = "SSB"
    CW = "CW"
    # FT*, FM not supported

class Band(enum.Enum):
    """
    Frequency ranges for the bands. HF only, and I'm not trying to do band plans - the point is just to filter
    """
    METERS_160 = (1800, 2000)
    METERS_80 = (3500, 4000)
    METERS_40 = (7000, 7300)
    METERS_30 = (10100, 10150)
    METERS_20 = (14000, 14350)
    METERS_17 = (18068, 18168)
    METERS_15 = (21000, 21450)
    METERS_12 = (24890, 24990)
    METERS_10 = (28000, 29700)


class PotaSpotController():
    
    def __init__(self) -> None:
        self.spots = []
    
    def refresh(self):
        resp = requests.get(SPOT_URL)
        self.spots = json.loads(resp.content)

    def getSpots(self, mode=None, band=None):
        """
        Gets a filtered list of spots. Valid modes
        """
        # Yes, I probably got too clever here, but I'm already 90% of the way down the hole
        mode_filter = (lambda x : True) if mode is None else (
                lambda x : x['mode'] == mode.value)
        band_filter = (lambda x : True) if band is None else (
                lambda x : float(x['frequency']) >= band.value[0] and float(x['frequency']) <= band.value[1])
        
        return list(filter(lambda x: mode_filter(x) and band_filter(x), self.spots))