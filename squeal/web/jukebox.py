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

import wingdbstub

from zope.interface import Interface, implements

from nevow import rend
from nevow import inevow
from nevow import loaders
from nevow import tags as T
from nevow import page
from nevow import athena

import base

import ijukebox
from squeal import isqueal
from squeal.adaptivejson import simplify

from spotify import Link

class BaseContainer(object):

    """ Provides a simple method of providing default fragment instantiation """

    contained = {}

    def _contained_render(self, name):
        def _(ctx, data):
            elem = self.contained[name]()
            elem.setFragmentParent(self)
            return ctx.tag[elem]
        return _

    def renderer(self, ctx, name):
        if name in self.contained:
            return self._contained_render(name)
        return super(BaseContainer, self).renderer(ctx, name)

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

class Search(base.BaseElement):
    jsClass = u"Squeal.Search"
    docFactory = base.xmltemplate("search.html")

class Account(base.BaseElement):
    jsClass = u"Squeal.Account"
    docFactory = base.xmltemplate("account.html")

    @page.renderer
    def credentials(self, request, tag):
        return tag['You are not logged in']

class SearchEvent(object):
    def __init__(self, query):
        self.query = query

class Options(base.BaseElement):
    jsClass = u"Squeal.Options"
    docFactory = base.xmltemplate("options.html")


class Playing(base.BaseElement):
    jsClass = u"Squeal.Playing"
    docFactory = base.xmltemplate("playing.html")

class Queue(base.BaseElement):
    jsClass = u"Squeal.Queue"
    docFactory = base.xmltemplate("queue.html")

    @athena.expose
    def goingLive(self):
        self.subscribe()
        self.reload()

    def reload(self):
        for queue in self.store.powerupsFor(isqueal.IPlaylist): pass
        items = list(queue)
        print ">>>>>>>>>>>>", items
        items = map(simplify, items)
        print ">>>>>>>>>>>>", items
        self.callRemote("reload", items)

    @athena.expose
    def queueTrack(self, tid):
        """ Called from other UI components, via the javascript partner class
        to this one. Allows queuing of any track if it's global tid is known.
        """
        namespace = tid.split(":")[0]
        for queue in self.store.powerupsFor(isqueal.IPlaylist):
            pass # one and only one queue is assumed
        for p in self.store.powerupsFor(isqueal.ITrackSource):
            if p.namespace == namespace:
                provider = p
                break
        else:
            raise KeyError("No track source uses the namespace %s" % namespace)
        queue.enqueue(provider, tid)

class Main(base.BaseElement):
    jsClass = u"Squeal.Main"
    docFactory = base.xmltemplate("main.html")

class Connected(base.BaseElement):
    jsClass = u"Squeal.Connected"
    docFactory = base.xmltemplate("connected.html")

    @page.renderer
    def users(self, request, tag):
        return tag['USERS']

    @page.renderer
    def players(self, request, tag):
        return tag['PLAYERS']

class Jukebox(BaseContainer, athena.LivePage):

    docFactory = base.xmltemplate("jukebox.html")

    contained = {
        'source': Source,
        'account': Account,
        'search': Search,
        'options': Options,
        'main': Main,
        'playing': Playing,
        'queue': Queue,
        'connected': Connected,
    }

    def __init__(self, service):
        super(Jukebox, self).__init__()
        self.service = service
