import discord
from discord.ext import commands, tasks
import requests
import asyncio
from discord.ui import Button, View
from discord import PermissionOverwrite
import random
import json
import os
from datetime import datetime, timedelta

DISCORD_TOKEN = "MTMyNTE2Njc5ODk1NzcwNzM0NQ.GOQpeZ.ED4urGhimN6_H2YlHkbSQA6N3XwfXsfWVv-QGQ"  # use own bot token
API_KEY = "vivek"  # use own key name here
# BASE_URL = "https://likes.cloudenginecore.com/api/"
INFO_BASE_URL = "https://info.cloudenginecore.com/api/info"  # info apis
ALLOWED_CHANNEL_IDS = [1325162811214663710]  # use your allowed channel ids
ALLOWED_ROLE_ID = 1325167626368057405  # use allowed role id
ADMIN_USER_ID = 711623890438324296  # set admin user id
LOG_CHANNEL_ID = 1258226671891513428  # use log channel id

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

free_data = {"free_request_count": 0}
plan_data = {}
promote_data = {"message_id": None}  

def load_free_data():
    global free_data
    if os.path.exists("free_requests.json"):
        with open("free_requests.json", "r") as file:
            free_data = json.load(file)
    else:
        with open("free_requests.json", "w") as file:
            json.dump(free_data, file)

def save_free_data():
    with open("free_requests.json", "w") as file:
        json.dump(free_data, file)

def load_plan_data():
    global plan_data
    if os.path.exists("paid_plans.json"):
        with open("paid_plans.json", "r") as file:
            plan_data = json.load(file)
    else:
        with open("paid_plans.json", "w") as file:
            json.dump(plan_data, file)

def save_plan_data():
    with open("paid_plans.json", "w") as file:
        json.dump(plan_data, file)

def load_promote_data():
    global promote_data
    if os.path.exists("promote_data.json"):
        with open("promote_data.json", "r") as file:
            promote_data = json.load(file)
    else:
        with open("promote_data.json", "w") as file:
            json.dump(promote_data, file)

def save_promote_data():
    with open("promote_data.json", "w") as file:
        json.dump(promote_data, file)

def get_avatar_url(user: discord.User):
    return user.avatar.url if user.avatar else user.default_avatar.url

async def log_activity(message: str, title: str = "Bot Activity"):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title=title, description=message, color=discord.Color.blue())
        embed.set_footer(text=f"Logged by {bot.user.name}", icon_url=get_avatar_url(bot.user))
        await log_channel.send(embed=embed)

def check_permissions(ctx):
    if ctx.author.id == ADMIN_USER_ID:
        return True
    if ctx.channel.id not in ALLOWED_CHANNEL_IDS:
        return False
    role_ids = [role.id for role in ctx.author.roles]
    if ALLOWED_ROLE_ID not in role_ids:
        return False
    return True

@bot.event
async def on_ready():
    load_free_data()
    load_plan_data()
    load_promote_data()
    print(f"Bot is ready! Logged in as {bot.user}")
    await log_activity(f"Bot started and logged in as {bot.user.name}")
    # promote_paid_likes.start()

