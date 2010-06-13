#!/usr/bin/env python
#
#   Python module for parsing HTML files produced by CompCheck
#   Copyright (C) 2010  Tom Payne
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


from datetime import datetime
from operator import attrgetter
import os.path
import re

from BeautifulSoup import BeautifulSoup


class Task(object):

    def __init__(self, task, date, gps_distance):
        self.task = task
        self.date = date
        self.gps_distance = gps_distance

    @classmethod
    def parse(self, soup):
        indexes = {}
        for tr in soup.table.table.findAll('tr'):
            if indexes:
                tds = tr.findAll('td')
                if len(tds) == len(indexes):
                    task = tds[indexes['Task']].contents[0]
                    date = datetime.strptime(tds[indexes['Date']].contents[0], '%a %d-%b-%y').date()
                    gps_distance = float(re.match(r'(\d+\.\d+)\s+km', tds[indexes['GPS Dist']].contents[0]).group(1))
                    yield self(task, date, gps_distance)
                else:
                    break
            else:
                ths = tr.findAll('th')
                if ths and ths[0].contents[0] == 'Task':
                    indexes = dict((th.contents[0], i) for i, th in enumerate(ths))


class Pilot(object):

    def __init__(self, rank, id, name, nation, glider, sponsor, scores, score):
        self.rank = rank
        self.id = id
        self.name = name
        self.nation = nation
        self.glider = glider
        self.sponsor = sponsor
        self.scores = scores
        self.score = score
        self.tags = set()

    @classmethod
    def parse(self, soup):
        indexes, tasks = {}, []
        for tr in soup.table.findAll('tr'):
            if indexes:
                tds = tr.findAll('td')
                if len(tds) == len(indexes):
                    rank = int(tds[indexes['Rank']].contents[0])
                    id = int(tds[indexes['ID']].contents[0])
                    name = tds[indexes['Name']].contents[0]
                    nation = tds[indexes['Nation']].contents[0]
                    glider = tds[indexes['Glider']].contents[0]
                    try:
                        sponsor = tds[indexes['Sponsor']].contents[0]
                    except IndexError:
                        sponsor = ''
                    scores = [int(tds[indexes[k]].contents[0]) for k in tasks]
                    score = int(tds[indexes['Score']].contents[0])
                    yield self(rank, id, name, nation, glider, sponsor, scores, score)
                else:
                    break
            else:
                ths = tr.findAll('th')
                if ths and ths[0].contents[0] == 'Rank':
                    indexes = dict((th.contents[0], i) for i, th in enumerate(ths))
                    tasks = sorted(k for k in indexes.keys() if re.match(r'T\d+\Z', k))


class Competition(object):

    def __init__(self, title, location, tasks, pilots):
        self.title = title
        self.location = location
        self.tasks = tasks
        self.pilots = pilots

    @classmethod
    def load(self, basename, dirname):
        soup = BeautifulSoup(open(os.path.join(dirname, '%s (Open-Open).htm' % basename)))
        title = soup.h1.contents[0]
        location = soup.h2.contents[0]
        tasks = list(Task.parse(soup))
        pilots = dict((pilot.id, pilot) for pilot in Pilot.parse(soup))
        for tag in ('champs', 'serial', 'sports', 'women'):
            for pilot in Pilot.parse(BeautifulSoup(open(os.path.join(dirname, '%s (Open-%s).htm' % (basename, tag.capitalize()))))):
                pilots[pilot.id].tags.add(tag)
        return self(title, location, tasks, pilots)


if __name__ == '__main__':
    c = Competition.load('Kobarid', 'Kobarid')
    if True:
        for t in c.tasks:
            print t.__dict__
    if True:
        ps = list(pilot for pilot in c.pilots.values() if 'champs' in pilot.tags)
        for p in ps:
            p.score = sum(sorted(p.scores)[1:])
        for i, p in enumerate(sorted(ps, key=attrgetter('score'), reverse=True)):
            print i, p.name, p.score
