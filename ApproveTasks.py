from __future__ import annotations
import datetime
import discord
from discord.interactions import Interaction
import discord.ui
import gspread
from Data import *
import Queries
import os
from dotenv import load_dotenv
load_dotenv(override=True)

EMBED_ICON_URL = "https://shorturl.at/wGOXY"
BINGO_LOGS_CHANNEL = 1195530905398284348
TZ_OFFSET = -6.0

tz_info = datetime.timezone(datetime.timedelta(hours=TZ_OFFSET))

class ApproveTasks(discord.ui.View):
    def __init__(self, ctx, bot, timeout: float = 45.0) -> None:
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot
        self.current_page = 1
    
    async def interaction_check(self, interaction: Interaction[discord.Client]):
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message(
            f"The command was initiated by {self.ctx.author}", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        try:
            if self.message:
                await self.message.delete()
        except:
            pass
        
    def create_embed(self, data, index):
        if len(data) == 0:
            embed = discord.Embed(title="There are no submissions available for approval.")
            return embed

        self.submission_id = self.data[index - 1].get('submission_id')
        self.task_id = self.data[index - 1].get('task_id')
        self.img_url = self.data[index - 1].get('img_url')
        self.jump_url = self.data[index - 1].get('jump_url')
        self.channel_id = self.data[index - 1].get('channel_id')
        self.message_id = self.data[index - 1].get('message_id')
        self.player = self.data[index - 1].get('player')
        self.team = self.data[index - 1].get('team')
        self.date = self.data[index - 1].get('date_submitted')

        embed = discord.Embed(title=f"Submission ID Number: {self.submission_id}", url=self.jump_url)
        embed.set_thumbnail(url=self.img_url)
        embed.add_field(name="Task:", value=task_list.get(self.task_id), inline=False)
        embed.add_field(name="Submission:", value=f"[HERE]({self.jump_url})", inline=True)
        embed.add_field(name="Player:", value=f"{self.player}", inline=True)
        embed.add_field(name="", value="", inline=True)
        embed.add_field(name="Team:", value=f"{self.team}", inline=True)
        embed.add_field(name="Date Submitted:", value=f"{self.date}", inline=True)
        embed.add_field(name="", value="", inline=True)

        return embed

    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.update_message(self.data, 1)

    async def update_message(self, data, index):
        await self.update_buttons(data)
        await self.message.edit(embed=self.create_embed(data, index), view=self)





    @discord.ui.button(
        label="<", custom_id="prev_button", style=discord.ButtonStyle.blurple
    )
    async def prev_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page -= 1
        await interaction.response.defer()
        await self.update_message(self.data, self.current_page)

    @discord.ui.button(
        label="Approve", custom_id="submit_button", style=discord.ButtonStyle.green
    )
    async def submit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message("Approving submission, please do not touch the submission screen until current submission has been approved.", delete_after=5.0)

        await Queries.task_complete(self.team, self.task_id, self.player)
        await self.update_team_sheet(self.team, self.task_id, self.player, 2)
        await Queries.remove_submission_by_id(self.submission_id)
        await self.post_approval_embed()
        try:
            ch = await self.bot.fetch_channel(self.channel_id)
            msg = await ch.fetch_message(self.message_id)
            await msg.add_reaction("✅")
        except:
            print("Foki Bot: Message is not available to react to.")
        
        self.data = await Queries.get_submissions()
        self.current_page -= 1
        await self.update_message(self.data, self.current_page)
        
        # LOG
        print(
            "Foki Bot: Captain, submission ID # {0} has been approved.".format(
                self.submission_id
            )
        )

    @discord.ui.button(
        label="Deny", custom_id="deny_button", style=discord.ButtonStyle.red
    )
    async def deny_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message("Denying submission, please do not touch the submission screen until current submission has been denied.", delete_after=5.0)

        await self.update_team_sheet(self.team, self.task_id, self.player, 3)
        await Queries.remove_submission_by_id(self.submission_id)
        await self.post_deny_embed()
        
        try:
            ch = await self.bot.fetch_channel(self.channel_id)
            msg = await ch.fetch_message(self.message_id)
            await msg.add_reaction("❌")
        except:
            print("Foki Bot: Message is not available to react to.")

        self.data = await Queries.get_submissions()
        self.current_page -= 1
        await self.update_message(self.data, self.current_page)

        # LOG
        print(
            "Foki Bot: Captain, submission ID # {0} has been DENIED.".format(
                self.submission_id
            )
        )

    @discord.ui.button(
        label=">", custom_id="next_button", style=discord.ButtonStyle.blurple
    )
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page += 1
        await interaction.response.defer()
        await self.update_message(self.data, self.current_page)

    """
    Updates team sheet on Google sheets
    team - string player team name
    task - int task number
    code - method special parameter
    Updates the task cell on Google Sheets per code status
    1 = Awaiting Approval, 2 = Complete, 3 = Incomplete
    """

    async def update_team_sheet(self, team: str, task: int, player: str, code: int):
        # CODES: 1 = Awaiting Approval, 2 = Complete, 3 = Incomplete
        gc = gspread.service_account(filename="service_account.json")
        GOOGLE_SHEETS_KEY = os.getenv("GOOGLE_SHEETS_KEY")

        d = datetime.datetime.now(tz_info)
        sheet = gc.open_by_key(GOOGLE_SHEETS_KEY)

        TASK_STATUS_COLUMN = 5
        TASK_DATE_COLUMN = 6
        cell_row = task + 1

        # Getting team specific sheet
        team_sheet = sheet.worksheet(team)

        # Updating task on team sheet
        if code == 1:
            team_sheet.update_cell(cell_row, TASK_STATUS_COLUMN, "Awaiting Approval")
            team_sheet.update_cell(cell_row, TASK_DATE_COLUMN, str(d))
            print(f"SHEETS: Updating task {task} for team {team}")
        elif code == 2:
            current_score = int(team_sheet.cell(4, 10).value)
            if current_score == None:
                current_score = 0
            points = task_points.get(task)
            team_sheet.update_cell(cell_row, TASK_STATUS_COLUMN, "Complete")
            team_sheet.update_cell(cell_row, TASK_DATE_COLUMN, str(d))
            team_sheet.update_cell(4, 10, (current_score + points))
            print(f"SHEETS: Approving task {task} for team {team}")
        else:
            team_sheet.update_cell(cell_row, TASK_STATUS_COLUMN, "Incomplete")
            team_sheet.update_cell(cell_row, TASK_DATE_COLUMN, str(d))
            print(f"SHEETS: Denying task {task} for team {team}")

        history_sheet = sheet.worksheet("History")
        history_sheet.insert_row([player, team, task, code, str(d)], index=2)
        print("SHEETS: History recorded.")

    async def update_buttons(self, data):
        if len(data) == 0:
            self.prev_button.disabled = True
            self.submit_button.disabled = True
            self.deny_button.disabled = True
            self.next_button.disabled = True
        elif len(data) == 1:
            self.prev_button.disabled = True
            self.next_button.disabled = True
        elif self.current_page == 1:
            self.prev_button.disabled = True
            self.next_button.disabled = False
        elif self.current_page == len(data):
            self.next_button.disabled = True
            self.prev_button.disabled = False
        else:
            self.prev_button.disabled = False
            self.submit_button.disabled = False
            self.deny_button.disabled = False
            self.next_button.disabled = False

    async def post_approval_embed(self):
        channel = await self.bot.fetch_channel(BINGO_LOGS_CHANNEL)

        approval_embed = discord.Embed(
            title=f"Submission Approved", url=self.jump_url, color=0x00FF00
        )
        approval_embed.set_thumbnail(url=self.img_url)
        approval_embed.add_field(name="Team:", value=self.team)
        approval_embed.add_field(name="Player:", value=self.player)
        approval_embed.add_field(name="Approved on:", value=self.date)

        await channel.send(embed=approval_embed)

    async def post_deny_embed(self):
        channel = await self.bot.fetch_channel(BINGO_LOGS_CHANNEL)

        denial_embed = discord.Embed(
            title=f"Submission Denied", url=self.jump_url, color=0xFF0000
        )
        denial_embed.set_thumbnail(url=self.img_url)
        denial_embed.add_field(name="Team:", value=self.team)
        denial_embed.add_field(name="Player:", value=self.player)
        denial_embed.add_field(name="Denied on:", value=self.date)

        await channel.send(embed=denial_embed)
