from __future__ import annotations
import discord
from discord.interactions import Interaction
import discord.ui
import Queries
from Data import *

# TODO: show only non-completed tasks

class Tasks(discord.ui.View):

    current_page = 1
    separator = 10
    task = 1

    def __init__(
        self, user: discord.User | discord.Member, timeout: float = 60.0) -> None:
        super().__init__(timeout=timeout)
        self.user = user

    async def interaction_check(self, interaction: Interaction[discord.Client]) -> bool:
        if interaction.user == self.user:
            return True
        await interaction.response.send_message(
            f"The command was initiated by {self.user.mention}", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.delete()

    
    async def send(self, ctx):
        self.message = await ctx.send(view = self)
        await self.update_message(self.data)
    
    # TODO: move the logic from here to the button press
    
    async def create_embed(self, data):
        start_task, end_task = await Queries.get_unlocked_tasks()
        
        if start_task == 0 or end_task == 0:
            embed = discord.Embed(title="There are no tasks available at this time.")
            self.first_page_button.disabled = True
            self.prev_page_button.disabled = True
            self.last_page_button.disabled = True
            self.next_page_button.disabled = True
            return embed
        embed = discord.Embed(title="Battle Bingo Task List")
        # counts the tasks (for the bullet ordering)
        if start_task == 1:
            count = (self.current_page * self.separator) - 9
            print("start == 1, so count ==: " + str(count))
        else:
            count = ((self.current_page - 1) * 10) +  start_task
            print("start != 1, so count ==: " + str(count))        
        
        for i in range(0, self.separator):
            print(count)
            if count > end_task:
                self.last_page_button.disabled = True
                self.next_page_button.disabled = True
                return embed
            if start_task <= count <= end_task:
                embed.add_field(name=f"Task #{count}", value=task_list.get(count), inline=False)
                count += 1
                
        return embed
       

    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=await self.create_embed(data), view=self)

    def update_buttons(self):
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_page_button.disabled = True
        else:
            self.first_page_button.disabled = False
            self.prev_page_button.disabled = False
            
        if self.current_page == int(len(self.data) / self.separator) + 1:
            self.last_page_button.disabled = True
            self.next_page_button.disabled = True
        else:
            self.last_page_button.disabled = False
            self.next_page_button.disabled = False

    @discord.ui.button(label="|<", custom_id="first_page_button", style=discord.ButtonStyle.blurple)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1
        until_item = self.current_page * self.separator
        await self.update_message(self.data[:until_item])

    @discord.ui.button(label="<", custom_id="prev_page_button", style=discord.ButtonStyle.blurple)
    async def prev_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        until_item = self.current_page * self.separator
        from_item = until_item - self.separator
        await self.update_message(self.data[from_item:until_item])
        
    @discord.ui.button(label=">", custom_id="next_page_button", style=discord.ButtonStyle.blurple)
    async def next_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        until_item = self.current_page * self.separator
        from_item = until_item - self.separator
        await self.update_message(self.data[from_item:until_item])
        
    @discord.ui.button(label=">|", custom_id="last_page_button", style=discord.ButtonStyle.blurple)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = int(len(self.data) / self.separator) + 1
        until_item = self.current_page * self.separator
        from_item = until_item - self.separator
        await self.update_message(self.data[from_item:])