@bot.event
async def on_guild_join(guild):
    await log_activity(f"Joined a new server: {guild.name}")
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).create_instant_invite:
            invite = await channel.create_invite(max_age=0, max_uses=0)
            await log_activity(f"Invite link for {guild.name}: {invite.url}")
            break
    else:
        await log_activity(f"Could not create an invite link for {guild.name} (insufficient permissions).")
    activity = discord.Streaming(name="Bot Services Online", url="https://discord.gg/NvuAtQTqzN")
    await bot.change_presence(activity=activity)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id not in ALLOWED_CHANNEL_IDS:
        return
    await message.delete()
    await log_activity(f"Message from {message.author.name} deleted in {message.channel.name}")
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="Invalid Command",
            description="Oops! You entered an invalid command. Please use one of the following commands:",
            color=discord.Color.red()
        )
        #embed.add_field(name="â€¢ !cgkeyset <number>", value="Sets the free requests limit (Admin only).", inline=False)
       # embed.add_field(name="â€¢ !cgkeyreset", value="Clears all free requests data (Admin only).", inline=False)
       # embed.add_field(name="â€¢ !cglike <region> <player_id>", value="Sends likes to the specified player.", inline=False)
        embed.add_field(name="â€¢ !cgxinfo <region> <uid>", value="Fetches user information from the API.", inline=False)
       # embed.add_field(name="â€¢ !cgstatus", value="Checks the operational status of the bot (Admin only).", inline=False)
       # embed.add_field(name="â€¢ !addplan <discord_id> <daily_amount> <expiry_days>", value="Adds or updates a user's paid plan (Admin only).", inline=False)
       # embed.add_field(name="â€¢ !removeplan <discord_id>", value="Removes a user's paid plan (Admin only).", inline=False)
        embed.add_field(name="â€¢ !help", value="Displays the help message.", inline=False)
       # embed.add_field(name="â€¢ !clear <number>", value="Clear messages in bulk.", inline=False)
       # embed.add_field(name="â€¢ !lock", value="Lock the current channel.", inline=False)
      #  embed.add_field(name="â€¢ !unlock", value="Unlock the current channel.", inline=False)
        embed.set_footer(text=f"Logged by {bot.user.name}", icon_url=get_avatar_url(bot.user))
        await ctx.send(content=f"{ctx.author.mention}", embed=embed)
    await log_activity(f"Error occurred for {ctx.author.name}: {error}")

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="Bot Command Reference",
        description="Below is a a commands available for checking information:",
        color=discord.Color.blue()
    )
   # embed.add_field(name="â€¢ !cgkeyset <number>", value="Sets the free requests limit (Admin only).", inline=False)
   # embed.add_field(name="â€¢ !cgkeyreset", value="Clears all free requests data (Admin only).", inline=False)
   # embed.add_field(name="â€¢ !cglike <region> <player_id>", value="Sends likes to the specified player.", inline=False)
    embed.add_field(name="👉 !cgxinfo <region> <uid>", value="Fetches user information from the API.", inline=False)
   # embed.add_field(name="â€¢ !cgstatus", value="Checks the operational status of the bot (Admin only).", inline=False)
   # embed.add_field(name="â€¢ !addplan <discord_id> <daily_amount> <expiry_days>", value="Adds or updates a user's paid plan (Admin only).", inline=False)
   # embed.add_field(name="â€¢ !removeplan <discord_id>", value="Removes a user's paid plan (Admin only).", inline=False)
   # embed.add_field(name="â€¢ !help", value="Displays this help message.", inline=False)
   # embed.add_field(name="â€¢ !clear <number>", value="Clear messages in bulk.", inline=False)
   # embed.add_field(name="â€¢ !lock", value="Lock the current channel.", inline=False)
  #  embed.add_field(name="â€¢ !unlock", value="Unlock the current channel.", inline=False)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=get_avatar_url(ctx.author))
    await ctx.send(content=f"{ctx.author.mention}", embed=embed)
    await log_activity(f"Help command used by {ctx.author.name}")

# @bot.command(name="cgkeyset")
# async def set_free_requests(ctx, number: int):
#     if ctx.author.id != ADMIN_USER_ID:
#         await ctx.send(content=f"{ctx.author.mention} You don't have permission to use this command.")
#         return
#     free_data["free_request_count"] = number
#     save_free_data()
#     embed = discord.Embed(
#         title="Free Request Configuration",
#         description=f"The free requests limit is now set to {number}.",
#         color=discord.Color.blue()
#     )
#     embed.set_footer(text=f"Set by {ctx.author.name}", icon_url=get_avatar_url(ctx.author))
#     await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#     await log_activity(f"Free request limit set to {number} by {ctx.author.name}")

