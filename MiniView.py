import discord
import Queries
import gspread
import datetime
from Data import *
from discord.interactions import Interaction

TZ_OFFSET = -6.0
BINGO_LOGS_CHANNEL = 1195530905398284348
GOOGLE_SHEETS_KEY = "1lI7jSeyCPXFbA5eCRa8U77ClEQnBMXdud3OiIppH9A8"

tz_info = datetime.timezone(datetime.timedelta(hours=TZ_OFFSET))

class MiniView(discord.ui.View):
    
    def __init__(self, channel, user: discord.User | discord.Member, team, task_id, msg) -> None:
        super().__init__(timeout=None)
        self.channel = channel
        self.user = user
        self.team = team
        self.task_id = task_id
        self.msg = msg
        self.date = datetime.datetime.now()

    @discord.ui.button(label="Approve", custom_id="submit_button", style=discord.ButtonStyle.green)
    async def submit_button(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Approving submission...", delete_after=5.0)

        try:
            await self.msg.add_reaction("✅")
        except:
            print("Foki Bot: Message is not available to react to.")

        await Queries.task_complete(self.team, self.task_id, self.user.display_name)
        await Queries.remove_submission(self.task_id, self.team)
        await self.post_approval_embed()

        # LOG
        print("Foki Bot: Captain, a submission has been approved.")
        await self.update_buttons()
        await self.update_team_sheet(self.team, self.task_id, self.user.display_name, 2)

    @discord.ui.button(label="Deny", custom_id="deny_button", style=discord.ButtonStyle.red)
    async def deny_button(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Denying submission...",delete_after=5.0)
        
        try:
            await self.msg.add_reaction("❌")
        except:
            print("Foki Bot: Message is not available to react to.")

        await Queries.remove_submission(self.task_id, self.team)
        await self.post_deny_embed()

        # LOG
        print("Foki Bot: Captain, a submission has been DENIED.")
        await self.update_buttons()
        await self.update_team_sheet(self.team, self.task_id, self.user.display_name, 3)

    async def update_team_sheet(self, team: str, task: int, player: str, code: int):
        # CODES: 1 = Awaiting Approval, 2 = Complete, 3 = Incomplete
        gc = gspread.service_account(filename="service_account.json")

        d = datetime.datetime.now(tz_info)
        sheet = gc.open_by_key(GOOGLE_SHEETS_KEY)

        TASK_STATUS_COLUMN = 5
        TASK_DATE_COLUMN = 6
        cell_row = task + 1
        
        team = team.replace('\'', '')
        if len(team) > 5:
            team = team.title()
        # Getting team specific sheet
        team_sheet = sheet.worksheet(team)

        # Updating task on team sheet
        if code == 1:
            team_sheet.update_cell(cell_row, TASK_STATUS_COLUMN, "Awaiting Approval")
            team_sheet.update_cell(cell_row, TASK_DATE_COLUMN, str(d))
            print(f"SHEETS: Updating task {task} for team {team}")
        elif code == 2:
            current_score = int(team_sheet.cell(4, 10).value)
            if current_score is None:
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
        
    async def post_approval_embed(self):

        approval_embed = discord.Embed(
            title=f"Submission Approved", url=self.msg.jump_url, color=0x00FF00
        )
        approval_embed.set_thumbnail(url=self.msg.attachments[0].url)
        approval_embed.add_field(name="Team:", value=self.team)
        approval_embed.add_field(name="Player:", value=self.user.display_name)
        approval_embed.add_field(name="Task #:", value=self.task_id)
        if len(task_list) <= self.task_id <= (len(task_list) + 5):
            approval_embed.add_field(name="Task:", value=bonus_tasks.get(self.task_id))
        else:
            approval_embed.add_field(name="Task:", value=task_list.get(self.task_id)) 
        approval_embed.add_field(name="Approved on:", value=self.date, inline=False)

        await self.channel.send(embed=approval_embed)

    async def post_deny_embed(self):

        denial_embed = discord.Embed(
            title=f"Submission Denied", url=self.msg.jump_url, color=0xFF0000
        )
        denial_embed.set_thumbnail(url=self.msg.attachments[0].url)
        denial_embed.add_field(name="Team:", value=self.team)
        denial_embed.add_field(name="Player:", value=self.user.display_name)
        denial_embed.add_field(name="Task #:", value=self.task_id)
        if len(task_list) <= self.task_id <= (len(task_list) + 5):
            denial_embed.add_field(name="Task:", value=bonus_tasks.get(self.task_id))
        else:
            denial_embed.add_field(name="Task:", value=self.task_list.get(self.task_id)) 
        denial_embed.add_field(name="Denied on:", value=self.date, inline=False)

        await self.channel.send(embed=denial_embed)

    async def update_buttons(self):
        self.submit_button.disabled = True
        self.deny_button.disabled = True
        await self.message.edit(view=self)
