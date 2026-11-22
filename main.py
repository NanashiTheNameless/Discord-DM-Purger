import discord
from discord.ext import commands
import asyncio
import os
import sys
import time
from colorama import Fore, Style, init
from dotenv import load_dotenv

init(autoreset=True)
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN or TOKEN == "YOUR_TOKEN_HERE":
    sys.exit("DISCORD_TOKEN is not set. Copy .env.example to .env and add your token.")

# Optional: DM channel ID, Group DM channel ID, or user ID to purge without the interactive list.
DM_ID = os.getenv("DM_ID", "").strip()

client = discord.Client()

DEFAULT_DELAY = 0.5

def current_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def print_message(message, color=Fore.WHITE):
    print(f"{color}[{current_timestamp()}] {message}{Style.RESET_ALL}")

@client.event
async def on_ready():
    print_message(f"Logged in as {client.user}", Fore.GREEN)
    print_message("Do you want to Proceed with this account?", Fore.CYAN)
    
    choice = input(f"{Fore.GREEN}Enter your choice (Case sensitive, must be UPPERCASE Y/N): ").strip()

    if choice == "Y":
        await select_specific_dm()
    elif choice == "N":
        print_message("Okay, Exiting...", Fore.RED)
        await client.close()
    else:
        print_message("Invalid choice. Exiting...", Fore.RED)
        await client.close()

def find_dm_by_id(dms, target_id):
    for dm in dms:
        if dm.id == target_id:
            return dm
        if isinstance(dm, discord.DMChannel) and dm.recipient and dm.recipient.id == target_id:
            return dm
    return None

async def select_specific_dm():
    dms = client.private_channels

    if DM_ID:
        try:
            target_id = int(DM_ID)
        except ValueError:
            print_message(f"DM_ID in .env is not a valid ID: {DM_ID}", Fore.RED)
            await client.close()
            return

        selected_dm = find_dm_by_id(dms, target_id)
        if selected_dm is None:
            print_message(f"No DM or Group DM found matching ID {target_id}.", Fore.RED)
            await client.close()
            return

        dm_name = selected_dm.name if isinstance(selected_dm, discord.GroupChannel) else selected_dm.recipient
        print_message(f"Selected from .env: {dm_name} (ID: {selected_dm.id})", Fore.YELLOW)
    else:
        print_message("Fetching all DM channels...", Fore.CYAN)
        for index, dm in enumerate(dms, start=1):
            dm_name = dm.name if isinstance(dm, discord.GroupChannel) else dm.recipient
            print_message(f"{index}. {dm_name} (ID: {dm.id})", Fore.YELLOW)

        choice = input(f"{Fore.GREEN}Enter the number corresponding to the DM you want to clear: ").strip()
        try:
            selected_dm = dms[int(choice) - 1]
        except (IndexError, ValueError):
            print_message("Invalid input. Please enter a valid number.", Fore.RED)
            await client.close()
            return

    custom_delay_input = input(f"{Fore.GREEN}Do you want to set a custom delay for message deletions? (y/n): ").strip().lower()
    if custom_delay_input == "y":
        delay = input(f"{Fore.GREEN}Enter the delay (in seconds): ").strip()
        try:
            delay = float(delay)
            if delay <= 0:
                print_message("Invalid delay value. Using default delay.", Fore.YELLOW)
                delay = DEFAULT_DELAY
        except ValueError:
            print_message("Invalid delay input. Using default delay.", Fore.YELLOW)
            delay = DEFAULT_DELAY
    else:
        delay = DEFAULT_DELAY

    print_message(f"Using a delay of {delay} seconds for the selected DM.", Fore.GREEN)

    if isinstance(selected_dm, discord.DMChannel):
        await purge_user_dm(selected_dm, delay)
    elif isinstance(selected_dm, discord.GroupChannel):
        await purge_group_dm(selected_dm, delay)
    else:
        print_message("Invalid choice.", Fore.RED)

    await client.close()

async def purge_user_dm(dm, delay):
    try:
        print_message(f"Purging messages in DM with {dm.recipient}...", Fore.CYAN)
        async for message in dm.history(limit=None):
            if message.author == client.user:
                try:
                    await message.delete()
                    print_message("Deleted a message.", Fore.GREEN)
                except Exception as e:
                    print_message(f"Failed to delete a message: {e}", Fore.RED)
                await asyncio.sleep(delay)  # Customizable delay

        await dm.delete()
        print_message(f"Closed DM with {dm.recipient}.", Fore.GREEN)
    except Exception as e:
        print_message(f"Failed to process DM with {dm.recipient}: {e}", Fore.RED)

async def purge_group_dm(dm, delay):
    try:
        print_message(f"Purging messages in Group DM: {dm.name}...", Fore.CYAN)
        async for message in dm.history(limit=None):
            if message.author == client.user:
                try:
                    await message.delete()
                    print_message("Deleted a message.", Fore.GREEN)
                except Exception as e:
                    print_message(f"Failed to delete a message: {e}", Fore.RED)
                await asyncio.sleep(delay)  # Customizable delay

        await dm.leave()
        print_message(f"Left Group DM: {dm.name}.", Fore.GREEN)
    except Exception as e:
        print_message(f"Failed to process Group DM: {e}", Fore.RED)

client.run(TOKEN)