# @bot.command(name="cgkeyreset")
# async def reset_free_requests(ctx):
#     if ctx.author.id != ADMIN_USER_ID:
#         await ctx.send(content=f"{ctx.author.mention} You don't have permission to use this command.")
#         return
#     free_data["free_request_count"] = 0
#     save_free_data()
#     embed = discord.Embed(
#         title="Free Request Reset",
#         description="All free request data has been cleared.",
#         color=discord.Color.blue()
#     )
#     embed.set_footer(text=f"Reset by {ctx.author.name}", icon_url=get_avatar_url(ctx.author))
#     await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#     await log_activity(f"Free requests data cleared by {ctx.author.name}")

# @bot.command(name="addplan")
# async def add_plan(ctx, discord_id: int, daily_amount: int, expiry_days: int):
#     if ctx.author.id != ADMIN_USER_ID:
#         await ctx.send(content=f"{ctx.author.mention} You don't have permission to use this command.")
#         return
#     expiry_date = (datetime.now() + timedelta(days=expiry_days)).date().isoformat()
#     plan_data[str(discord_id)] = {
#         "daily_amount": daily_amount,
#         "expiry_date": expiry_date,
#         "used_today": 0,
#         "last_used_date": ""
#     }
#     save_plan_data()
#     embed = discord.Embed(
#         title="Plan Assigned/Updated",
#         description=f"Plan for <@{discord_id}>:\nDaily Amount: `{daily_amount}`\nExpiry Date: `{expiry_date}`",
#         color=discord.Color.green()
#     )
#     embed.set_footer(text=f"Set by {ctx.author.name}", icon_url=get_avatar_url(ctx.author))
#     await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#     await log_activity(f"Plan updated for {discord_id} by {ctx.author.name}")

# @bot.command(name="removeplan")
# async def remove_plan(ctx, discord_id: int):
#     if ctx.author.id != ADMIN_USER_ID:
#         await ctx.send(content=f"{ctx.author.mention} You don't have permission to use this command.")
#         return
#     if str(discord_id) in plan_data:
#         plan_data.pop(str(discord_id))
#         save_plan_data()
#         embed = discord.Embed(
#             title="Plan Removed",
#             description=f"Plan for <@{discord_id}> has been removed.",
#             color=discord.Color.green()
#         )
#         embed.set_footer(text=f"Removed by {ctx.author.name}", icon_url=get_avatar_url(ctx.author))
#         await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#         await log_activity(f"Plan removed for {discord_id} by {ctx.author.name}")
#     else:
#         await ctx.send(content=f"{ctx.author.mention} No plan found for that user.")

# def check_and_reset_plan_usage(discord_id):
#     if str(discord_id) in plan_data:
#         plan = plan_data[str(discord_id)]
#         expiry = datetime.fromisoformat(plan["expiry_date"])
#         if datetime.now().date() > expiry.date():
#             plan_data.pop(str(discord_id), None)
#             save_plan_data()
#             return None
#         if plan["last_used_date"] != datetime.now().date().isoformat():
#             plan["used_today"] = 0
#             plan["last_used_date"] = datetime.now().date().isoformat()
#             save_plan_data()
#         return plan
#     return None

