# agent.py
import asyncio
import concurrent
import discord
import matplotlib.pyplot as plt
import numpy as np
import string
import os
import psycopg2
import psycopg2.extras
from core import utils, DCSServerBot, Plugin, PluginRequiredError
from contextlib import closing, suppress
from datetime import timedelta
from discord.ext import commands
from matplotlib.patches import ConnectionPatch
from matplotlib.ticker import FuncFormatter
from typing import Optional, Union
from .listener import UserStatisticsEventListener


class AgentUserStatistics(Plugin):
    pass


class MasterUserStatistics(AgentUserStatistics):

    WEEKDAYS = {
        0: 'Mon',
        1: 'Tue',
        2: 'Wed',
        3: 'Thu',
        4: 'Fri',
        5: 'Sat',
        6: 'Sun'
    }

    def __init__(self, bot, listener):
        super().__init__(bot, listener)
        plt.switch_backend('agg')
        # Make sure we only get back floats, not Decimal
        dec2float = psycopg2.extensions.new_type(
            psycopg2.extensions.DECIMAL.values,
            'DEC2FLOAT',
            lambda value, curs: float(value) if value is not None else None)
        psycopg2.extensions.register_type(dec2float)
        self.servers = []
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute('SELECT DISTINCT server_name FROM missions')
                for row in cursor.fetchall():
                    self.servers.append(row[0])
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    @commands.command(description='Links a member to a DCS user', usage='<member> <ucid>')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def link(self, ctx, member: discord.Member, ucid):
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute('UPDATE players SET discord_id = %s WHERE ucid = %s', (member.id, ucid))
                conn.commit()
                await ctx.send('Member {} linked to ucid {}'.format(member.display_name, ucid))
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
            conn.rollback()
        finally:
            self.pool.putconn(conn)

    @commands.command(description='Unlinks a member', usage='<member>')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def unlink(self, ctx, member: discord.Member):
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute('UPDATE players SET discord_id = -1 WHERE discord_id = %s', (member.id, ))
                conn.commit()
                await ctx.send('Member {} unlinked.'.format(member.display_name))
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
            conn.rollback()
        finally:
            self.pool.putconn(conn)

    @commands.command(description='Resets the statistics of a specific server')
    @utils.has_role('Admin')
    @commands.guild_only()
    async def reset(self, ctx):
        server = await utils.get_server(self, ctx)
        if server:
            server_name = server['server_name']
            if server['status'] in ['Stopped', 'Shutdown']:
                conn = self.pool.getconn()
                try:
                    if await utils.yn_question(self, ctx, 'I\'m going to **DELETE ALL STATISTICS**\nof server "{}".\n\nAre you sure?'.format(server_name)) is True:
                        with closing(conn.cursor()) as cursor:
                            cursor.execute(
                                'DELETE FROM statistics WHERE mission_id in (SELECT id FROM missions WHERE '
                                'server_name = %s)', (server_name, ))
                            cursor.execute('DELETE FROM missions WHERE server_name = %s', (server_name, ))
                            conn.commit()
                        await ctx.send('Statistics for server "{}" have been wiped.'.format(server_name))
                except (Exception, psycopg2.DatabaseError) as error:
                    self.log.exception(error)
                    conn.rollback()
                finally:
                    self.pool.putconn(conn)
            else:
                await ctx.send('Please stop server "{}" before deleteing the statistics!'.format(server_name))

    def draw_playtime_planes(self, member, axis, server, period):
        SQL_PLAYTIME = 'SELECT s.slot, ROUND(SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on)))) AS playtime FROM ' \
                       'statistics s, players p, missions m WHERE s.player_ucid = p.ucid AND p.discord_id = %s AND ' \
                       's.hop_off IS NOT NULL AND s.mission_id = m.id '
        if server:
            SQL_PLAYTIME += 'AND m.server_name = \'{}\' '.format(server)
        if period:
            SQL_PLAYTIME += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
        SQL_PLAYTIME += 'GROUP BY s.slot ORDER BY 2'

        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_PLAYTIME, (member.id, ))
                labels = []
                values = []
                for row in cursor.fetchall():
                    labels.insert(0, row['slot'])
                    values.insert(0, row['playtime'] / 3600.0)
                axis.bar(labels, values, width=0.5, color='mediumaquamarine')
                for label in axis.get_xticklabels():
                    label.set_rotation(30)
                    label.set_ha('right')
                axis.set_title('Flighttimes per Plane', color='white', fontsize=25)
                axis.set_yticks([])
                for i in range(0, len(values)):
                    axis.annotate('{:.1f} h'.format(values[i]), xy=(
                        labels[i], values[i]), ha='center', va='bottom', weight='bold')
                if cursor.rowcount == 0:
                    axis.set_xticks([])
                    axis.text(0, 0, 'No data available.', ha='center', va='center', rotation=45, size=15)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    def draw_server_time(self, member, axis, server, period):
        SQL_STATISTICS = f"SELECT regexp_replace(m.server_name, '{self.bot.config['FILTER']['SERVER_FILTER']}', '', 'g') AS server_name, ROUND(SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on)))) AS playtime FROM statistics s, players p, missions m WHERE s.player_ucid = p.ucid AND p.discord_id = %s AND m.id = s.mission_id AND s.hop_off IS NOT NULL "
        if server:
            SQL_STATISTICS += 'AND m.server_name = \'{}\' '.format(server)
        if period:
            SQL_STATISTICS += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
        SQL_STATISTICS += 'GROUP BY 1'

        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_STATISTICS, (member.id, ))
                if cursor.rowcount > 0:
                    def func(pct, allvals):
                        absolute = int(round(pct/100.*np.sum(allvals)))
                        return '{:.1f}%\n({:s}h)'.format(pct, str(timedelta(seconds=absolute)))

                    labels = []
                    values = []
                    for row in cursor.fetchall():
                        labels.insert(0, row['server_name'])
                        values.insert(0, row['playtime'])
                    patches, texts, pcts = axis.pie(values, labels=labels, autopct=lambda pct: func(pct, values),
                                                    wedgeprops={'linewidth': 3.0, 'edgecolor': 'black'}, normalize=True)
                    plt.setp(pcts, color='black', fontweight='bold')
                    axis.set_title('Server Time', color='white', fontsize=25)
                    axis.axis('equal')
                else:
                    axis.set_visible(False)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    def draw_map_time(self, member, axis, server, period):
        SQL_STATISTICS = 'SELECT m.mission_theatre, ROUND(SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on)))) AS ' \
                         'playtime FROM statistics s, players p, missions m WHERE s.player_ucid = p.ucid AND ' \
                         'p.discord_id = %s AND m.id = s.mission_id AND s.hop_off IS NOT NULL '
        if server:
            SQL_STATISTICS += 'AND m.server_name = \'{}\' '.format(server)
        if period:
            SQL_STATISTICS += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
        SQL_STATISTICS += 'GROUP BY m.mission_theatre'

        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_STATISTICS, (member.id, ))
                if cursor.rowcount > 0:
                    def func(pct, allvals):
                        absolute = int(round(pct/100.*np.sum(allvals)))
                        return '{:.1f}%\n({:s}h)'.format(pct, str(timedelta(seconds=absolute)))

                    labels = []
                    values = []
                    for row in cursor.fetchall():
                        labels.insert(0, row['mission_theatre'])
                        values.insert(0, row['playtime'])
                    patches, texts, pcts = axis.pie(values, labels=labels, autopct=lambda pct: func(pct, values),
                                                    wedgeprops={'linewidth': 3.0, 'edgecolor': 'black'}, normalize=True)
                    plt.setp(pcts, color='black', fontweight='bold')
                    axis.set_title('Time per Map', color='white', fontsize=25)
                    axis.axis('equal')
                else:
                    axis.set_visible(False)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    def draw_recent(self, member, axis, server):
        SQL_STATISTICS = 'SELECT TO_CHAR(s.hop_on, \'MM/DD\') as day, ROUND(SUM(EXTRACT(EPOCH FROM (COALESCE(' \
                         's.hop_off, NOW()) - s.hop_on)))) AS playtime FROM statistics s, players p, missions m WHERE ' \
                         's.player_ucid = p.ucid AND p.discord_id = %s AND s.hop_on > (DATE(NOW()) - integer \'7\') ' \
                         'AND s.mission_id = m.id '
        if server:
            SQL_STATISTICS += 'AND m.server_name = \'{}\' '.format(server)
        SQL_STATISTICS += 'GROUP BY day'

        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                labels = []
                values = []
                cursor.execute(SQL_STATISTICS, (member.id, ))
                axis.set_title('Recent Activities', color='white', fontsize=25)
                axis.set_yticks([])
                for row in cursor.fetchall():
                    labels.append(row['day'])
                    values.append(row['playtime'] / 3600.0)
                axis.bar(labels, values, width=0.5, color='mediumaquamarine')
                for i in range(0, len(values)):
                    axis.annotate('{:.1f} h'.format(values[i]), xy=(
                        labels[i], values[i]), ha='center', va='bottom', weight='bold')
                if cursor.rowcount == 0:
                    axis.set_xticks([])
                    axis.text(0, 0, 'No data available.', ha='center', va='center', rotation=45, size=15)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    def draw_flight_performance(self, member, axis, server, period):
        SQL_STATISTICS = 'SELECT SUM(ejections) as ejections, SUM(crashes) as crashes, ' \
            'SUM(takeoffs) as takeoffs, SUM(landings) as landings FROM statistics s, ' \
            'players p, missions m WHERE s.player_ucid = p.ucid AND p.discord_id = %s' \
            'AND s.mission_id = m.id '
        if server:
            SQL_STATISTICS += 'AND m.server_name = \'{}\''.format(server)
        if period:
            SQL_STATISTICS += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)

        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_STATISTICS, (member.id, ))
                if cursor.rowcount > 0:
                    def func(pct, allvals):
                        absolute = int(round(pct/100.*np.sum(allvals)))
                        return '{:.1f}%\n({:d})'.format(pct, absolute)

                    labels = []
                    values = []
                    for item in dict(cursor.fetchone()).items():
                        if item[1] is not None and item[1] > 0:
                            labels.append(string.capwords(item[0]))
                            values.append(item[1])
                    if len(values) > 0:
                        patches, texts, pcts = axis.pie(values, labels=labels, autopct=lambda pct: func(pct, values),
                                                        wedgeprops={'linewidth': 3.0, 'edgecolor': 'black'}, normalize=True)
                        plt.setp(pcts, color='black', fontweight='bold')
                        axis.set_title('Flying', color='white', fontsize=25)
                        axis.axis('equal')
                    else:
                        axis.set_visible(False)
                else:
                    axis.set_visible(False)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    def draw_kill_performance(self, member, axis, server, period):
        SQL_STATISTICS = 'SELECT COALESCE(SUM(kills), 0) as kills, COALESCE(SUM(deaths), 0) as deaths, COALESCE(SUM(' \
                         'teamkills), 0) as teamkills FROM statistics s, players p, missions m WHERE s.player_ucid = ' \
                         'p.ucid AND p.discord_id = %s AND s.mission_id = m.id '
        if server:
            SQL_STATISTICS += 'AND m.server_name = \'{}\''.format(server)
        if period:
            SQL_STATISTICS += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)

        retval = []
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_STATISTICS, (member.id, ))
                if cursor.rowcount > 0:
                    def func(pct, allvals):
                        absolute = int(round(pct/100.*np.sum(allvals)))
                        return '{:.1f}%\n({:d})'.format(pct, absolute)

                    labels = []
                    values = []
                    explode = []
                    result = cursor.fetchone()
                    for item in dict(result).items():
                        if item[1] is not None and item[1] > 0:
                            labels.append(string.capwords(item[0]))
                            values.append(item[1])
                            if item[0] in ['deaths', 'kills']:
                                retval.append(item[0])
                                explode.append(0.1)
                            else:
                                explode.append(0.0)
                    if len(values):
                        angle1 = -180 * result[0]/np.sum(values)
                        angle2 = 180 - 180*result[1]/np.sum(values)
                        if angle1 == 0:
                            angle = angle2
                        elif angle2 == 180:
                            angle = angle1
                        else:
                            angle = angle1 + (angle2 + angle1) / 2

                        patches, texts, pcts = axis.pie(values, labels=labels, startangle=angle, explode=explode,
                                                        autopct=lambda pct: func(pct, values),
                                                        colors=['lightgreen', 'darkorange', 'lightblue'],
                                                        wedgeprops={'linewidth': 3.0, 'edgecolor': 'black'},
                                                        normalize=True)
                        plt.setp(pcts, color='black', fontweight='bold')
                        axis.set_title('Kill/Death-Ratio', color='white', fontsize=25)
                        axis.axis('equal')
                    else:
                        axis.set_visible(False)
                else:
                    axis.set_visible(False)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)
        return retval

    def draw_kill_types(self, member, axis, server, period):
        SQL_STATISTICS = 'SELECT 0 AS self, COALESCE(SUM(kills_planes), 0) as planes, COALESCE(SUM(' \
                         'kills_helicopters), 0) helicopters, COALESCE(SUM(kills_ships), 0) as ships, COALESCE(SUM(' \
                         'kills_sams), 0) as air_defence, COALESCE(SUM(kills_ground), 0) as ground FROM statistics s, ' \
                         'players p, missions m WHERE s.player_ucid = p.ucid AND p.discord_id = %s AND s.mission_id = ' \
                         'm.id '
        if server:
            SQL_STATISTICS += 'AND m.server_name = \'{}\' '.format(server)
        if period:
            SQL_STATISTICS += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)

        retval = False
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_STATISTICS, (member.id, ))
                # if no data was found, return False as no chart was drawn
                if cursor.rowcount > 0:
                    labels = []
                    values = []
                    for item in dict(cursor.fetchone()).items():
                        labels.append(string.capwords(item[0], sep='_').replace('_', ' '))
                        values.append(item[1])
                    xpos = 0
                    bottom = 0
                    width = 0.2
                    # there is something to be drawn
                    if np.sum(values) > 0:
                        for i in range(len(values)):
                            height = values[i]/np.sum(values)
                            axis.bar(xpos, height, width, bottom=bottom)
                            ypos = bottom + axis.patches[i].get_height() / 2
                            bottom += height
                            if int(values[i]) > 0:
                                axis.text(xpos, ypos, "%d%%" %
                                          (axis.patches[i].get_height() * 100), ha='center', color='black')

                        axis.set_title('Killed by\nPlayer', color='white', fontsize=15)
                        axis.axis('off')
                        axis.set_xlim(- 2.5 * width, 2.5 * width)
                        axis.legend(labels, fontsize=15, loc=3, ncol=6, mode='expand',
                                    bbox_to_anchor=(-2.4, -0.2, 2.8, 0.4), columnspacing=1, frameon=False)
                        # Chart was drawn, return True
                        retval = True
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)
        return retval

    def draw_death_types(self, member, axis, legend, server, period):
        SQL_STATISTICS = 'SELECT SUM(deaths - deaths_planes - deaths_helicopters - deaths_ships - deaths_sams - ' \
                         'deaths_ground) AS self, SUM(deaths_planes) as planes, SUM(deaths_helicopters) helicopters, ' \
                         'SUM(deaths_ships) as ships, SUM(deaths_sams) as air_defence, SUM(deaths_ground) as ground ' \
                         'FROM statistics s, players p, missions m WHERE s.player_ucid = p.ucid AND p.discord_id = %s ' \
                         'AND s.mission_id = m.id '
        if server:
            SQL_STATISTICS += 'AND m.server_name = \'{}\' '.format(server)
        if period:
            SQL_STATISTICS += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)

        retval = False
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_STATISTICS, (member.id, ))
                result = cursor.fetchone()
                # if no data was found, return False as no chart was drawn
                if cursor.rowcount > 0:
                    labels = []
                    values = []
                    for item in dict(result).items():
                        labels.append(string.capwords(item[0], sep='_').replace('_', ' '))
                        values.append(item[1])
                    xpos = 0
                    bottom = 0
                    width = 0.2
                    # there is something to be drawn
                    if np.sum(values) > 0:
                        for i in range(len(values)):
                            height = values[i]/np.sum(values)
                            axis.bar(xpos, height, width, bottom=bottom)
                            ypos = bottom + axis.patches[i].get_height() / 2
                            bottom += height
                            if int(values[i]) > 0:
                                axis.text(xpos, ypos, "%d%%" %
                                          (axis.patches[i].get_height() * 100), ha='center', color='black')

                        axis.set_title('Player\nkilled by', color='white', fontsize=15)
                        axis.axis('off')
                        axis.set_xlim(- 2.5 * width, 2.5 * width)
                        if legend is True:
                            axis.legend(labels, fontsize=15, loc=3, ncol=6, mode='expand',
                                        bbox_to_anchor=(0.6, -0.2, 2.8, 0.4), columnspacing=1, frameon=False)
                        # Chart was drawn, return True
                        retval = True
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)
        return retval

    @commands.command(description='Shows player statistics', usage='[member] [period]', aliases=['stats'])
    @utils.has_role('DCS')
    @commands.guild_only()
    async def statistics(self, ctx, member: Optional[discord.Member], period: Optional[str], server=None):
        try:
            if member is None:
                member = ctx.message.author
            if period and period not in ['day', 'week', 'month']:
                await ctx.send('Period must be one of day/week/month!')
                return
            # Check if there are statistics available for this user at all
            conn = self.pool.getconn()
            try:
                with closing(conn.cursor()) as cursor:
                    cursor.execute('SELECT COUNT(s.*) FROM statistics s, players p WHERE s.player_ucid = p.ucid AND '
                                   'p.discord_id = %s', (member.id, ))
                    if cursor.fetchone()[0] == 0:
                        await ctx.send(f'There are no statistics available for user "{member.display_name}"')
                        return
            except (Exception, psycopg2.DatabaseError) as error:
                self.log.exception(error)
            finally:
                self.pool.putconn(conn)

            plt.style.use('dark_background')
            plt.rcParams['axes.facecolor'] = '2C2F33'
            figure = plt.figure(figsize=(20, 20))
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                executor.submit(self.draw_playtime_planes, member=member,
                                axis=plt.subplot2grid((3, 3), (0, 0), colspan=2, fig=figure), server=server, period=period)
                executor.submit(self.draw_recent, member=member, axis=plt.subplot2grid(
                    (3, 3), (0, 2), colspan=1, fig=figure), server=server)
                executor.submit(self.draw_server_time, member=member,
                                axis=plt.subplot2grid((3, 3), (1, 0), colspan=1, fig=figure), server=server, period=period)
                executor.submit(self.draw_map_time, member=member,
                                axis=plt.subplot2grid((3, 3), (1, 1), colspan=1, fig=figure), server=server, period=period)
                executor.submit(self.draw_flight_performance, member=member,
                                axis=plt.subplot2grid((3, 3), (1, 2), colspan=1, fig=figure), server=server, period=period)
            ax1 = plt.subplot2grid((3, 3), (2, 0), colspan=1, fig=figure)
            ax2 = plt.subplot2grid((3, 3), (2, 1), colspan=1, fig=figure)
            ax3 = plt.subplot2grid((3, 3), (2, 2), colspan=1, fig=figure)
            retval = self.draw_kill_performance(member, ax2, server, period)
            i = 0
            if ('kills' in retval) and (self.draw_kill_types(member, ax3, server, period) is True):
                # use ConnectionPatch to draw lines between the two plots
                # get the wedge data
                theta1, theta2 = ax2.patches[i].theta1, ax2.patches[i].theta2
                center, r = ax2.patches[i].center, ax2.patches[i].r
                bar_height = sum([item.get_height() for item in ax3.patches])

                # draw top connecting line
                x = r * np.cos(np.pi / 180 * theta2) + center[0]
                y = r * np.sin(np.pi / 180 * theta2) + center[1]
                con = ConnectionPatch(xyA=(-0.2 / 2, bar_height), coordsA=ax3.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax3.add_artist(con)

                # draw bottom connecting line
                x = r * np.cos(np.pi / 180 * theta1) + center[0]
                y = r * np.sin(np.pi / 180 * theta1) + center[1]
                con = ConnectionPatch(xyA=(-0.2 / 2, 0), coordsA=ax3.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax3.add_artist(con)
                i += 1
            else:
                ax3.set_visible(False)
            if ('deaths' in retval) and (self.draw_death_types(member, ax1, (i == 0), server, period) is True):
                # use ConnectionPatch to draw lines between the two plots
                # get the wedge data
                theta1, theta2 = ax2.patches[i].theta1, ax2.patches[i].theta2
                center, r = ax2.patches[i].center, ax2.patches[i].r
                bar_height = sum([item.get_height() for item in ax1.patches])

                # draw top connecting line
                x = r * np.cos(np.pi / 180 * theta2) + center[0]
                y = r * np.sin(np.pi / 180 * theta2) + center[1]
                con = ConnectionPatch(xyA=(0.2 / 2, 0), coordsA=ax1.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax1.add_artist(con)

                # draw bottom connecting line
                x = r * np.cos(np.pi / 180 * theta1) + center[0]
                y = r * np.sin(np.pi / 180 * theta1) + center[1]
                con = ConnectionPatch(xyA=(0.2 / 2, bar_height), coordsA=ax1.transData,
                                      xyB=(x, y), coordsB=ax2.transData)
                con.set_color('lightgray')
                con.set_linewidth(2)
                con.set_linestyle('dashed')
                ax1.add_artist(con)
            else:
                ax1.set_visible(False)

            plt.subplots_adjust(hspace=0.5, wspace=0.5)
            title = 'Statistics for {}'.format(member.display_name)
            if server is not None:
                title += '\n_{}_'.format(server)
            else:
                title += '\n_- Overall -_'
            embed = discord.Embed(title=title, color=discord.Color.blue())
            filename = f'{ctx.message.id}.png'
            figure.savefig(filename, bbox_inches='tight', facecolor='#2C2F33')
            plt.close(figure)
            file = discord.File(filename)
            embed.set_image(url='attachment://' + filename)
            footer = 'Click on the image to zoom in.'
            if len(self.servers) > 1:
                footer += '\nPress ◀️ or ▶️ to cycle through per-server statistics.'
            embed.set_footer(text=footer)
            message = None
            try:
                with suppress(Exception):
                    message = await ctx.send(file=file, embed=embed)
                os.remove(filename)
                if message and (len(self.servers) > 1):
                    await message.add_reaction('◀️')
                    await message.add_reaction('▶️')
                    react = await utils.wait_for_single_reaction(self, ctx, message)
                    await message.delete()
                    if server is None:
                        prev = self.servers[-1]
                        nxt = self.servers[0]
                    else:
                        i = 0
                        prev = nxt = None
                        for s in self.servers:
                            if s == server:
                                break
                            i += 1
                        if i < len(self.servers) - 1:
                            nxt = self.servers[i + 1]
                        if i > 0:
                            prev = self.servers[i - 1]

                    if react.emoji == '◀️':
                        await self.statistics(ctx, member, period, prev)
                    elif react.emoji == '▶️':
                        await self.statistics(ctx, member, period, nxt)
            except asyncio.TimeoutError:
                embed.set_footer(text='Click on the image to zoom in.')
                await message.edit(embed=embed)
                await message.clear_reactions()
        except Exception as error:
            self.log.exception(error)

    def draw_highscore_playtime(self, ctx, axis, period, server, limit):
        SQL_HIGHSCORE_PLAYTIME = 'SELECT p.discord_id, ROUND(SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on)))) AS ' \
                                 'playtime FROM statistics s, players p, missions m WHERE p.ucid = s.player_ucid AND ' \
                                 's.hop_off IS NOT NULL AND p.discord_id <> -1 AND s.mission_id = m.id '
        if server:
            SQL_HIGHSCORE_PLAYTIME += ' AND m.server_name = \'{}\' '.format(server)
        if period:
            SQL_HIGHSCORE_PLAYTIME += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
        SQL_HIGHSCORE_PLAYTIME += f' GROUP BY p.discord_id ORDER BY 2 DESC LIMIT {limit}'
        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                labels = []
                values = []
                cursor.execute(SQL_HIGHSCORE_PLAYTIME)
                for row in cursor.fetchall():
                    member = ctx.message.guild.get_member(row[0])
                    name = member.display_name if member else 'Unknown'
                    labels.insert(0, name)
                    values.insert(0, row[1] / 3600)
                axis.barh(labels, values, color=['#CD7F32', 'silver', 'gold'], height=0.75)
                axis.set_xlabel('hours')
                axis.set_title('Longest Playtimes', color='white', fontsize=25)
                if len(values) == 0:
                    axis.set_xticks([])
                    axis.set_yticks([])
                    axis.text(0, 0, 'No data available.', ha='center', va='center', size=15)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    def draw_highscore_kills(self, ctx, figure, period, server, limit):
        SQL_PARTS = {
            'Air Targets': 'SUM(s.kills_planes+s.kills_helicopters)',
            'Ships': 'SUM(s.kills_ships)',
            'Air Defence': 'SUM(s.kills_sams)',
            'Ground Targets': 'SUM(s.kills_ground)',
            'Most Efficient Killers': 'SUM(s.kills) / (SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on))) / 3600)',
            'Most Wasteful Pilots': 'SUM(s.crashes) / (SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on))) / 3600)'
        }
        LABELS = {
            'Air Targets': 'kills',
            'Ships': 'kills',
            'Air Defence': 'kills',
            'Ground Targets': 'kills',
            'Most Efficient Killers': 'kills / h',
            'Most Wasteful Pilots': 'airframes wasted / h'
        }
        COLORS = ['#CD7F32', 'silver', 'gold']
        SQL_HIGHSCORE = {}
        for key in SQL_PARTS.keys():
            SQL_HIGHSCORE[key] = 'SELECT p.discord_id, {} FROM players p, statistics s, missions m WHERE ' \
                                 's.player_ucid = p.ucid AND p.discord_id <> -1 AND s.mission_id = m.id'.format(
                SQL_PARTS[key])
            if server:
                SQL_HIGHSCORE[key] += ' AND m.server_name = \'{}\' '.format(server)
            if period:
                SQL_HIGHSCORE[key] += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
            SQL_HIGHSCORE[key] += ' AND s.hop_off IS NOT NULL GROUP BY p.discord_id HAVING {} > 0 ORDER BY 2 DESC ' \
                                  'LIMIT {}'.format(SQL_PARTS[key], limit)

        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                keys = list(SQL_PARTS.keys())
                for j in range(0, len(keys)):
                    typ = keys[j]
                    cursor.execute(SQL_HIGHSCORE[typ])
                    result = cursor.fetchall()
                    axis = plt.subplot2grid((4, 2), (1+int(j/2), j % 2), colspan=1, fig=figure)
                    labels = []
                    values = []
                    for i in range(0, len(result)):
                        if len(result) > i:
                            member = ctx.message.guild.get_member(result[i][0])
                            name = member.display_name if member else 'Unkown'
                            labels.insert(0, name)
                            values.insert(0, result[i][1])
                    axis.barh(labels, values, color=COLORS, label=typ, height=0.75)
                    axis.set_title(typ, color='white', fontsize=25)
                    axis.set_xlabel(LABELS[typ])
                    if len(values) == 0:
                        axis.set_xticks([])
                        axis.set_yticks([])
                        axis.text(0, 0, 'No data available.', ha='center', va='center', rotation=45, size=15)
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    @commands.command(description='Shows actual highscores', usage='[period]', aliases=['hs'])
    @utils.has_role('DCS')
    @commands.guild_only()
    async def highscore(self, ctx, period=None, server=None):
        if period and period not in ['day', 'week', 'month']:
            await ctx.send('Period must be one of day/week/month!')
            return
        try:
            plt.style.use('dark_background')
            plt.rcParams['axes.facecolor'] = '2C2F33'
            figure = plt.figure(figsize=(15, 20))
            limit = self.config['STATISTICS']['NUM_HIGHSCORE']
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                executor.submit(self.draw_highscore_playtime, ctx=ctx, axis=plt.subplot2grid(
                    (4, 2), (0, 0), colspan=2, fig=figure), period=period, server=server, limit=limit)
                executor.submit(self.draw_highscore_kills, ctx=ctx, figure=figure,
                                period=period, server=server, limit=limit)
            plt.subplots_adjust(hspace=0.5, wspace=0.5)
            title = f'Highscores (TOP {limit})'
            if period:
                title += ' of the ' + string.capwords(period)
            if server is not None:
                title += '\n_{}_'.format(server)
            else:
                title += '\n_- Overall -_'
            embed = discord.Embed(title=title, color=discord.Color.blue())
            filename = f'{ctx.message.id}.png'
            figure.savefig(filename, bbox_inches='tight', facecolor='#2C2F33')
            plt.close(figure)
            file = discord.File(filename)
            embed.set_image(url='attachment://' + filename)
            footer = 'Click on the image to zoom in.'
            if len(self.servers) > 1:
                footer += '\nPress ◀️ or ▶️ to cycle through per-server highscores.'
            embed.set_footer(text=footer)
            message = None
            try:
                with suppress(Exception):
                    message = await ctx.send(file=file, embed=embed)
                os.remove(filename)
                if message and (len(self.servers) > 1):
                    await message.add_reaction('◀️')
                    await message.add_reaction('▶️')
                    react = await utils.wait_for_single_reaction(self, ctx, message)
                    await message.delete()
                    if server is None:
                        prev = self.servers[-1]
                        nxt = self.servers[0]
                    else:
                        i = 0
                        prev = nxt = None
                        for s in self.servers:
                            if s == server:
                                break
                            i += 1
                        if i < len(self.servers) - 1:
                            nxt = self.servers[i + 1]
                        if i > 0:
                            prev = self.servers[i - 1]

                    if react.emoji == '◀️':
                        await self.highscore(ctx, period, prev)
                    elif react.emoji == '▶️':
                        await self.highscore(ctx, period, nxt)
            except asyncio.TimeoutError:
                embed.set_footer(text='Click on the image to zoom in.')
                await message.edit(embed=embed)
                await message.clear_reactions()
        except Exception as error:
            self.log.exception(error)

    def draw_server_stats(self, period, server):
        SQL_USER_BASE = 'SELECT COUNT(DISTINCT p.ucid) AS dcs_users, COUNT(DISTINCT p.discord_id) AS discord_users ' \
                        'FROM players p, missions m, statistics s WHERE m.id = s.mission_id and s.player_ucid = p.ucid '
        SQL_SERVER_USAGE = f"SELECT trim(regexp_replace(m.server_name, '{self.bot.config['FILTER']['SERVER_FILTER']}', '', 'g')) AS server_name, ROUND(SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on))) / 3600) AS playtime, COUNT(DISTINCT s.player_ucid) AS players FROM missions m, statistics s WHERE m.id = s.mission_id AND s.hop_off IS NOT NULL "
        SQL_TOP_MISSIONS_OUTER_LEFT = 'SELECT server_name, mission_name, playtime FROM (SELECT server_name, ' \
                                      'mission_name, playtime, ROW_NUMBER() OVER(PARTITION BY server_name ORDER BY ' \
                                      'playtime DESC) AS rn FROM ( '
        SQL_TOP_MISSIONS_INNER = f"SELECT trim(regexp_replace(m.server_name, '{self.bot.config['FILTER']['SERVER_FILTER']}', '', 'g')) AS server_name, trim(regexp_replace(m.mission_name, '{self.bot.config['FILTER']['MISSION_FILTER']}', ' ', 'g')) AS mission_name, ROUND(SUM(EXTRACT(EPOCH FROM (s.hop_off - s.hop_on))) / 3600) AS playtime FROM missions m, statistics s WHERE m.id = s.mission_id AND s.hop_off IS NOT NULL"
        SQL_TOP_MISSIONS_OUTER_RIGHT = ') AS x) AS y WHERE rn {} ORDER BY 3 DESC'
        SQL_TOP_MODULES = 'SELECT s.slot, COUNT(s.slot) AS num_usage, ROUND(SUM(EXTRACT(EPOCH FROM (s.hop_off - ' \
                          's.hop_on))) / 3600) AS playtime, COUNT(DISTINCT s.player_ucid) AS players FROM missions m, ' \
                          'statistics s WHERE m.id = s.mission_id '
        SQL_LAST_14DAYS = 'SELECT d.date AS date, COUNT(DISTINCT s.player_ucid) AS players FROM statistics s, ' \
                          'missions m, generate_series(DATE(NOW()) - INTERVAL \'2 weeks\', DATE(NOW()), INTERVAL \'1 ' \
                          'day\') d WHERE d.date BETWEEN DATE(s.hop_on) AND DATE(s.hop_off) AND s.mission_id = m.id '
        SQL_MAIN_TIMES = 'SELECT to_char(s.hop_on, \'ID\') as weekday, to_char(h.time, \'HH24\') AS hour, ' \
                         'COUNT(DISTINCT s.player_ucid) AS players FROM statistics s, missions m, generate_series(' \
                         'TIMESTAMP \'01.01.1970 00:00:00\', TIMESTAMP \'01.01.1970 23:00:00\', INTERVAL \'1 hour\') ' \
                         'h WHERE date_part(\'hour\', h.time) BETWEEN date_part(\'hour\', s.hop_on) AND date_part(' \
                         '\'hour\', s.hop_off) AND s.mission_id = m.id '

        embed = discord.Embed(color=discord.Color.blue())
        embed.title = 'Server Statistics'
        if server:
            SQL_USER_BASE += ' AND m.server_name = \'{}\' '.format(server)
            SQL_SERVER_USAGE += ' AND m.server_name = \'{}\' '.format(server)
            SQL_TOP_MISSIONS_INNER += ' AND m.server_name = \'{}\' '.format(server)
            SQL_TOP_MODULES += ' AND m.server_name = \'{}\' '.format(server)
            SQL_LAST_14DAYS += ' AND m.server_name = \'{}\' '.format(server)
            SQL_MAIN_TIMES += ' AND m.server_name = \'{}\' '.format(server)
        if period:
            SQL_USER_BASE += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
            SQL_SERVER_USAGE += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
            SQL_TOP_MISSIONS_INNER += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
            SQL_TOP_MODULES += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
            SQL_MAIN_TIMES += ' AND DATE(s.hop_on) > (DATE(NOW()) - interval \'1 {}\')'.format(period)
            embed.title = string.capwords(period if period != 'day' else 'dai') + 'ly ' + embed.title
        else:
            embed.title = 'Overall ' + embed.title
        SQL_SERVER_USAGE += ' GROUP BY 1 ORDER BY 2 DESC'
        SQL_TOP_MISSIONS_INNER += ' GROUP BY 1, 2'
        SQL_TOP_MODULES += ' GROUP BY s.slot ORDER BY 3 DESC LIMIT 10'
        SQL_LAST_14DAYS += ' GROUP BY d.date'
        SQL_MAIN_TIMES += ' GROUP BY 1, 2'

        if server:
            embed.title += '\n_{}_'.format(server)

        conn = self.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(SQL_USER_BASE)
                row = cursor.fetchone()
                unique_ucids = str(row[0])
                unique_dicord_ids = str(row[1])
                if not server:
                    embed.add_field(name='Unique Players', value=unique_ucids)
                    embed.add_field(name='Discord Members', value=unique_dicord_ids)
                    embed.add_field(name='_ _', value='_ _')
                # Server usages
                servers = playtimes = players = ''
                cursor.execute(SQL_SERVER_USAGE)
                for row in cursor.fetchall():
                    servers += row['server_name'] + '\n'
                    playtimes += '{:.0f}\n'.format(row['playtime'])
                    players += '{:.0f}\n'.format(row['players'])
                if len(servers) > 0:
                    if not server:
                        embed.add_field(name='Server', value=servers)
                    embed.add_field(name='Playtime (h)', value=playtimes)
                    embed.add_field(name='Unique Players', value=players)
                    if server:
                        embed.add_field(name='Discord Members', value=unique_dicord_ids)
                # TOP missions per server
                servers = missions = playtimes = ''
                cursor.execute(SQL_TOP_MISSIONS_OUTER_LEFT + SQL_TOP_MISSIONS_INNER + SQL_TOP_MISSIONS_OUTER_RIGHT.format('= 1' if not server else '<= 3'))
                for row in cursor.fetchall():
                    servers += row['server_name'] + '\n'
                    missions += row['mission_name'][:20] + '\n'
                    playtimes += '{:.0f}\n'.format(row['playtime'])
                if len(servers) > 0:
                    if not server:
                        embed.add_field(name='Server', value=servers)
                    embed.add_field(name='TOP Mission' if not server else 'TOP 3 Missions', value=missions)
                    embed.add_field(name='Playtime (h)', value=playtimes)
                    if server:
                        embed.add_field(name='_ _', value='_ _')
                # TOP 10 modules
                modules = playtimes = players = ''
                cursor.execute(SQL_TOP_MODULES)
                for row in cursor.fetchall():
                    modules += row['slot'] + '\n'
                    playtimes += '{:.0f}\n'.format(row['playtime'])
                    players += '{:.0f} ({:.0f})\n'.format(row['players'], row['num_usage'])
                if len(modules) > 0:
                    embed.add_field(name='TOP 10 Modules', value=modules)
                    embed.add_field(name='Playtime (h)', value=playtimes)
                    embed.add_field(name='Players (# uses)', value=players)
                # Draw charts
                plt.style.use('dark_background')
                plt.rcParams['axes.facecolor'] = '2C2F33'
                figure = plt.figure(figsize=(15, 10))
                # Last 7 days
                axis = plt.subplot2grid((2, 1), (0, 0), colspan=1, fig=figure)
                labels = []
                values = []
                cursor.execute(SQL_LAST_14DAYS)
                for row in cursor.fetchall():
                    labels.append(row['date'].strftime('%a %m/%d'))
                    values.append(row['players'])
                axis.bar(labels, values, width=0.5, color='dodgerblue')
                axis.set_title('Unique Players past 14 Days', color='white', fontsize=25)
                axis.set_yticks([])
                for label in axis.get_xticklabels():
                    label.set_rotation(30)
                    label.set_ha('right')
                for i in range(0, len(values)):
                    axis.annotate(values[i], xy=(
                        labels[i], values[i]), ha='center', va='bottom', weight='bold')
                if len(values) == 0:
                    axis.set_xticks([])
                    axis.text(0, 0, 'No data available.', ha='center', va='center', rotation=45, size=15)
                # Times & Days
                axis = plt.subplot2grid((2, 1), (1, 0), colspan=1, fig=figure)
                values = np.zeros((24, 7))
                cursor.execute(SQL_MAIN_TIMES)
                for row in cursor.fetchall():
                    values[int(row['hour'])][int(row['weekday'])-1] = row['players']
                axis.imshow(values, cmap='cividis', aspect='auto')
                axis.set_title('Users per Day/Time (UTC)', color='white', fontsize=25)
                # axis.invert_yaxis()
                axis.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: self.WEEKDAYS[int(np.clip(x, 0, 6))]))
                plt.subplots_adjust(hspace=0.5, wspace=0.0)
                footer = 'Click on the image to zoom in.'
                if len(self.servers) > 1:
                    footer += '\nPress ◀️ or ▶️ to cycle through per-server statistics.'
                embed.set_footer(text=footer)
                return embed, figure
        except (Exception, psycopg2.DatabaseError) as error:
            self.log.exception(error)
        finally:
            self.pool.putconn(conn)

    @commands.command(description='Shows servers statistics', usage='[period]')
    @utils.has_role('Admin')
    @commands.guild_only()
    async def serverstats(self, ctx, period=None, server=None):
        if period and period not in ['day', 'week', 'month']:
            await ctx.send('Period must be one of day/week/month!')
            return
        embed, figure = self.draw_server_stats(period, server)
        filename = f'{ctx.message.id}.png'
        figure.savefig(filename, bbox_inches='tight', facecolor='#2C2F33')
        plt.close(figure)
        file = discord.File(filename)
        embed.set_image(url='attachment://' + filename)
        message = None
        try:
            with suppress(Exception):
                message = await ctx.send(file=file, embed=embed)
            os.remove(filename)
            if message and (len(self.servers) > 1):
                await message.add_reaction('◀️')
                await message.add_reaction('▶️')
                react = await utils.wait_for_single_reaction(self, ctx, message)
                await message.delete()
                if server is None:
                    prev = self.servers[-1]
                    nxt = self.servers[0]
                else:
                    i = 0
                    prev = nxt = None
                    for s in self.servers:
                        if s == server:
                            break
                        i += 1
                    if i < len(self.servers) - 1:
                        nxt = self.servers[i + 1]
                    if i > 0:
                        prev = self.servers[i - 1]

                if react.emoji == '◀️':
                    await self.serverstats(ctx, period, prev)
                elif react.emoji == '▶️':
                    await self.serverstats(ctx, period, nxt)
        except asyncio.TimeoutError:
            embed.set_footer(text='Click on the image to zoom in.')
            await message.edit(embed=embed)
            await message.clear_reactions()

    @commands.command(description='Shows information about a specific player', usage='<@member / ucid>')
    @utils.has_role('DCS Admin')
    @commands.guild_only()
    async def player(self, ctx, member: Union[discord.Member, str]):
        sql = 'SELECT p.discord_id, p.ucid, p.last_seen, COALESCE(p.name, \'?\') AS NAME, COALESCE(ROUND(SUM(EXTRACT(' \
              'EPOCH FROM (s.hop_off - s.hop_on))) / 3600), 0) AS playtime FROM players p LEFT OUTER JOIN statistics ' \
              's ON (s.player_ucid = p.ucid) WHERE p.discord_id = '
        if isinstance(member, str):
            sql += f"(SELECT discord_id FROM players WHERE ucid = '{member}' AND discord_id != -1) OR p.ucid = '{member}'"
        else:
            sql += f"'{member.id}'"
        sql += ' GROUP BY p.ucid, p.discord_id, p.name, p.last_seen'
        conn = self.bot.pool.getconn()
        try:
            with closing(conn.cursor(cursor_factory=psycopg2.extras.DictCursor)) as cursor:
                cursor.execute(sql)
                rows = list(cursor.fetchall())
                if rows is not None and len(rows) > 0:
                    embed = discord.Embed(title='User Information', color=discord.Color.blue())
                    embed.description = f'Information about '
                    if rows[0]['discord_id'] != -1:
                        member = ctx.guild.get_member(rows[0]['discord_id'])
                    if isinstance(member, discord.Member):
                        embed.description += f'member **{member.display_name}**:'
                        embed.add_field(name='Discord ID:', value=member.id)
                    else:
                        embed.description += f'a non-member user:'
                    if rows[0]['last_seen']:
                        embed.add_field(name='Last seen:', value=rows[0]['last_seen'].strftime("%m/%d/%Y, %H:%M:%S"))
                    embed.add_field(name='▬' * 30, value='_ _', inline=False)
                    ucids = names = playtimes = ''
                    for line in rows:
                        ucids += line['ucid'] + '\n'
                        names += line['name'] + '\n'
                        playtimes += '{:.0f}\n'.format(line['playtime'])
                    embed.add_field(name='UCID', value=ucids)
                    embed.add_field(name='DCS Name', value=names)
                    embed.add_field(name='Playtime (h)', value=playtimes)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f'No data found for user "{member if isinstance(member, str) else member.display_name}".')
        except (Exception, psycopg2.DatabaseError) as error:
            self.bot.log.exception(error)
        finally:
            self.bot.pool.putconn(conn)


def setup(bot: DCSServerBot):
    if 'mission' not in bot.plugins:
        raise PluginRequiredError('mission')
    listener = UserStatisticsEventListener(bot)
    if bot.config.getboolean('BOT', 'MASTER') is True:
        bot.add_cog(MasterUserStatistics(bot, listener))
    else:
        bot.add_cog(AgentUserStatistics(bot, listener))