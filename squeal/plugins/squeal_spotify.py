
from zope.interface import classProvides
from squeal.isqueal import ISquealPlugin

from squeal.spot.service import Spotify

class SpotifyPlugin(object):
    classProvides(ISquealPlugin)

    version = '0.0.0'

    def __init__(self):
        pass

    def install(self, config, store):
        s = Spotify(config, store=store)
        for iface in s.powerupInterfaces:
            store.powerUp(s, iface)
        store.powerUp(s, IService)