# @bot.command(name="cglike")
# async def fetch_likes(ctx, region: str, player_id: str):
#     if not check_permissions(ctx):
#         embed = discord.Embed(
#             title="Access Denied",
#             description="âŒ You don't have the required role or permissions to use this command.",
#             color=discord.Color.red()
#         )
#         await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#         return
#     plan = check_and_reset_plan_usage(ctx.author.id)
#     has_free = (free_data["free_request_count"] > 0)
#     allowed_to_use = False
#     if has_free:
#         allowed_to_use = True
#     if plan:
#         if plan["used_today"] < plan["daily_amount"]:
#             allowed_to_use = True
#     if not allowed_to_use:
#         if has_free or plan:
#             embed = discord.Embed(
#                 title="Daily Limit Reached",
#                 description="âŒ You have reached your daily limit.",
#                 color=discord.Color.orange()
#             )
#             await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#         else:
#             embed = discord.Embed(
#                 title="No Subscription or Free Requests",
#                 description="âŒ Please contact an admin to purchase a subscription, or wait for free requests to be added.",
#                 color=discord.Color.orange()
#             )
#             await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#         return
#     processing_embed = discord.Embed(
#         title="Processing Request",
#         description="â³ Please wait while your request is being processed...",
#         color=discord.Color.blue()
#     )
#     waiting_message = await ctx.send(content=f"{ctx.author.mention}", embed=processing_embed)
#     try:
#         url = f"{BASE_URL}/{region}/{player_id}?key={API_KEY}"
#         headers = {"User-Agent": "DiscordBot/2.0"}
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()
#         data = response.json()
#         likes_given = data.get("likes_given", 100)
#         if plan and plan["used_today"] < plan["daily_amount"]:
#             plan["used_today"] += 1
#             save_plan_data()
#         elif free_data["free_request_count"] > 0:
#             free_data["free_request_count"] -= 1
#             save_free_data()
#         success_embed = discord.Embed(
#             title="âœ… Request Successful",
#             description=f"**{likes_given} likes** have been sent to the player.",
#             color=discord.Color.green()
#         )
#         success_embed.add_field(name="Player ID", value=player_id, inline=True)
#         success_embed.add_field(name="Region", value=region.upper(), inline=True)
#         success_embed.set_image(url="https://cdn.discordapp.com/attachments/1259879691028791419/1313123984732327948/221968.gif")
#         await waiting_message.edit(embed=success_embed)
#         await log_activity(f"Likes sent to {player_id} in {region} by {ctx.author.name}")
#     except requests.exceptions.RequestException:
#         error_messages = [
#             "âŒ This ID already received likes for today. Please try again tomorrow.",
#             "âŒ The API returned an error. Please try again later."
#         ]
#         error_message = random.choice(error_messages)
#         error_embed = discord.Embed(
#             title="Request Failed",
#             description=error_message,
#             color=discord.Color.red()
#         )
#         await waiting_message.edit(embed=error_embed)
#         await log_activity(f"Error in processing like request for {player_id} in {region} by {ctx.author.name}")
#     except Exception as e:
#         unexpected_error_embed = discord.Embed(
#             title="Unexpected Error",
#             description="âŒ An unexpected error occurred. Please try again later.",
#             color=discord.Color.red()
#         )
#         await waiting_message.edit(embed=unexpected_error_embed)
#         await log_activity(f"Unexpected error: {e}")

# @bot.command(name="cgstatus")
# async def check_status(ctx):
#     if ctx.author.id != ADMIN_USER_ID:
#         await ctx.send(content=f"{ctx.author.mention} You don't have permission to check the bot status.")
#         return
#     embed = discord.Embed(
#         title="Bot Status",
#         description="The bot is currently operational and running smoothly.",
#         color=discord.Color.green()
#     )
#     embed.add_field(name="Free Requests Remaining", value=free_data["free_request_count"], inline=False)
#     await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#     await log_activity(f"Bot status requested by {ctx.author.name}")

@bot.command(name="clear")
async def clear(ctx, amount: int):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="Access Denied",
            description="You don't have the required role or permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(content=f"{ctx.author.mention}", embed=embed)
        return
    if amount < 1 or amount > 100:
        await ctx.send(content=f"{ctx.author.mention} Please specify a number between 1 and 100.")
        return
    deleted = await ctx.channel.purge(limit=amount)
    embed = discord.Embed(
        title="Messages Cleared",
        description=f"{len(deleted)} messages have been cleared.",
        color=discord.Color.green()
    )
    await ctx.send(content=f"{ctx.author.mention}", embed=embed, delete_after=5)
    await log_activity(f"{len(deleted)} messages cleared by {ctx.author.name} in {ctx.channel.name}")

