import discord
import psycopg
from discord import app_commands
from core import DCSServerBot, Plugin, utils, Channel, Coalition, command


class Battleground(Plugin):

    def __init__(self, bot: DCSServerBot):
        super().__init__(bot)

    def rename(self, conn: psycopg.Connection, old_name: str, new_name: str) -> None:
        conn.execute("UPDATE bg_geometry SET server = %s WHERE server= %s", (new_name, old_name))

    @command(description='Push MGRS coordinates with screenshots to DCS Battleground')
    @app_commands.guild_only()
    @utils.app_has_role('DCS')
    async def recon(self, interaction: discord.Interaction, name: str, mgrs: str):
        if not interaction.message.attachments or \
                not interaction.message.attachments[0].filename[-4:] in ['.jpg', '.gif', '.png']:
            await interaction.response.send_message('You need to add one or more screenshots (.jpg/.gif/.png)',
                                                    ephemeral=True)
            return
        done = False
        for server in self.bot.servers.values():
            sides = utils.get_sides(interaction, server)
            blue_channel = server.channels.get(Channel.COALITION_BLUE_CHAT)
            red_channel = server.channels.get(Channel.COALITION_RED_CHAT)
            if Coalition.BLUE in sides and blue_channel and blue_channel.id == interaction.message.channel.id:
                side = "blue"
            elif Coalition.RED in sides and red_channel and red_channel.id == interaction.message.channel.id:
                side = "red"
            else:
                continue
            done = True
            screenshots = [att.url for att in interaction.message.attachments]
            with self.pool.connection() as conn:
                with conn.transation():
                    conn.execute("""
                        INSERT INTO bg_geometry(id, type, name, posmgrs, screenshot, discordname, avatar, side, server) 
                        VALUES (nextval('bg_geometry_id_seq'), 'recon', %s, %s, %s, %s, %s, %s, %s)
                    """, (name, mgrs, screenshots, interaction.user.name, interaction.user.display_avatar.url,
                          side, server.name))
            await interaction.response.send_message(f"Recon data added - {side} side - {server.name}", ephemeral=True)
        if not done:
            await interaction.response.send_message('Coalitions have to be enabled and you need to use this command '
                                                    'in one of your coalition channels.', ephemeral=True)


async def setup(bot: DCSServerBot):
    await bot.add_cog(Battleground(bot))