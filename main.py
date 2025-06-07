import typing
import discord
from discord.ext import commands,tasks
from discord.ui import View,Select,Button,Modal,TextInput
from discord import ButtonStyle, Interaction
import volt
import os
from dotenv import load_dotenv
from discord import app_commands
from random import randint
import pytz
import datetime
import re
import aiosqlite
import logging
from discord import AllowedMentions

logging.basicConfig(filename="bot.log",
                    filemode="a",
                    format="(%(asctime)s) | %(name)s | %(levelname)s => '%(message)s'",
                    datefmt="%d-%m-%Y, %I:%M %p")


the_global_guild=None

pr_id=1252362641976983724
tl_id=1252362480944939142
ed_id=1252362874609991701
rp_id=1258220209471230046

roles_id_dict={
    "translator":tl_id,
    "proofreader":pr_id,
    "editors":ed_id,
    "raw_provider":rp_id
}

management=1252357806070435882
guild_id=1252357504768147528
pending_raw=1322457811288064010
pending_tl=1322458037117648896
pending_pr=1322458122966663192
pending_ed=1322458165568339979
pending_up=1322458309264932864
pending_rp=1348579725831962646

claim_chapters_id=1322460838921109504

channels_id_dict={}



update_list=["Boom! Series Zapped into Perfection!","Success! The Series Now Obeys Your Whims!",
            "Kaboom! Details Sent to Another Dimension!","Mwahaha! Series Updated by Supreme Overlord!","Boom, baby! I blew it up—oh wait, no, I fixed it!",
            "KABLAMO! Your series got Jinxified!","Oopsie! I accidentally made it better. Or worse. You decide!",
            "I didn’t break it! I improved it! Big difference.","BOOMSHAKALAKA! I fixed your series! ...or destroyed it. Who cares?!",
            "Your boring ol’ series? Yeah, I spiced it up. Thank me later!","KA-POW! Your series begged for mercy, but I improved it anyway!",
            "I fixed your series. Fixed it GOOD! Like… really good. Trust me!"]

load_dotenv("TOKEN.env") 
TOKEN=os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_embed(title):
    embed=discord.Embed(title=title,color=0x9d0f87)
    embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
    return embed


def get_assign_embed(message):
    random=randint(0,len(update_list)-1)
    embed=discord.Embed(title=update_list[random],description=message,color=0x9d0f87)
    embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
    return embed

def get_mention_embed(message,raw_link,drive_link):
    embed=discord.Embed(title=message,color=0x9d0f87)
    embed.add_field(name="Raws Link",value=f"> {raw_link}")
    embed.add_field(name="Drive Link",value=f"> {drive_link}")
    embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
    return embed



def role_check(role_name):
    async def predicate(interaction: discord.Interaction):
        role = discord.utils.get(interaction.user.roles, name=role_name)
        if role:
            return True
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
        return False
    return app_commands.check(predicate)


def has_role(role_name):
    def predicate(interaction: discord.Interaction):
        # Check if the user has the required role
        user_roles = [role.name for role in interaction.user.roles]
        return role_name in user_roles
    return discord.app_commands.check(predicate)


async def get_members_with_role(guild, role_id):
    role = discord.utils.get(guild.roles, id=role_id) 
    
    if not role:
        return "Role not found."

    members_with_role = [member for member in guild.members if role in member.roles]

    if members_with_role:
        return members_with_role
    
    else:
        return "No members found with the specified role."


async def start_tasks():
    # Start the check_series_updates task
    if not check_series_updates.is_running():
        check_series_updates.start()

    # Start the update_pending_message task if it's not running
    if not update_pending_message.is_running():
        update_pending_message.start()

    # Start the check_deadline_time task
    if not check_deadline_time.is_running():
        check_deadline_time.start()

    if not update_pending_rp.is_running():
        update_pending_rp.start()

@bot.event
async def on_resumed():
    print("Bot Has Resumed Its Connection To Discord After Some Trouble.")
    # Restart tasks
    await start_tasks()       



@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game("With You"))
    await init_db()
    check_series_updates.start()
    update_pending_message.start()
    update_pending_rp.start()
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    print(f"Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")

    guilds=bot.guilds  
    for guild in guilds:

        if str(guild)=="My_Aowsome_Server":
            

            try:    
                global the_global_guild
                the_global_guild=guild
                print(f"cool {the_global_guild}")
                
            except Exception as e:
                print(f"Error syncing commands: {e}")
            else:
            
                volt.add_manhua(server=guild)
                await coco(target_channel=pending_tl,target_position="translate_st",job="send")
                await coco(target_channel=pending_pr,target_position="prof_st",job="send")
                await coco(target_channel=pending_ed,target_position="edit_st",job="send")
                await coco(target_channel=pending_up,target_position="upload_st",job="send")
    check_deadline_time.start()


@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.TextChannel):
        guild = channel.guild
        volt.add_manhua(guild)
        print("New Channel Is Added")

# add chapter
# ------------------------------------------------------------------------------------------------------------
@bot.tree.command(name="add_chapter",description="Add A New Chapter To The System")
@has_role("Management")
async def add_chapter(interaction: discord.Interaction,chapter_number:int):
    current_channel=interaction.channel.name
    current_cat=interaction.channel.category.name
    print(current_channel)

    raw_provider_role=discord.utils.get(interaction.guild.roles,name="Rp" )

    async with aiosqlite.connect('series.db') as db:
        try:
            cursor= await db.execute(f"select rp_money, pr_money, tl_money, ed_money from series where channel_id = {interaction.channel.id}")

            money_data=await cursor.fetchone()
        
        except Exception as e:
            print(e)

    if money_data:

        result=volt.add_chapter(current_channel,chapter_number, current_cat , interaction.guild.roles, money_data[0], money_data[2], money_data[1], money_data[3] )

        if result[0]=="0":
            await interaction.response.send_message(embed=get_embed(result[1:]))

        else:

            await interaction.response.send_message(f"{raw_provider_role.mention}",embed=get_embed(result),allowed_mentions=discord.AllowedMentions(roles=True))

    else:
        await interaction.response.send_message(embed=get_embed("Please Add The Series To The System Before Doing Any Action"),ephemeral=True)  

# ------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="rp",description="Provide The Raw")
@has_role("Rp")
async def rp(interaction: discord.Interaction,chapter_number:int):
    current_channel=interaction.channel.name
    current_cat=interaction.channel.category.name
    print(current_channel)

    result=volt.rp(current_channel,chapter_number,str(interaction.user),current_cat)

    translator_role="k-Translator"

    role = discord.utils.get(interaction.guild.roles,name=translator_role )

    assigned_tl=volt.get_assigned_translator(current_channel)

    if str(assigned_tl) != "None":
        assigned_tl=assigned_tl[0]
        mention_assign=discord.utils.get(interaction.guild.members,name=assigned_tl)


    if result[0]=="0":
        await interaction.response.send_message(embed=get_embed(result[1:]))
        
    else:
        try:
            await interaction.response.send_message(f"{mention_assign.mention}",embed=get_embed(result))
        except Exception:
            await interaction.response.send_message(f"{role.mention}",embed=get_embed(result),allowed_mentions=discord.AllowedMentions(roles=True))




import requests
@bot.tree.command(name="test",description="Provide The Raw")
async def test(interaction: discord.Interaction):
    id=443409689796018196
    user_avatar=bot.get_user(id).display_avatar
    page=requests.get(user_avatar)
    with open("soma avatar.jpg","wb") as f:
        f.write(page.content)
    
    await interaction.response.send_message(content=interaction.user)


