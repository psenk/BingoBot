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
load_dotenv()

EMBED_ICON_URL = "https://shorturl.at/wGOXY"

class ApproveTasks(discord.ui.View):
    def __init__(self, ctx, timeout: float = 180.0) -> None:
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.current_page = 1

    def create_embed(self, data, index):
        if len(data) == 0:
            embed = discord.Embed(
                title="There are no submissions available for approval."
            )
            return embed

        (
            self.submission_id,
            self.task_id,
            self.url,
            self.channel_id,
            self.message_id,
            self.player,
            self.team,
            self.date,
        ) = self.data[index - 1]

        embed = discord.Embed(title=f"Submission # {self.submission_id}")
        # embed.set_thumbnail(url=self.url)

        embed.add_field(name="Task:", value=task_list.get(self.task_id), inline=False)
        embed.add_field(name="Submission:", value=f"[HERE]({self.url})", inline=True)
        embed.add_field(name="Player:", value=f"{self.player}", inline=True)
        embed.add_field(name="", value="", inline=True)
        embed.add_field(name="Team:", value=f"{self.team}", inline=True)
        embed.add_field(name="Date Submitted:", value=f"{self.date}", inline=True)
        embed.add_field(name="", value="", inline=True)

        return embed

    async def send(self, ephemeral: bool):
        self.message = await self.ctx.send(view=self, ephemeral=ephemeral)
        await self.update_message(self.data, 1)

    async def update_message(self, data, index):
        await self.update_buttons()
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
        label="Approve", custom_id="approve_button", style=discord.ButtonStyle.green
    )
    async def submit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()

        try:
            msg = await self.ctx.fetch_message(self.message_id)
            await msg.add_reaction("✅")
        except:
            pass

        await Queries.task_complete(self.team, self.task_id, self.player)
        await self.update_team_sheet(self.team, self.task_id, self.player, 2)
        await Queries.remove_submission(self.submission_id)
        await self.post_approval_embed()

        submissions = await Queries.get_submissions()
        self.current_page = 1
        await self.update_message(submissions, self.current_page)

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
        await interaction.response.defer()

        try:
            msg = await self.ctx.fetch_message(self.message_id)
            await msg.add_reaction("❌")
        except:
            pass

        await self.update_team_sheet(self.team, self.task_id, self.player, 3)
        await Queries.remove_submission(self.submission_id)
        await self.post_deny_embed()

        submissions = await Queries.get_submissions()
        self.current_page = 1
        await self.update_message(submissions, self.current_page)

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

        d = datetime.datetime.now()
        sheet = gc.open_by_key(GOOGLE_SHEETS_KEY)

        TASK_STATUS_COLUMN = 6
        TASK_DATE_COLUMN = 7
        cell_row = task + 1

        # Getting team specific sheet
        team_sheet = sheet.worksheet(team)

        # Updating task on team sheet
        if code == 1:
            team_sheet.update_cell(cell_row, TASK_STATUS_COLUMN, "Awaiting Approval")
            team_sheet.update_cell(cell_row, TASK_DATE_COLUMN, str(d))
            print(f"SHEETS: Updating task {task} for team {team}")
        elif code == 2:
            current_score = int(team_sheet.cell(4, 11).value)
            points = task_points.get(task)
            team_sheet.update_cell(cell_row, TASK_STATUS_COLUMN, "Complete")
            team_sheet.update_cell(cell_row, TASK_DATE_COLUMN, str(d))
            team_sheet.update_cell(4, 11, (current_score + points))
            print(f"SHEETS: Approving task {task} for team {team}")
        else:
            team_sheet.update_cell(cell_row, TASK_STATUS_COLUMN, "Incomplete")
            team_sheet.update_cell(cell_row, TASK_DATE_COLUMN, str(d))
            print(f"SHEETS: Denying task {task} for team {team}")

        history_sheet = sheet.worksheet("History")
        print("SHEETS: History recorded.")
        history_sheet.insert_row([player, team, task, code, str(d)], index=2)

    async def update_buttons(self):
        if len(self.data) == 0:
            self.prev_button.disabled = True
            self.submit_button.disabled = True
            self.deny_button.disabled = True
            self.next_button.disabled = True
        elif len(self.data) == 1:
            self.prev_button.disabled = True
            self.next_button.disabled = True
        elif self.current_page == 1:
            self.prev_button.disabled = True
            self.next_button.disabled = False
        elif self.current_page == len(self.data):
            self.next_button.disabled = True
            self.prev_button.disabled = False
        else:
            self.prev_button.disabled = False
            self.submit_button.disabled = False
            self.deny_button.disabled = False
            self.next_button.disabled = False

    async def post_approval_embed(self):
        # Creating the custom embed to track the submission
        approval_embed = discord.Embed(
            title=f"Submission Approved", url=self.url, color=0xFF0000
        )
        approval_embed.set_thumbnail(url=EMBED_ICON_URL)
        approval_embed.add_field(name="Team:", value=self.team)
        approval_embed.add_field(name="Player:", value=self.player)
        approval_embed.add_field(name="Approved on:", value=self.date)

        await self.ctx.send(embed=approval_embed)

    async def post_deny_embed(self):
        # Creating the custom embed to track the submission
        denial_embed = discord.Embed(
            title=f"Submission Denied", url=self.url, color=0xFF0000
        )
        denial_embed.set_thumbnail(url=EMBED_ICON_URL)
        denial_embed.add_field(name="Team:", value=self.team)
        denial_embed.add_field(name="Player:", value=self.player)
        denial_embed.add_field(name="Denied on:", value=self.date)

        await self.ctx.send(embed=denial_embed)
