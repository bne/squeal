# $Id$
#
# Copyright 2010 Doug Winter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" The web jukebox. """

__author__ = "Doug Winter <doug.winter@isotoma.com>"
__docformat__ = "restructuredtext en"
__version__ = "$Revision$"[11:-2]

from zope.interface import Interface, implements

from nevow import rend
from nevow import inevow
from nevow import loaders
from nevow import tags as T
from nevow import page
from nevow import athena
from nevow.flat import flatten
import urllib

import base

import ijukebox
from squeal import isqueal
from squeal.adaptivejson import simplify

from formlet import widget
from formlet import form
from formlet import field

from twisted.python import log

class Source(base.BaseElement):
    jsClass = u"Squeal.Source"
    docFactory = base.xmltemplate("source.html")

    @page.renderer
    def sources(self, request, tag):
        sources = [T.option(selected=True, value="")['-- None --']]
        for s in self.store.powerupsFor(isqueal.IMusicSource):
            sources.append(T.option(value=s.name)[s.label])
        return tag[
            sources
        ]

    @athena.expose
    def main_widget(self, source):
        for s in self.store.powerupsFor(isqueal.IMusicSource):
            if s.name == source:
                w = s.main_widget()
                w.setFragmentParent(self.page.runtime['main'])
                return w

class Account(base.BaseElement):
    jsClass = u"Squeal.Account"
    docFactory = base.xmltemplate("account.html")

    @page.renderer
    def credentials(self, request, tag):
        return tag['You are not logged in']

class Playing(base.BaseElement):
    jsClass = u"Squeal.Playing"
    docFactory = base.xmltemplate("playing.html")

    @athena.expose
    def goingLive(self):
        self.subscribe()

    def subscribe(self):
        self.evreactor.subscribe(self.queueChange, isqueal.IPlaylistChangeEvent)
        self.evreactor.subscribe(self.queueChange, isqueal.IMetadataChangeEvent)

    @property
    def playlist_service(self):
        for queue in self.store.powerupsFor(isqueal.IPlaylist):
            return queue

    def queueChange(self, ev):
        self.reload()

    def reload(self):
        self.callRemote("reload", unicode(flatten(self.playtag())))

    def playtag(self):
        current = self.playlist_service.get_current_track()
        if current is None:
            return "Nothing"
        elif not current.is_loaded:
            return "Loading..."
        else:
            return (
                T.img(src=current.image_uri(), width="100px"),
                T.br,
                "Now playing ",
                T.a(href="")[current.title],
                " by ",
                T.a(href="")[current.artist],
                " on ",
                T.a(href="")[current.album]
            )

    @page.renderer
    def playing(self, request, tag):
        return tag[self.playtag()]

class Queue(base.BaseElement):
    jsClass = u"Squeal.Queue"
    docFactory = base.xmltemplate("queue.html")

    @athena.expose
    def goingLive(self):
        self.subscribe()
        self.reload()

    def subscribe(self):
        self.evreactor.subscribe(self.queueChange, isqueal.IPlaylistChangeEvent)
        self.evreactor.subscribe(self.queueChange, isqueal.IMetadataChangeEvent)

    @property
    def playlist_service(self):
        for queue in self.store.powerupsFor(isqueal.IPlaylist):
            return queue

    def queueChange(self, ev):
        self.reload()

    @athena.expose
    def clear(self):
        log.msg("clear", system="squeal.web.jukebox.Queue")
        self.playlist_service.clear()
        self.reload()

    def reload(self):
        queue = self.playlist_service
        items = map(simplify, queue)
        self.callRemote("reload", {
            u'items': items,
            u'current': queue.current,
        })

    @athena.expose
    def queueTrack(self, namespace, tid):
        """ Called from other UI components, via the javascript partner class
        to this one. Allows queuing of any track if it's global tid is known.
        """
        log.msg("queueTrack called with %r, %r" % (namespace, tid), system="squeal.web.jukebox.Queue")
        queue = self.playlist_service
        for p in self.store.powerupsFor(isqueal.ITrackSource):
            if p.namespace == namespace:
                provider = p
                break
        else:
            raise KeyError("No track source uses the namespace %s" % namespace)
        track = provider.get_track(tid)
        queue.enqueue(track)

class Main(base.BaseElement):
    jsClass = u"Squeal.Main"
    docFactory = base.xmltemplate("main.html")

class PluginInstaller(base.BaseElement):
    jsClass = u"Squeal.PluginInstaller"
    docFactory = base.xmltemplate("plugin_installer.html")

    def __init__(self, original):
        super(PluginInstaller, self).__init__()
        self.original = original

    @property
    def plugin_manager(self):
        for s in self.store.powerupsFor(isqueal.IPluginManager):
            return s

    @page.renderer
    def name(self, request, tag):
        return tag[self.original['plugin'].name]

    @page.renderer
    def description(self, request, tag):
        return tag[self.original['plugin'].description]

    @page.renderer
    def configform(self, request, tag):
        setup_form = self.original['plugin'].setup_form
        return tag[setup_form.element(self)]

    @athena.expose
    def install(self, **kw):
        pm = self.plugin_manager
        s = pm.install(args=kw, **self.original)
        s.setServiceParent(self.plugin_manager.parent)

class Setup(base.BaseElement):
    jsClass = u"Squeal.Setup"
    docFactory = base.xmltemplate("setup.html")

    @property
    def plugin_manager(self):
        for s in self.store.powerupsFor(isqueal.IPluginManager):
            return s

    @page.renderer
    def install(self, request, tag):
        def installer(i):
            p = PluginInstaller(i)
            p.setFragmentParent(self)
            return p
        return tag[(installer(i) for i in self.plugin_manager.installable)]

class Connected(base.BaseElement):
    jsClass = u"Squeal.Connected"
    docFactory = base.xmltemplate("connected.html")

    def subscribe(self):
        log.msg("Subscribing", system="squeal.web.jukebox.Connected")
        self.evreactor.subscribe(self.playerChange, isqueal.IPlayerStateChange)

    def playerChange(self, ev):
        log.msg("Reloading players", system="squeal.web.jukebox.Connected")
        self.callRemote("reload", unicode(flatten(self.player_content())))

    @page.renderer
    def users(self, request, tag):
        return tag['USERS']

    def player_content(self):
        for p in self.store.powerupsFor(isqueal.ISlimPlayerService):
            slimservice = p
            break
        else:
            raise("Unable to show the connected list with no SlimService running")
        players = []
        for p in slimservice.players:
            players.append(T.li["%s (%s)" % (p.mac_address, p.device_type)])
        if players:
            return T.h2["Players"], T.ul[players]
        else:
            return T.h2["Players"], "No players connected!"

    @page.renderer
    def players(self, request, tag):
        return tag[self.player_content()]

class Jukebox(base.BasePageContainer):

    docFactory = base.xmltemplate("jukebox.html")

    contained = {
        'source': Source,
        'account': Account,
        'main': Main,
        'playing': Playing,
        'queue': Queue,
        'connected': Connected,
        'setup': Setup,
    }

    def __init__(self, service):
        super(Jukebox, self).__init__()
        self.service = service