@bot.tree.command(name="tldone",description="Inform About Translation Complete")
@has_role("k-Translator")
async def tldone(interaction: discord.Interaction,chapter_number:int):
    
    current_channel=interaction.channel.name
    current_cat=interaction.channel.category.name

    if volt.has_deadline_passed(current_channel,chapter_number,"tl_deadline"):
        await interaction.response.send_message(embed=get_embed("The Deadline Has Passed For This Chapter"))
    else:
        result=volt.tldone(current_channel,chapter_number,str(interaction.user),current_cat)
        proofreader_role="ProofReader"
        role = discord.utils.get(interaction.guild.roles,name=proofreader_role)

        assigned_pr=volt.get_assigned_proofreader(current_channel)

        if str(assigned_pr) != "None":
            assigned_pr=assigned_pr[0]
            mention_assign=discord.utils.get(interaction.guild.members,name=assigned_pr)

        if result[0]=="0":
            await interaction.response.send_message(embed=get_embed(result[1:]))

        elif result[0]=="x":
            await interaction.response.send_message(embed=get_embed(result[1:]),ephemeral=True)
            
        elif result[0]=="w":
            await interaction.response.send_message(embed=get_embed(result[1:]),ephemeral=True)

        else:
            try:
                await interaction.response.send_message(f"{mention_assign.mention}",embed=get_embed(result))
            except Exception:
                await interaction.response.send_message(f"{role.mention}",
                                                        embed=get_embed(result),
                                                        allowed_mentions=discord.AllowedMentions(roles=True))
                



@bot.tree.command(name="prdone",description="Inform About ProofReading Complete")
@has_role("ProofReader")
async def prdone(interaction: discord.Interaction,chapter_number:int):
    current_channel=interaction.channel.name
    current_cat=interaction.channel.category.name


    if volt.has_deadline_passed(current_channel,chapter_number,"pr_deadline"):
        await interaction.response.send_message(embed=get_embed("The Deadline Has Passed For This Chapter"))

    else:
        result=volt.prdone(current_channel,chapter_number,str(interaction.user),current_cat)
        editor_role="Editor"
        role = discord.utils.get(interaction.guild.roles,name=editor_role)

        assigned_ed=volt.get_assigned_editor(current_channel)


        if str(assigned_ed) != "None":
            assigned_ed=assigned_ed[0]
            mention_assign=discord.utils.get(interaction.guild.members,name=assigned_ed)


        if result[0]=="0":
            await interaction.response.send_message(embed=get_embed(result[1:]))
        elif result[0]=="w":
            await interaction.response.send_message(embed=get_embed(result[1:]))
        elif result[0]=="x":
            await interaction.response.send_message(embed=get_embed(result[1:]),ephemeral=True)
        else:
            try:
                await interaction.response.send_message(f"{mention_assign.mention}",embed=get_embed(result))
            except Exception:
                await interaction.response.send_message(f"{role.mention}",embed=get_embed(result),allowed_mentions=discord.AllowedMentions(roles=True))


@bot.tree.command(name="eddone",description="Inform About Editing Complete")
@has_role("Editor")
async def eddone(interaction: discord.Interaction,chapter_number:int):
    current_channel=interaction.channel.name


    bot

    if volt.has_deadline_passed(current_channel,chapter_number,"ed_deadline"):
        await interaction.response.send_message(embed=get_embed("The Deadline Has Passed For This Chapter"))
    else:

        up_role=discord.utils.get(interaction.guild.roles, id=1271010080556580884)

        result=volt.eddone(current_channel,chapter_number,str(interaction.user))
        uploader_role="uploader"
        role = discord.utils.get(interaction.guild.roles,name=uploader_role)
        if result[0]=="0":
            await interaction.response.send_message(embed=get_embed(result[1:]))
        elif result[0]=="w":
            await interaction.response.send_message(embed=get_embed(result[1:]))
        elif result[0]=="x":
            await interaction.response.send_message(embed=get_embed(result[1:]),ephemeral=True)
        else:
            await interaction.response.send_message(f"{up_role.mention}",
                                                    embed=get_embed(result),
                                                    allowed_mentions=discord.AllowedMentions(roles=True))




@bot.tree.command(name="udone",description="Inform About Uploading Complete")
@has_role("uploader")
async def udone(interaction: discord.Interaction,chapter_number:int):
    current_channel=interaction.channel.name

    result=volt.udone(current_channel,chapter_number,str(interaction.user))

    if result[0]=="0":
        await interaction.response.send_message(embed=get_embed(result[1:]))
    elif result[0]=="w":
        await interaction.response.send_message(embed=get_embed(result[1:]))
    elif result[0]=="x":
        await interaction.response.send_message(embed=get_embed(result[1:]),ephemeral=True)
    else:
        await interaction.response.send_message(embed=get_embed(result))

# -----------------------------------------------------------------------------------------------------
# payment method modal

