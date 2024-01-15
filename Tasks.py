from __future__ import annotations
import discord
import logging
import typing
from discord.interactions import Interaction
from discord.ui import View

from Utils import task_list

# TODO: show only non-completed tasks


class Tasks(discord.ui.View):
    message: discord.Message | None = None
    task = 0
    task_list_options = []

    def __init__(
        self, user: discord.User | discord.Member, timeout: float = 60.0) -> None:
        super().__init__(timeout=timeout)
        self.user = user

    # checks for views interactions
    async def interaction_check(self, interaction: Interaction[discord.Client]) -> bool:
        if interaction.user == self.user:
            return True
        await interaction.response.send_message(
            f"The command was initiated by {self.user.mention}", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True  # type: ignore
        if self.message:
            await self.message.edit(view=self)
    
    # populate task list
    # TODO: can task descriptions be truncated somehow?  they're awfully long
    for i in task_list:
        task_list_options.append(
            discord.SelectOption(
                label=f"Tile # {i}" ,
                value=i,
                description=f"Point Value: {task_list.get(i)[1]}",
                default=False,
            )
        )
    
    @discord.ui.select(
        placeholder="Select a Task",
        options=task_list_options[:9],
        custom_id="task_selection_component_tasks 1-9",
        min_values=1,
        max_values=1,
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.task = select.values[0]
        print("task: " + self.task)
        # BELOW FOR PRODUCTION!
        task_str = task_list.get(int(self.task))
        message = (
            "You selected Tile #"
            + self.task
            + ": "
            + task_str
            + "\nAre you sure you've picked the correct task?"
        )
        await interaction.response.send_message(message, ephemeral=True)


    @discord.ui.button(label="Submit", custom_id="submit_task_button", style=discord.ButtonStyle.green,)
    async def submit_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("You chose Tile #" + self.task + ".  Good luck gamer!",)