# @bot.command(name="lock")
# async def lock(ctx):
#     if not check_permissions(ctx):
#         embed = discord.Embed(
#             title="Access Denied",
#             description="You don't have the required role or permissions to use this command.",
#             color=discord.Color.red()
#         )
#         await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#         return
#     await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
#     embed = discord.Embed(
#         title="Channel Locked",
#         description="This channel has been locked. No new messages can be sent.",
#         color=discord.Color.red()
#     )
#     await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#     await log_activity(f"Channel locked by {ctx.author.name} in {ctx.channel.name}")

# @bot.command(name="unlock")
# async def unlock(ctx):
#     if not check_permissions(ctx):
#         embed = discord.Embed(
#             title="Access Denied",
#             description="You don't have the required role or permissions to use this command.",
#             color=discord.Color.red()
#         )
#         await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#         return
#     await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
#     embed = discord.Embed(
#         title="Channel Unlocked",
#         description="This channel has been unlocked. New messages can now be sent.",
#         color=discord.Color.green()
#     )
#     await ctx.send(content=f"{ctx.author.mention}", embed=embed)
#     await log_activity(f"Channel unlocked by {ctx.author.name} in {ctx.channel.name}")
    
@bot.command(name="cgxinfo")
async def user_info(ctx, region: str, uid: str):
    if not check_permissions(ctx):
        embed = discord.Embed(title="Access Denied", description="âŒ You don't have the required role or permissions to use this command.", color=discord.Color.red())
        await ctx.send(content=f"{ctx.author.mention}", embed=embed)
        return
    processing_embed = discord.Embed(title="Fetching User Information", description="🫸 Please wait while your request is being processed...", color=discord.Color.blue())
    waiting_message = await ctx.send(content=f"{ctx.author.mention}", embed=processing_embed)
    try:
        params = {
            "api_key": API_KEY,
            "region": region,
            "uid": uid
        }
        response = requests.get(INFO_BASE_URL, params=params, headers={"User-Agent": "DiscordBot/2.0"})
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"Status code: {response.status_code}")
        data = response.json()
        cloud_data = data.get("cloud_data", {})
        embed = discord.Embed(title="User Information", color=discord.Color.purple())
        for key, value in cloud_data.items():
            if isinstance(value, dict):
                sub_fields = "\n".join([f"**{sub_key}:** {sub_value}" for sub_key, sub_value in value.items()])
                embed.add_field(name=key, value=sub_fields if sub_fields else "None", inline=False)
            else:
                embed.add_field(name=key, value=str(value), inline=True)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=get_avatar_url(ctx.author))
        await waiting_message.edit(embed=embed)
        await log_activity(f"User info fetched for UID {uid} in region {region} by {ctx.author.name}")
    except requests.exceptions.HTTPError as http_err:
        error_embed = discord.Embed(title="Error", description=f"âŒ Failed to fetch user information. HTTP Error: {http_err}", color=discord.Color.red())
        await waiting_message.edit(embed=error_embed)
        await log_activity(f"HTTP error for UID {uid} in region {region} by {ctx.author.name}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        error_embed = discord.Embed(title="Error", description=f"âŒ Failed to fetch user information. Request Error: {req_err}", color=discord.Color.red())
        await waiting_message.edit(embed=error_embed)
        await log_activity(f"Request error for UID {uid} in region {region} by {ctx.author.name}: {req_err}")
    except Exception as e:
        unexpected_error_embed = discord.Embed(title="Unexpected Error", description="âŒ An unexpected error occurred. Please try again later.", color=discord.Color.red())
        await waiting_message.edit(embed=unexpected_error_embed)
        await log_activity(f"Unexpected error for UID {uid} in region {region} by {ctx.author.name}: {e}")

# @tasks.loop(minutes=60)
# async def promote_paid_likes():

#     channel = bot.get_channel(1325162811214663710)
 
#     old_message_id = promote_data.get("message_id")
#     if old_message_id:
#         try:
#             old_message = await channel.fetch_message(old_message_id)
#             await old_message.delete()
#         except discord.NotFound:
#             pass
#         except discord.DiscordException as e:
#             await log_activity(f"Error deleting old promote message: {e}")

#     embed = discord.Embed(
#         title="Get Paid Likes Now!",
#         description="Choose your plan to get paid likes and continue sending requests to players:",
#         color=discord.Color.blue()
#     )
#     embed.add_field(name="> 90 Rs", value="1 request daily", inline=False)
#     embed.add_field(name="> 180 Rs", value="3 requests daily", inline=False)
#     embed.add_field(name="> 250 Rs", value="5 requests daily", inline=False)
#     embed.add_field(name="> 500 Rs", value="Unlimited requests daily", inline=False)
#     embed.set_footer(text="Click below to create a ticket for assistance.")

#     ticket_button = Button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
#     view = View()
#     view.add_item(ticket_button)

#     msg = await channel.send(embed=embed, view=view)

#     promote_data["message_id"] = msg.id
#     save_promote_data()

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "create_ticket":
            user = interaction.user
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name="Gandu System")
            if category is None:
                category = await guild.create_category("Gandu System")
            overwrites = {
                guild.default_role: PermissionOverwrite(view_channel=False),
                user: PermissionOverwrite(view_channel=True)
            }
            ticket_channel = await guild.create_text_channel(f"ticket-{user.name}", category=category, overwrites=overwrites)
            embed = discord.Embed(title="Ticket Created", description=f"Hello {user.mention}, an admin will assist you shortly. Please wait for a response.", color=discord.Color.green())
            embed.set_footer(text="Your ticket will be handled by an admin.")
            close_button = Button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
            qr_button = Button(label="QR Code", style=discord.ButtonStyle.blurple, custom_id="send_qr_photo")
            binance_button = Button(label="Binance ID", style=discord.ButtonStyle.gray, custom_id="binance_id")
            view = View()
            view.add_item(close_button)
            view.add_item(qr_button)
            view.add_item(binance_button)
            await ticket_channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}.", ephemeral=True)
        elif interaction.data["custom_id"] == "send_qr_photo":
            photo_url = "https://cdn.discordapp.com/attachments/1213894010754695179/1346197436376285264/WhatsApp_Image_2024-07-23_at_22.26.45_64db9ea2.jpg?ex=67c74f8f&is=67c5fe0f&hm=72e80c65f738a1f77a3a02967289ee0c9f4361757cecd730daba52dbd3f2e7ab&"
            await interaction.response.send_message(content="Here's your QR Code:", ephemeral=False)
            await interaction.channel.send(photo_url)
        elif interaction.data["custom_id"] == "binance_id":
            await interaction.response.send_message(content=f"Your Binance ID: **NA**", ephemeral=False)
        elif interaction.data["custom_id"] == "close_ticket":
            if interaction.user.guild_permissions.manage_channels:
                ticket_channel = interaction.channel
                channel_name = ticket_channel.name
                messages = []
                async for msg in ticket_channel.history(oldest_first=True, limit=None):
                    messages.append(f"{msg.author} [{msg.created_at}]: {msg.content}")
                logs_filename = f"{ticket_channel.id}.txt"
                with open(logs_filename, "w", encoding="utf-8") as f:
                    for m in messages:
                        f.write(m + "\n")
                await interaction.response.send_message(f"Ticket `{channel_name}` has been closed and will be deleted shortly.", ephemeral=True)
                log_ch = bot.get_channel(LOG_CHANNEL_ID)
                if log_ch:
                    await log_ch.send(file=discord.File(logs_filename))
                if os.path.exists(logs_filename):
                    os.remove(logs_filename)
                await asyncio.sleep(1)
                await ticket_channel.delete()
            else:
                await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)

bot.run(DISCORD_TOKEN)