class PaymentLinkModal(discord.ui.Modal):
    def __init__(self, payment_method):
        super().__init__(title=f"Enter Your {payment_method} Link")
        self.payment_method = payment_method
        self.add_item(
            discord.ui.TextInput(
                label=f"Your {payment_method} Link",
                placeholder=f"e.g., PayPal email, Binance ID, etc.",
                required=True
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        payment_link = self.children[0].value
        unique_name = interaction.user.name

        # Update the database with both the payment method and link
        volt.update_payment_info(unique_name, self.payment_method, payment_link)

        # Send a confirmation message
        await interaction.response.send_message(
            embed=get_embed(f"Your {self.payment_method} link has been updated!"),
            ephemeral=True
        )



# -----------------------------------------------------------------------------------------------------
# e-mail model
class EmailModal(Modal):
    def __init__(self):
        super().__init__(title="Email Update")

        # Add an InputText field for email
        self.add_item(TextInput(label="Email Address", placeholder="Example: yourname@example.com", required=True))

    async def on_submit(self, interaction: discord.Interaction):

        # Get the entered email
        email = self.children[0].value  

        # Get user unique name
        unique_name=interaction.user.name

        volt.update_email(unique_name,email)

        await interaction.response.send_message(f"Email updated to: {email}", ephemeral=True)

# -----------------------------------------------------------------------------------------------------
# Change BirthDay Modal

class ChangeBirthdayModal(Modal):
    def __init__(self):
        super().__init__(title="Birthday Setup")

        # Birth day input
        self.add_item(
            TextInput(
                label="Birth Day",
                placeholder="This is the day of your birthday (01-31)",
                required=True,
                min_length=1,
                max_length=2
            )
        )

        # Birth month input
        self.add_item(
            TextInput(
                label="Birth Month",
                placeholder="This is the month of your birthday (01-12)",
                required=True,
                min_length=1,
                max_length=2
            )
        )

        # Birth year input
        self.add_item(
            TextInput(
                label="Birth Year",
                placeholder="This is the year of your birthday (e.g., 2000)",
                required=True,
                min_length=4,
                max_length=4
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        unique_name=interaction.user.name
        day = self.children[0].value
        month = self.children[1].value
        year = self.children[2].value

        # Validate inputs (e.g., check valid day, month, year)
        try:
            day = int(day)
            month = int(month)
            year = int(year)

            if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                raise ValueError

            birthday=f"{day:02d}/{month:02d}/{year}"

            volt.update_birthday(unique_name,birthday)

            await interaction.response.send_message(
                embed=get_embed(f"Your Birthday Has Been Updated To: {birthday}"),
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                embed=get_embed("Invalid birthday input. Please try again."),
                ephemeral=True
            )

# -----------------------------------------------------------------------------------------------------
# Reset Statics Modal

class ResetStaticsModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Reset Statics")
        self.add_item(discord.ui.TextInput(
            label="Month",
            placeholder="Enter the month (e.g., January) OR Any Title For The Data",
            required=True
        ))
        self.add_item(discord.ui.TextInput(
            label="Year",
            placeholder="Enter the year (e.g., 2024)",
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        month = self.children[0].value
        year = self.children[1].value

        old_data_label=f"{month}-{year}"

        # Fetch current statics
        old_data = volt.fetch_archive_data()

        # Save old statics 
        try:
            volt.store_old_statics(old_data_label,old_data)
        except Exception as e:
            print(e)
            await interaction.response.send_message(
                embed=get_embed(f"Error Happend While Saving The Old Statics\nYou Can't Use The Same Name Twice")
            )
        else:
        # Reset statics in the database
            volt.reset_statics()


        # Send confirmation message
            await interaction.response.send_message(
                embed=get_embed(f"Statics For {month}-{year} Have Been Saved And Reset."),
                ephemeral=True
            )


# -----------------------------------------------------------------------------------------------------
# /profile section
@bot.tree.command(name="profile",description="Shows The The Member Profile")
async def profile(interaction: discord.Interaction):
    username=interaction.user.display_name
    unique_username=interaction.user.name
    view = ProfileView(username,unique_username,interaction)
    await interaction.response.send_message(embed=view.main_embed,view=view,ephemeral=True)

# ------------------------------------------------------------------------------------------------------
# profile buttons class

class ProfileView(View):
    def __init__(self,username:str,unique_username:str, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.username=username
        self.unique_username=unique_username
        self.main_embed = self.create_main_embed(username)
        self.interaction = interaction

    def create_main_embed(self,username:str):
        embed = discord.Embed(title="Profile Overview", description=f"Good evening, {username}.",color=0x9d0f87)
        profile_data=volt.profile(username)
        embed.add_field(name="Earnings this month", value=f"${profile_data[1]}", inline=True)
        embed.add_field(name="Chapters done this month", value=profile_data[0], inline=True)     
        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
        return embed


    @discord.ui.button(label="Chapters Overview", style=discord.ButtonStyle.green)
    async def chapters_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=self.create_chapters_embed(self.unique_username), view=ChaptersView(self))

    @discord.ui.button(label="Finances", style=discord.ButtonStyle.green)
    async def finances_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=self.create_finances_embed(self.unique_username), view=FinancesView(self))

    @discord.ui.button(label="Assigned Series", style=discord.ButtonStyle.blurple)
    async def assigned_series_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=self.create_assigned_series_embed(self.unique_username), view=AssignedView(self))


    @discord.ui.button(label="Pending", style=discord.ButtonStyle.blurple)
    async def pending_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=self.create_pending_embed(self.username,self.unique_username), view=PendingView(self))


    @discord.ui.button(label="Pesonal Info", style=discord.ButtonStyle.red)
    async def personal_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=self.create_personal_embed(self.username), view=PersonalInfoView(self))

# Management Section
# ----------------------------------------------------------------------------------------------------------------------------------

    @discord.ui.button(label="Management", style=discord.ButtonStyle.gray)
    async def management_button(self, interaction: discord.Interaction, button: Button):
        if any(role.name.lower() == "management" for role in interaction.user.roles):
            await interaction.response.edit_message(embed=self.create_management_embed(), view=ManagementView(self))
        else:
            await interaction.response.send_message("You do not have permission to access this.", ephemeral=True)

# ----------------------------------------------------------------------------------------------------------------------------------

    def create_chapters_embed(self, unique_name: str):
        embed = discord.Embed(title="Chapters Overview", description=f"Your Chapter Statistics for {unique_name}", color=0x9d0f87)

        results = volt.chapters_overview(unique_name)

        if not results:
            embed.add_field(name="No Data", value="You haven't worked on any chapters yet!", inline=False)
        else:
            chunks = []
            temp_chunk = ""

            for key, value in results.items():
                chapter_list = ", ".join(str(chap) for chap in value) 
                entry = f"📖 **{key.title()}**\nChapters Done: {chapter_list}\n{'-'*30}\n"

                if len(temp_chunk) + len(entry) > 1024:
                    chunks.append(temp_chunk)
                    temp_chunk = entry
                else:
                    temp_chunk += entry

            if temp_chunk:
                chunks.append(temp_chunk)

            for i, chunk in enumerate(chunks):
                embed.add_field(name=f"Page {i+1}", value=chunk, inline=False)

        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
        return embed

    def create_finances_embed(self,unique_username:str):
        finaces_report=volt.get_finaces_details(unique_username)
        embed = discord.Embed(title="Finances Report",color=0x9d0f87)
        for key, value in finaces_report.items():
            embed.add_field(name=key,value=f"> {value}")

        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")

        return embed

    def create_assigned_series_embed(self,username:str):
        embed = discord.Embed(title="Assigned Series",color=0x9d0f87)
        user_data=volt.get_assigned_series(username)
        
        for key, value in user_data.items():
            value=list(value)
            channel=bot.get_channel(value[-1])
            value[-1]=channel.category            
            value_str = "\n".join(f"> ● {str(data)}" for data in value if data)
            embed.add_field(name=str(key).title(),value=value_str,inline=False)

        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
        return embed

    def create_schedule_embed(self,username:str):
        embed = discord.Embed(title="Schedule")
        embed.add_field(name="Total Earnings", value="sc")
        embed.add_field(name="Pending Payments", value="sc")
        return embed

    def create_pending_embed(self,username:str,unique_username:str):
        for channel in bot.get_guild(1252357504768147528).channels:
            channels_id_dict.update({channel.name:channel.id})
    
        result=volt.get_profile_pending(unique_username)
        embed = discord.Embed(title="🕒 Pending Chapters",color=0x9d0f87)
        for key, value in result.items():
            channel_link= f"<#{channels_id_dict[key]}>"

            for v in value[:-1]:
                embed.add_field(name=f"{key.title()} | Chapter {v[0]}",value=f"> Job: {value[-1][0:2].title()}\n> {channel_link}",inline=False)


        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
        return embed

    def create_personal_embed(self, username: str):
        embed = discord.Embed(
            title="Personal Info", 
            description="You may edit any of your personal information by clicking on the buttons below.", 
            color=0x9d0f87
        )
        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
        return embed
    

    def create_management_embed(self):
        embed = discord.Embed(
            title="Management Panel",
            description="Welcome to the management panel. Use the buttons below to manage bonuses and penalties.",
            color=0x9d0f87
        )
        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
        return embed
    

class ReturnButton(View):
    def __init__(self, profile_view: ProfileView):
        super().__init__(timeout=None)
        self.profile_view = profile_view

    @discord.ui.button(label="Return", style=discord.ButtonStyle.red)
    async def return_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=self.profile_view.main_embed, view=self.profile_view)


class ChaptersView(ReturnButton):
    pass  # Inherits the "Return" button functionality


class FinancesView(ReturnButton):
    pass  # Inherits the "Return" button functionality

class AssignedView(ReturnButton):
    pass  # Inherits the "Return" button functionality

class ScheduleView(ReturnButton):
    pass  # Inherits the "Return" button functionality

class PendingView(ReturnButton):
    pass  # Inherits the "Return" button functionality


# Management Button Section
# ----------------------------------------------------------------------------------------------------------

class ManagementView(ReturnButton):
    def __init__(self, profile_view: ProfileView):
        super().__init__(profile_view)
        self.profile_view = profile_view

    @discord.ui.button(label="Show Statics", style=discord.ButtonStyle.blurple)
    async def statics_button(self, interaction: discord.Interaction, button: Button):
        result=volt.get_management_info()

        embed=discord.Embed(title="📊 Members Statics",color=0x9d0f87)

        chunks = []
        temp_chunk = ""

        print(result)
        for member in result:
            entry = f"👤 Name: **``{member[0]}``**\n💰 Total Money: **``{member[1]} $``**\n💱 Payment Method: **``{member[2]}``**\n🔗 Payment Link: **``{member[3]}``**\n{'-'*30}\n"
            
            if len(temp_chunk) + len(entry) > 1024:
                chunks.append(temp_chunk)
                temp_chunk = entry
            else:
                temp_chunk += entry
        if temp_chunk:
            chunks.append(temp_chunk)

        for i, chunk in enumerate(chunks):
            embed.add_field(name=f"Page {i+1}", value=chunk, inline=False)

        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")

        view = discord.ui.View()
        print_button = discord.ui.Button(label="Print", style=discord.ButtonStyle.green)


        async def print_callback(interaction: discord.Interaction):

            headers = ["Name", "Total Money", "Payment Method", "Payment Link"]
            
            csv_bytes = volt.generate_csv_file(headers, result)
            
            await interaction.response.send_message(
                embed=get_embed("Here is the CSV file for current statics:"),
                file=discord.File(csv_bytes, filename="current_statics.csv"),
                ephemeral=True
            )

        print_button.callback = print_callback
        view.add_item(print_button)

        await interaction.response.send_message(embed=embed,view=view, ephemeral=True)

# ------------------------------------------------------------------------
    @discord.ui.button(label="Show Old Statics", style=discord.ButtonStyle.green)
    async def show_old_statics_button(self, interaction: discord.Interaction, button: Button):
        old_statics_tables = volt.get_old_statics_tables()
        
        if not old_statics_tables:
            await interaction.response.send_message(
                embed=get_embed("No old statics found."),
                ephemeral=True
            )
            return

        select = discord.ui.Select(
            placeholder="Choose a statics table to view",
            options=[
                discord.SelectOption(label=table, value=table) for table in old_statics_tables
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            selected_table = select.values[0]
            statics_data = volt.get_old_statics_data(selected_table)
            
            # Create an embed to display the statics
            embed = discord.Embed(title=f"📊 Old Statics: {selected_table}", color=0x9d0f87)
            
            chunks = []
            temp_chunk = ""
            for member in statics_data:
                entry = f"👤 Name: **``{member[0]}``**\n💰 Total Money: **``{member[1]} $``**\n💱 Payment Method: **``{member[2]}``**\n🔗 Payment Link: **``{member[3]}``**\n{'-'*30}\n"
                
                if len(temp_chunk) + len(entry) > 1024:
                    chunks.append(temp_chunk)
                    temp_chunk = entry
                else:
                    temp_chunk += entry
            if temp_chunk:
                chunks.append(temp_chunk)

            for i, chunk in enumerate(chunks):
                embed.add_field(name=f"Page {i+1}", value=chunk, inline=False)

            embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")

            view = discord.ui.View()
            print_button = discord.ui.Button(label="Print", style=discord.ButtonStyle.green)

            async def print_callback(interaction: discord.Interaction):

                csv_file = volt.generate_csv_file(["Name","Total Money","Payment Method","Payment Link"], statics_data)
                
                # Send the CSV file to the user
                await interaction.response.send_message(
                    embed=get_embed(f"Here Is The CSV File For {selected_table} :"),
                    file=discord.File(csv_file, filename=f"{selected_table}.csv"),
                    ephemeral=True
                )

            print_button.callback = print_callback
            view.add_item(print_button)

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        select.callback = select_callback

        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message(
            embed=get_embed("Select A Statics Table To View:"),
            view=view,
            ephemeral=True
        )

# ------------------------------------------------------------------------
# Reset Statics Button

    @discord.ui.button(label="Reset Statics", style=discord.ButtonStyle.red)
    async def reset_statics_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ResetStaticsModal())

# Personal Info Section
# ------------------------------------------------------------------------

class PersonalInfoView(ReturnButton):
    def __init__(self, profile_view: ProfileView):
        super().__init__(profile_view)
        self.profile_view = profile_view

    @discord.ui.button(label="Email", style=discord.ButtonStyle.blurple)
    async def change_email_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(EmailModal())

    @discord.ui.button(label="Change Pay Method", style=discord.ButtonStyle.blurple)
    async def change_pay_button(self, interaction: discord.Interaction, button: Button):
        select = discord.ui.Select(
            placeholder="Choose Your Payment Method",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="TRC 20", value="TRC 20"),
                discord.SelectOption(label="Binance ID", value="binance id"),
                discord.SelectOption(label="PayPal", value="paypal"),
                discord.SelectOption(label="Others", value="others"),
            ],
        )
        unique_name=interaction.user.name

        async def select_callback(interaction: discord.Interaction):
            selected_value = select.values[0]  


            modal = PaymentLinkModal(selected_value)
            await interaction.response.send_modal(modal)

        
        select.callback = select_callback
        await interaction.response.send_message(embed=get_embed("Please Select A Payment Method:"), view=discord.ui.View.add_item(self=self,item=select), ephemeral=True)


    @discord.ui.button(label="Change Birthday", style=discord.ButtonStyle.blurple)
    async def change_birthday_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ChangeBirthdayModal())
        
    

