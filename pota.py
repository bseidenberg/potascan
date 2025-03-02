"""
This file is part of POTAScan

Copyright (C) 2023-2024 Benjamin Seidenberg

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
import json
import enum

SPOT_URL="https://api.pota.app/spot/"

# TODO FIXME: All this radio stuff needs to get moved out
class Mode(enum.Enum):
    SSB = "SSB"
    CW = "CW"
    # FT*, FM not supported

class Band(enum.Enum):
    """
    Frequency ranges for the bands. HF only, and I'm not trying to do band plans - the point is just to filter
    Also, yes, I know, these are just US limits.
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
        raw_spots = json.loads(resp.content)
        # DEBUG MODE (Uncomment)
        #raw_spots = json.loads(open("spots.json",'r').read())

        # POTA includes more than one spot per call, if someone keeps getting spotted
        # Just like the website, we only want the most recent.
        #
        # Note: If there is a call active in multiple parks (like a club call), we'll only
        # see one. I'm OK with this - it means if there's a bad spot, it won't persist.
        # Simillarly, if someone is on multiple frequencies, we'll also only show one.
        # Again I'm OK with this - trying to show both will be bad if someone QSY's.
        #
        # The logic for this looks just like a phone interview question, I know.

        # ASSUMPTION: Spot ID is a monotonically incrementing ID
        raw_spots = sorted(raw_spots, key=lambda spot: spot["spotId"])
        calls = set()
        deduped_spots = []
        for spot in raw_spots:
            if not spot["activator"] in calls:
                deduped_spots.append(spot)
                calls.add(spot["activator"])
        self.spots = deduped_spots


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