async def coco(target_channel=None, target_position=None, job=None):
    pending_chapters = volt.get_pending(target_position)

    position_name = target_position.split("_")[0].capitalize()
    if position_name == "Prof":
        embed = discord.Embed(title="<:bota:1324056312014962709> All Proofread Pending Chapters", color=0x9d0f87)
    else:
        embed = discord.Embed(title=f"<:bota:1324056312014962709> All {position_name} Pending Chapters", color=0x9d0f87)

    my_hive=bot.get_guild(1252357504768147528)

    for key, value in pending_chapters.items():
        for pending_chapter in value:
            channel = discord.utils.get(my_hive.channels, name=key)
            
            if channel is None:
                print(f"Channel '{key}' not found in guild")
                continue
            
            category_name = getattr(channel.category, "name", "No Category")
            
            if target_position != "upload_st":
                remaining_hours, remaining_minutes = volt.get_remaining_deadline(key, pending_chapter[0], target_position)
                if remaining_hours ==0 and remaining_minutes==0:
                    embed.add_field(
                        name=f"{key} | Chapter {pending_chapter[0]}",
                        value=f"> 👤 {category_name}\n> #️⃣ {channel.mention}\n> 🕒 Remaining Time: ~~**``{remaining_hours} Hrs And {remaining_minutes} Min.``**~~",
                        inline=False
                    )
                
                else:
                    embed.add_field(
                        name=f"{key} | Chapter {pending_chapter[0]}",
                        value=f"> 👤 {category_name}\n> #️⃣ {channel.mention}\n> 🕒 Remaining Time: **``{remaining_hours} Hrs And {remaining_minutes} Min.``**",
                        inline=False
                    )

            else:
                embed.add_field(
                    name=f"{key} | Chapter {pending_chapter[0]}",
                    value=f"> 👤 {category_name}\n> #️⃣ {channel.mention}",
                    inline=False
                )
    
    embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
    
    if job == "send":
        channel = bot.get_channel(target_channel)
        if channel:
            await channel.send(embed=embed)
    elif job == "edit":
        return embed

# ---------------------------------------------------------------------------------------------------------------
# Alternative loop:

@tasks.loop(seconds=59)
async def update_pending_message():
    print("Updating The Pending Message...")
    
    for pending_channel, target_position in zip([pending_tl, pending_pr, pending_ed, pending_up], ["translate_st", "prof_st", "edit_st", "upload_st"]):
        channel = bot.get_channel(pending_channel)
        
        try:
            await channel.purge()
        except Exception as e:
            print(f"Error deleting bot's last message in channel {channel.name}: {e}")
            continue 
        new_embed = await coco(target_channel=pending_channel, target_position=target_position, job="edit")
        await channel.send(embed=new_embed)

# ---------------------------------------------------------------------------------------------------------------
@tasks.loop(seconds=59)
async def update_pending_rp():
    print("Updating The Pending RP Message...")

    pending_chapters=volt.get_rp_pending()

    embed = discord.Embed(title="<:bota:1324056312014962709> All RP Pending Chapters", color=0x9d0f87)
    my_hive=bot.get_guild(1252357504768147528)

    for key, value in pending_chapters.items():
        for pending_chapter in value:
            channel = discord.utils.get(my_hive.channels, name=key)
            
            if channel is None:
                print(f"Channel '{key}' not found in guild")
                continue
            
            category_name = getattr(channel.category, "name", "No Category")
            
            embed.add_field(
                name=f"{key} | Chapter {pending_chapter[0]}",
                value=f"> 👤 {category_name}\n> #️⃣ {channel.mention}\n",
                inline=False
            )
        

    embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")
    
    pending_rp_channel= bot.get_channel(pending_rp)
    
    try:
        await pending_rp_channel.purge()
    except Exception as e:
        print(f"Error deleting bot's last message in channel {channel.name}: {e}")

    await pending_rp_channel.send(embed=embed)

# ---------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="assign_tl",description="Assign The Translator For The Manhaua")
@has_role("Management")
async def assign_tl(interaction:discord.Interaction,tl:str):
    guild=interaction.guild
    current_channel=interaction.channel.name
    member=guild.get_member_named(tl)
    
    result=volt.assign_tl(current_channel,member.name,member.global_name)
    await interaction.response.send_message(member.mention,embed=get_assign_embed(result))


@assign_tl.autocomplete("tl")
async def tl_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    result= await get_members_with_role(interaction.guild,1252362480944939142)
    data=[]
    for member in result :
        if current.lower() in member.display_name.lower():
            data.append(app_commands.Choice(name=member.display_name,value=member.display_name))
    return data



@bot.tree.command(name="assign_pr",description="Assign The Proofreader For The Manhaua")
@has_role("Management")
async def assign_pr(interaction:discord.Interaction,pr:str):
    guild=interaction.guild
    current_channel=interaction.channel.name
    member=guild.get_member_named(pr)
    result=volt.assign_pr(current_channel,member.name,member.global_name)
    await interaction.response.send_message(member.mention,embed=get_assign_embed(result))


@assign_pr.autocomplete("pr")
async def pr_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    result= await get_members_with_role(interaction.guild,1252362641976983724)
    data=[]
    for member in result :
        if current.lower() in member.display_name.lower():
            data.append(app_commands.Choice(name=member.display_name,value=member.display_name))
    return data




@bot.tree.command(name="assign_ed",description="Assign The Editor For The Manhaua")
@has_role("Management")
async def assign_ed(interaction:discord.Interaction,ed:str):
    guild=interaction.guild
    current_channel=interaction.channel.name
    member=guild.get_member_named(ed)
    result=volt.assign_ed(current_channel,member.name,member.global_name)
    await interaction.response.send_message(member.mention,embed=get_assign_embed(result))


@assign_ed.autocomplete("ed")
async def pr_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    result= await get_members_with_role(interaction.guild,1252362874609991701)
    data=[]
    for member in result :
        if current.lower() in member.display_name.lower():
            data.append(app_commands.Choice(name=member.display_name,value=member.display_name))
    return data



# Bounus Section
# ---------------------------------------------------------------------------------------------------------------
@bot.tree.command(name="add_bonus",description="Add A Bonus To A Member")
@has_role("Management")
async def add_bonus(interaction:discord.Interaction,member:str,bonus:float):
    guild=interaction.guild
    result=volt.add_bonus(member,bonus)  
    await interaction.response.send_message(embed=get_embed(result),ephemeral=True)  



@add_bonus.autocomplete("member")
async def bonus_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    result=volt.get_members()
    data=[]
    for member in result:
        if current.lower() in member.lower():
            data.append(app_commands.Choice(name=member,value=member))

    return data[:25]
        


# Penalty Section
# ---------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="add_penalty",description="Add A Penalty To A Member")
@has_role("Management")
async def add_penalty(interaction:discord.Interaction,member:str,penalty:float):
    guild=interaction.guild
    result=volt.add_penalty(member,penalty)  
    await interaction.response.send_message(embed=get_embed(result),ephemeral=True)  



@add_penalty.autocomplete("member")
async def penalty_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    result=volt.get_members()
    data=[]
    for member in result:
        if current.lower() in member.lower():
            data.append(app_commands.Choice(name=member,value=member))
    return data[:25]

# ---------------------------------------------------------------------------------------------------------------

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


# ===========================================================================================================
# Mention Part

K_TRANSLATOR_ROLE_ID = 1252362480944939142
PROOFREADER_ROLE_ID = 1252362641976983724
EDITOR_ROLE_ID = 1252362874609991701
UPLOADER_ROLE_ID = 1271010080556580884
WITH_RAW_CATEGORY_ID = 1252368633758220391
PENDING_SERIES_CATEGORY_ID = 1258522852462694400

async def init_db():
    async with aiosqlite.connect('series.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                day TEXT NOT NULL,
                time TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                site TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                raw_link string,
                drive_link string,
                
                rp_money float,
                tl_money float,
                pr_money float,
                ed_money float
                                
            )
        ''')
        await db.commit()

DAYS_OPTIONS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def is_valid_time(time_str):
    return bool(re.match(r'^(?:0[1-9]|1[0-2]):[0-5]\d (AM|PM)$', time_str))

def format_time_12_hour(dt):
    return dt.strftime('%I:%M %p')

async def get_series_options():
    async with aiosqlite.connect('series.db') as db:
        async with db.execute('SELECT role_id FROM series') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        

# ---------------------------------------------------------------------------------------------

@bot.tree.command(name="add_series",description="Add A New Series")
@has_role("Management")
async def add_series(
    interaction: discord.Interaction,
    day: str,
    time: str,
    channel: discord.TextChannel,
    role: discord.Role,
    site: str ,
    raw_link:str,
    drive_link:str,

    rp_money:float,
    tl_money:float,
    pr_money:float,
    ed_money:float
):
    print(discord.Role)
    if not is_valid_time(time):
        await interaction.response.send_message("Invalid time format. Please use 12-hour format with AM/PM (e.g., 01:00 PM).", ephemeral=True)
        return

    async with aiosqlite.connect('series.db') as db:
        await db.execute('INSERT INTO series (name, day, time, channel_id, role_id, site,raw_link,drive_link, rp_money,tl_money,pr_money,ed_money) VALUES (?, ?, ?, ?, ?, ?,?,?, ?, ?, ?, ? )',
                        (role.name, day, time, channel.id, role.id, site,raw_link,drive_link, rp_money,tl_money,pr_money,ed_money))
        await db.commit()
        await interaction.response.send_message(f"Series '{role.name}' added successfully.")
        await channel.send(f"New series '{role.name}' has been added. Notifications will be sent at {site} time every {day} ")


@add_series.autocomplete("day")
async def tl_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    data=[]
    for day in DAYS_OPTIONS :
        if current.lower() in day.lower():
            data.append(app_commands.Choice(name=day,value=day))
    return data

@add_series.autocomplete("site")
async def tl_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    data=[]
    for site in ["Naver","Kakao","Others"] :
        if current.lower() in site.lower():
            data.append(app_commands.Choice(name=site,value=site))
    return data

# -----------------------------------------------------------------------------------------------------

@bot.tree.command(name="delete_series",description="Delete A Series")
@has_role("Management")
async def delete_series(
    interaction: discord.Interaction,
    role: discord.Role
):
    async with aiosqlite.connect('series.db') as db:
        await db.execute('DELETE FROM series WHERE role_id = ?', (role.id,))
        await db.commit()
        await interaction.response.send_message(f"Series '{role.name}' deleted successfully.")

# -----------------------------------------------------------------------------------------------------

@bot.tree.command(name="update_series",description="Update A Series")
@has_role("Management")
async def update_series(
    interaction: discord.Interaction,
    role: discord.Role,
    day: str,
    time: str,
    channel: discord.TextChannel,
    site: str,
    enabled: str,
    raw_link:str,
    drive_link:str,

    rp_money:float,
    tl_money:float,
    pr_money:float,
    ed_money:float
):

    async with aiosqlite.connect('series.db') as db:
        if day:
            await db.execute('UPDATE series SET day = ? WHERE role_id = ?', (day, role.id))
        if time and is_valid_time(time):
            await db.execute('UPDATE series SET time = ? WHERE role_id = ?', (time, role.id))
        if channel:
            await db.execute('UPDATE series SET channel_id = ? WHERE role_id = ?', (channel.id, role.id))
        if site:
            await db.execute('UPDATE series SET site = ? WHERE role_id = ?', (site, role.id))
        if raw_link:
            await db.execute('UPDATE series SET raw_link = ? WHERE role_id = ?', (raw_link, role.id))
        if drive_link:
            await db.execute('UPDATE series SET drive_link = ? WHERE role_id = ?', (drive_link, role.id))

        if rp_money:
            await db.execute("update series set rp_money = ? where role_id= ?",(rp_money,role.id))
        if tl_money:
            await db.execute("update series set tl_money = ? where role_id= ?",(tl_money,role.id))
        if pr_money:
            await db.execute("update series set pr_money = ? where role_id= ?",(pr_money,role.id))
        if ed_money:
            await db.execute("update series set ed_money = ? where role_id= ?",(ed_money,role.id))


        if enabled == "True":
            await db.execute('UPDATE series SET enabled = ? WHERE role_id = ?', (1, role.id))
        elif enabled == "False":
            await db.execute('UPDATE series SET enabled = ? WHERE role_id = ?', (0, role.id))
        
        await db.commit()
        await interaction.response.send_message(f"Series associated with role '{role.name}' updated successfully.")

@update_series.autocomplete("day")
async def tl_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    data=[]
    for day in DAYS_OPTIONS :
        if current.lower() in day.lower():
            data.append(app_commands.Choice(name=day,value=day))
    return data

@update_series.autocomplete("site")
async def tl_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    data=[]
    for site in ["Naver","Kakao","Others"] :
        if current.lower() in site.lower():
            data.append(app_commands.Choice(name=site,value=site))
    return data


@update_series.autocomplete("enabled")
async def tl_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    data=[]
    for site in ["True","False"] :
        if current.lower() in site.lower():
            data.append(app_commands.Choice(name=site,value=site))
    return data

# -----------------------------------------------------------------------------------------------------

@bot.tree.command(name="series_list",description="List All Series")
@has_role("Management")
async def series_list(interaction: discord.Interaction):
    async with aiosqlite.connect('series.db') as db:
        async with db.execute('SELECT name, day, time, site FROM series') as cursor:
            rows = await cursor.fetchall()

    if rows:
        response = "Here is the list of series:\n"
        for row in rows:
            name, day, time, site = row
            response += f"- **{name}** on {site} ({day} at {time} UTC)\n"
    else:
        response = "No series found in the database."

    await interaction.response.send_message(response)

# -----------------------------------------------------------------------------------------------------
# Buttons Styling

class WorkView(View):
    def __init__(self, channel, role_id):
        super().__init__(timeout=None)
        self.channel = channel
        self.role_id = role_id
        self.pressed_buttons = {}

    async def update_button(self, button: Button, interaction: Interaction):
        user = interaction.user
        button.label = f"{button.custom_id}: {user.name}"
        button.disabled = True
        button.style = ButtonStyle.green
        self.pressed_buttons[button.custom_id] = user.name
        await interaction.response.edit_message(view=self)

        # Check if all buttons are pressed
        # if len(self.pressed_buttons) == 4:
        #     thank_you_message = "❤️ Thanks for your hard work on this Chapter:\n" + "\n".join(
        #         [f"{role}: {name}" for role, name in self.pressed_buttons.items()]
        #     )
        #     await self.channel.send(thank_you_message)
            # Move the channel back to the 'with raw' category
            # category = discord.utils.get(self.channel.guild.categories, id=WITH_RAW_CATEGORY_ID)
            # await self.channel.edit(category=category)

    @discord.ui.button(label="Translate", custom_id="Translate", style=ButtonStyle.blurple)
    async def translate_button(self, interaction: Interaction, button: Button):
        if K_TRANSLATOR_ROLE_ID in [role.id for role in interaction.user.roles]:
            await self.update_button(button, interaction)
        else:
            await interaction.response.send_message("You do not have permission to press this button.", ephemeral=True)

    @discord.ui.button(label="Proofread", custom_id="ProofReader", style=ButtonStyle.blurple)
    async def proofread_button(self, interaction: Interaction, button: Button):
        if PROOFREADER_ROLE_ID in [role.id for role in interaction.user.roles]:
            await self.update_button(button, interaction)
        else:
            await interaction.response.send_message("You do not have permission to press this button.", ephemeral=True)

    @discord.ui.button(label="Edit", custom_id="Editor", style=ButtonStyle.blurple)
    async def edit_button(self, interaction: Interaction, button: Button):
        if EDITOR_ROLE_ID in [role.id for role in interaction.user.roles]:
            await self.update_button(button, interaction)
        else:
            await interaction.response.send_message("You do not have permission to press this button.", ephemeral=True)


@tasks.loop(minutes=1)
async def check_series_updates():
    now = datetime.datetime.now(pytz.utc).strftime('%A %I:%M %p')
    print("Check For Series Updates")

    async with aiosqlite.connect('series.db') as db:
        async with db.execute('SELECT name, channel_id, role_id,raw_link,drive_link FROM series WHERE enabled = 1 AND day || " " || time = ?', (now,)) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                name, channel_id, role_id,raw_link,drive_link = row
                print(f"Found series to update: {name} in channel {channel_id}")
                
                channel = bot.get_channel(channel_id)
                if channel:
                    guild=bot.get_guild(guild_id)
                    role = discord.utils.get(channel.guild.roles, id=role_id)
                    rp_role=discord.utils.get(guild.roles, id=rp_id)
                    print(rp_role)
                else:
                    print(f"There is no channel with this id {channel_id}")
                
                rp_pending_channel=bot.get_channel(pending_rp)

                if channel and role:
                    await channel.send(f'{role.mention}{rp_role.mention}',embed=get_mention_embed("A New Chapter Just Came Out!",raw_link,drive_link))
                    
                    # Send the buttons for work tracking
                    view = WorkView(channel, role_id)
                    await channel.send(f"Please Press The Button If You Are Here! <:1238787156009422894:1301620277959987280>",view=view)
                
                else:
                    print(f"Channel or role not found for series {name}.")
# ------------------------------------------------------------------------------------------------------------

roles_dict={"tl_deadline":["Translation",tl_id],
            "pr_deadline":["Proofreading",pr_id],
            "ed_deadline":["Editing",ed_id]}

class DeadlineView(View):
    def __init__(self, management_role, manhua, chapter, role):
        super().__init__(timeout=None)
        self.management_role = management_role
        self.manhua = manhua  
        self.chapter = chapter 
        self.role = role 

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow users with the management role to interact with the buttons
        return self.management_role in interaction.user.roles

    @discord.ui.button(label="Extend 6h", style=discord.ButtonStyle.primary)
    async def extend_6h(self, interaction: discord.Interaction, button: Button):  
        await self.extend_deadline(interaction, hours=6)

    @discord.ui.button(label="Extend 12h", style=discord.ButtonStyle.primary)
    async def extend_12h(self, interaction: discord.Interaction, button: Button):  
        await self.extend_deadline(interaction, hours=12)

    @discord.ui.button(label="Extend 24h", style=discord.ButtonStyle.primary)
    async def extend_24h(self, interaction: discord.Interaction, button: Button):  
        await self.extend_deadline(interaction, hours=24)

    async def extend_deadline(self, interaction: discord.Interaction, hours: int):  

        try:
            volt.extend_deadline(hours, self.manhua, self.chapter, self.role)
        except Exception as e:
            print(e)
            await interaction.response.send_message( 
                f"Failed to extend the deadline: {e}", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message( 
                embed=get_embed(f"Deadline Is Extended By {hours} Hours For {self.manhua} (Chapter {self.chapter})."), 
                ephemeral=False
            )

    @discord.ui.button(label="Share Chapter", style=discord.ButtonStyle.secondary, custom_id="share_chapter")
    async def share_chapter(self, interaction: discord.Interaction, button: Button):

        # Find the "claim" channel
        claim_channel=bot.get_channel(claim_chapters_id)
        print(claim_channel)

        if claim_channel is None:
            await interaction.response.send_message(
                "The 'claim' Channel Doesn't Exist.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"Chapter Available for Claim",
            description=f"● **Manhua:** {self.manhua}\n● **Chapter:** {self.chapter}\n● **Role:** {roles_dict[self.role][0]}",
            color=0x9d0f87)
        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")

        role = discord.utils.get(interaction.guild.roles,id=roles_dict[self.role][1])



        
        # Send the embed to the "claim" channel
        await claim_channel.send(role.mention,embed=embed,view=ClaimView(self.manhua,self.chapter,role,interaction.channel.id))

        # Notify the user that the chapter has been shared
        await interaction.response.send_message(embed=get_embed(f"Chapter {self.chapter} Of {self.manhua} Has Been Shared In The 'Claim Chapters' Channel."))

# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# The Share-Chapter View

class OnlyShareChapter(View):
    def __init__(self, management_role, manhua, chapter, role):
        super().__init__(timeout=None)
        self.management_role = management_role
        self.manhua = manhua  
        self.chapter = chapter 
        self.role = role  

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow users with the management role to interact with the buttons
        return self.management_role in interaction.user.roles

    @discord.ui.button(label="Share Chapter", style=discord.ButtonStyle.secondary, custom_id="share_chapter")
    async def share_chapter(self, interaction: discord.Interaction, button: Button):
        # Find the "claim" channel
        claim_channel=bot.get_channel(claim_chapters_id)
        print(claim_channel)

        if claim_channel is None:
            await interaction.response.send_message(
                "The 'claim' Channel Doesn't Exist.",
                ephemeral=True
            )
            return
        
        # Create an embed to share the chapter details
        embed = discord.Embed(
            title=f"Chapter Available for Claim",
            description=f"● **Manhua:** {self.manhua}\n● **Chapter:** {self.chapter}\n● **Role:** {roles_dict[self.role][0]}",
            color=0x9d0f87)
        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")

        role = discord.utils.get(interaction.guild.roles,id=roles_dict[self.role][1])        
        
        # Send the embed to the "claim" channel
        await claim_channel.send(role.mention,embed=embed,view=ClaimView(self.manhua,self.chapter,role,interaction.channel.id))

        # Notify the user that the chapter has been shared
        await interaction.response.send_message(embed=get_embed(f"Chapter {self.chapter} Of {self.manhua} Has Been Shared In The 'Claim Chapters' Channel."))

# ------------------------------------------------------------------------------------------------------------------------------------------------------------

class ClaimView(View):
    def __init__(self, manhua, chapter,role, channel_name):
        super().__init__(timeout=None)
        self.manhua = manhua 
        self.chapter = chapter  
        self.role = role  
        self.channel_name = channel_name  

    async def interaction_check(self, interaction: discord.Interaction) -> bool:

        user_roles = [role.name for role in interaction.user.roles]

        if str(self.role) in user_roles:
            return True

        await interaction.response.send_message(
            embed=get_embed("You do not have the required role to claim this chapter."),
            ephemeral=True
        )
        return False

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.blurple)
    async def claim_button(self, interaction: discord.Interaction, button: Button):

        # Disable the button after it's clicked
        button.disabled = True
        
        await interaction.message.edit(view=self)
        channel_role=discord.utils.get(interaction.guild.roles,id=volt.get_channel_role_id(self.manhua)[0])

        if channel_role is None:
            await interaction.response.send_message(
                f"The role '{channel_role}' does not exist.",
                ephemeral=True
            )
            return

        # Assign the role to the user
        try:
            await interaction.user.add_roles(channel_role)
        except Exception as e:
            print(f"Error assigning role: {e}")
            await interaction.response.send_message(
                "An error occurred while assigning the role.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=get_embed(f"Chapter {self.chapter} of {self.manhua} has been assigned to {interaction.user.global_name}."),
            ephemeral=False
        )

        volt.assign_claim(self.manhua,self.chapter,self.role,interaction.user.name)
        
        
        # Notify the original channel
        original_channel = discord.utils.get(interaction.guild.channels, id=self.channel_name)
        if original_channel:
            await original_channel.send(
                interaction.user.mention,
                embed=get_embed(f"Chapter {self.chapter} of {self.manhua} has been assigned to {interaction.user.global_name}.")
            )

# ------------------------------------------------------------------------------------------------------------------------------------------------------------

@tasks.loop(seconds=57)
async def check_deadline_time():
    try:
        print('Check The Deadline')
        now = datetime.datetime.now(pytz.utc).strftime('%d-%m-%Y %I:%M %p')
        results=volt.check_deadline(now)
        management_role=discord.utils.get(the_global_guild.roles,id=management)
        for key,value in results.items():
            
            channel=discord.utils.get(the_global_guild.channels,name=key)

            
            value=value[0]
            print(value)
            if value[1] == now:
                translator=volt.get_assigned_translator(key)
                translator=the_global_guild.get_member_named(translator[0])

                deadline_counter= volt.get_notify_counter("tl",channel.name,value[0])

                if deadline_counter == 0:

                    volt.add_notify_counter("tl",channel.name,value[0])

                    view=DeadlineView(management_role,key,value[0],"tl_deadline")

                    await channel.send(f"{translator.mention}{management_role.mention}",embed=get_embed(f"**``{translator.display_name}``** You've Lost The Rights To Translate This Chapter => {value[0]}"),view=view)

                elif deadline_counter == 1 :
                    view=OnlyShareChapter(management_role,key,value[0],"tl_deadline")

                    await channel.send(f"{translator.mention}{management_role.mention}",embed=get_embed(f"**``{translator.display_name}``** You've Lost The Rights To Translate This Chapter => {value[0]}"),view=view)

# ----------------------------------------------------

            if value[2] == now:
                proofreader=volt.get_assigned_proofreader(key)
                proofreader=the_global_guild.get_member_named(proofreader[0])

                deadline_counter= volt.get_notify_counter("pr",channel.name,value[0])

                if deadline_counter == 0:

                    volt.add_notify_counter("pr",channel.name,value[0])
                    view=DeadlineView(management_role,key,value[0],"pr_deadline")

                    await channel.send(f"{proofreader.mention}{management_role.mention}",embed=get_embed(f"**``{proofreader.display_name}``** You've Lost The Rights To Proofread This Chapter => {value[0]}"),view=view)

                elif deadline_counter == 1 :
                    view=OnlyShareChapter(management_role,key,value[0],"pr_deadline")

                    await channel.send(f"{proofreader.mention}{management_role.mention}",embed=get_embed(f"**``{proofreader.display_name}``** You've Lost The Rights To Translate This Chapter => {value[0]}"),view=view)

# ----------------------------------------------------

            if value[3] == now:
                editor=volt.get_assigned_editor(key)
                editor=the_global_guild.get_member_named(editor[0])

                deadline_counter= volt.get_notify_counter("ed",channel.name,value[0])

                if deadline_counter == 0:
                    volt.add_notify_counter("ed",channel.name,value[0])
                    view=DeadlineView(management_role,key,value[0],"ed_deadline")

                    await channel.send(f"{editor.mention }{management_role.mention}",embed=get_embed(f"**``{editor.display_name}``** You've Lost The Rights To Edit This Chapter => {value[0]}"),view=view)

                elif deadline_counter == 1 :
                    view=OnlyShareChapter(management_role,key,value[0],"ed_deadline")

                    await channel.send(f"{editor.mention}{management_role.mention}",embed=get_embed(f"**``{editor.display_name}``** You've Lost The Rights To Translate This Chapter => {value[0]}"),view=view)

    except Exception as e:
        print(e)

# Shift Chapter
# -------------------------------------------------------------------------------------------------------------------------------

# Shift Chapter Command
@bot.tree.command(name="shift_chapter", description="Shift A Chapter From A Member To Another")
@has_role("Management")
async def shift_chapter(interaction: discord.Interaction, role: str, original_holder: str, new_holder: str, chapter_number: int):
    current_channel = interaction.channel.name

    if role == "editors":
        result=volt.shift_chapter_ed(current_channel,chapter_number,original_holder,new_holder)
    elif role == "proofreader":
        result=volt.shift_chapter_pr(current_channel,chapter_number,original_holder,new_holder)
    elif role == "raw_provider":
        result=volt.shift_rp(current_channel,chapter_number,original_holder,new_holder)
    elif role == "translator":
        result=volt.shift_chapter_tl(current_channel,chapter_number,original_holder,new_holder)

    print(result)
    # Your logic for shifting the chapter goes here
    await interaction.response.send_message(
        embed=get_embed(result),
        ephemeral=False
    )


# Autocomplete for Role
# -------------------------------------------------------------------------------------------------------------------------------
@shift_chapter.autocomplete("role")
async def role_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    roles = ["editors", "proofreader", "raw_provider", "translator"]
    return [
        app_commands.Choice(name=role, value=role)
        for role in roles if current.lower() in role.lower()
    ]

# Autocomplete for Original Holder and New Holder
@shift_chapter.autocomplete("original_holder")
async def original_holder_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:

    role = interaction.namespace.role
    if not role:
        return []

    # Fetch members with the selected role
    role_id = roles_id_dict.get(role)
    if not role_id:
        return []

    members = await get_members_with_role(interaction.guild, role_id)
    return [
        app_commands.Choice(name=member.display_name, value=member.name)
        for member in members if current.lower() in member.display_name.lower()
    ]

@shift_chapter.autocomplete("new_holder")
async def new_holder_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    role = interaction.namespace.role
    if not role:
        return [] 

    # Fetch members with the selected role
    role_id = roles_id_dict.get(role)
    if not role_id:
        return [] 

    members = await get_members_with_role(interaction.guild, role_id)
    return [
        app_commands.Choice(name=member.display_name, value=member.name)
        for member in members if current.lower() in member.display_name.lower()
    ]

# -------------------------------------------------------------------------------------------------------------------------------


@bot.tree.command(name="add_member", description="Add A Member To The System")
@has_role("Management")
async def add_member(interaction: discord.Interaction, role: str,name:str):

    display_name=discord.utils.get(interaction.guild.members, name=name)

    volt.add_member(role,name,display_name.display_name)

    await interaction.response.send_message(embed=get_embed(f"The Member {display_name.display_name} Is Added Successfully To The System."))



@add_member.autocomplete("role")
async def role_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    roles = ["editors", "proofreader", "raw_provider", "translator"]
    return [
        app_commands.Choice(name=role, value=role)
        for role in roles if current.lower() in role.lower()
    ]

# Autocomplete for Original Holder and New Holder
@add_member.autocomplete("name")
async def name_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:

    # Get the selected role from the interaction
    role = interaction.namespace.role
    if not role:
        return [] 

    role_id = roles_id_dict.get(role)
    if not role_id:
        return [] 

    members = await get_members_with_role(interaction.guild, role_id)
    return [
        app_commands.Choice(name=member.display_name, value=member.name)
        for member in members if current.lower() in member.display_name.lower()
    ]

# Force Extend Part
# -------------------------------------------------------------------------------------------------------------------------------
@bot.tree.command(name="reschedule_deadline",description="Force To Extend Deadline")
@has_role("Management")
async def reschedule_deadline(interaction: discord.Interaction,role:str,chapter_number:int,extended_hours:float):
    current_channel=interaction.channel.name

    try:
        volt.extend_deadline(extended_hours,current_channel,chapter_number,role)

    except Exception as e:
        print(e)
        await interaction.response.send_message(embed=get_embed(f"Error Happened While Extending The Deadline :("))
    
    else:
        await interaction.response.send_message(embed=get_embed(f"The Deadline Is Extended By {extended_hours} Hours :)"))

@reschedule_deadline.autocomplete("role")
async def role_autocompletion(interaction:discord.Interaction,
                            current:str)-> typing.List[app_commands.Choice[str]]:
    data=[]
    for role in ["tl_deadline", "pr_deadline", "ed_deadline"]:
        if current.lower() in role.lower():
            data.append(app_commands.Choice(name=role,value=role))
    return data

# sereis info
# -------------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="series_info",description="Shows The Info Of A Specific Series.")
@has_role("Management")
async def series_info(interaction: discord.Interaction,):
    current_channel= interaction.channel.name
    channel_id=interaction.channel.id
    
    info1=volt.get_series_info(current_channel)

    async with aiosqlite.connect('series.db') as db:
        async with db.execute(f'SELECT day, time, site, raw_link, drive_link FROM series where channel_id={channel_id}') as cursor:
            info2 = await cursor.fetchone()
    if info2 != None and info1 != None:

        date=f"{info2[0]}-{info2[1]}"

        embed=discord.Embed(title=f"{current_channel} info",color=0x9d0f87)

        embed.add_field(name="Assigned Translator:",value=f"> **``{info1[0]}``**")
        embed.add_field(name="Assigned ProoofReader:",value=f"> **``{info1[1]}``**")
        embed.add_field(name="Assigned Editor:",value=f"> **``{info1[2]}``**")

        embed.add_field(name="Release Date:",value=f"> **``{date}``**",inline=False)
        embed.add_field(name="Site:",value=f"> **``{info2[2]}``**",inline=False)

        embed.add_field(name="Raws Link:",value=f"> {info2[3]}",inline=False)
        embed.add_field(name="Drive Link:",value=f"> {info2[4]}")

        embed.set_image(url="https://i.imgur.com/bWDStsx.jpg")

        await interaction.response.send_message(embed=embed,ephemeral=True)
    
    else:
        await interaction.response.send_message(embed=get_embed("This Title Is Not Added To The System :("),ephemeral=True)

# delete chapter
# -------------------------------------------------------------------------------------------------------------------------------

@bot.tree.command(name="delete_chapter",description="Delete A Chapter From The System.")
@has_role("Management")
async def delete_chapter(interaction: discord.Interaction,chapter_number: int):
    current_channel= interaction.channel.name

    result=volt.delete_chapter(current_channel,chapter_number)

    await interaction.response.send_message(embed=get_embed(result))


# On Changing On Channel Name
# -------------------------------------------------------------------------------------------------------------------------------

@bot.event
async def on_guild_channel_update(before, after):
    if isinstance(after, discord.TextChannel) and before.name != after.name:
        
        # Rename the table in the database
        if volt.rename_manhua_table(before.name, after.name):
            print(f"Table renamed from '{before.name}' to '{after.name}'")
        else:
            print(f"Failed to rename table from '{before.name}' to '{after.name}'")

# -------------------------------------------------------------------------------------------------------------------------------

# Error Handling
# -------------------------------------------------------------------------------------------------------------------------------

from discord.app_commands import AppCommandError, CheckFailure

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):

    if isinstance(error, app_commands.CheckFailure):
        my_logger = logging.getLogger(interaction.user.name)
        my_logger.warning(error)
        await interaction.response.send_message(
            embed=get_embed("You Don't Have The Required Role To Use This Command (•ᴗ-)"),
            ephemeral=True
        )

    else:

        my_logger = logging.getLogger(interaction.user.name)
        my_logger.warning(error)


        await interaction.response.send_message(
            embed=get_embed(f"An Unexpected Error Occurred: {error} Please Send It To The Management"),
            ephemeral=True
        )
        
        print(f"Unexpected error in command: {error}")


bot.run(TOKEN)

