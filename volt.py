import datetime
import io
import sqlite3
import discord
import csv
import pytz
from thefuzz.fuzz import token_set_ratio


db=sqlite3.connect("manhua.db")
cr=db.cursor()

staff_tables=["translator","proofreader","editors","raw_provider"]

def saving():
    db.commit()
# deadline part------------------------------------------------------------------------


def get_deadline(category):

    def add_12h():
        time_now=datetime.datetime.now(pytz.utc)
        deadline=time_now+datetime.timedelta(hours=12)
        deadline=deadline.strftime('%d-%m-%Y %I:%M %p')
        print(f"The Deadline Is {deadline}")
        return deadline
        
    def add_36h():
        time_now=datetime.datetime.now(pytz.utc)
        deadline=time_now+datetime.timedelta(hours=36)
        deadline=deadline.strftime('%d-%m-%Y %I:%M %p')
        print(f"The Deadline Is {deadline}")
        return deadline

    def add_24h():
        time_now=datetime.datetime.now(pytz.utc)
        deadline=time_now+datetime.timedelta(hours=24)
        deadline=deadline.strftime('%d-%m-%Y %I:%M %p')
        print(f"The Deadline Is {deadline}")
        return deadline
    
    def add_6h():
        time_now=datetime.datetime.now(pytz.utc)
        deadline=time_now+datetime.timedelta(hours=6)
        deadline=deadline.strftime('%d-%m-%Y %I:%M %p')
        print(f"The Claim Deadline Is => {deadline}")
        return deadline
    
    def add_3h():
        time_now=datetime.datetime.now(pytz.utc)
        deadline=time_now+datetime.timedelta(hours=3)
        deadline=deadline.strftime('%d-%m-%Y %I:%M %p')
        print(f"The Claim Deadline Is => {deadline}")
        return deadline

    if category == "High Priority":
        return add_24h()
    elif category =="Normal Priority":
        return add_36h()
    elif category =="claim":
        return add_3h()
    elif category == "Urgent Comp":
        return add_6h()

def extend_deadline(extend_length,manhua,chapter,role):
    time_now=datetime.datetime.now(pytz.utc)
    deadline=time_now+datetime.timedelta(hours=extend_length)
    deadline=deadline.strftime('%d-%m-%Y %I:%M %p')
    print(deadline)
    try:
        cr.execute(f"update '{manhua}' set '{role}' = '{deadline}' where chapter = '{chapter}'")
    except Exception as e:
        print(e)
    else:
        saving()



def check_deadline(time_now):
    deadline_dict={}
    cr.execute("select name from sqlite_master where type='table'")
    table_names=cr.fetchall()  
    for table in table_names:
        table=table[0]
        if table not in staff_tables:
            cr.execute(f'''select chapter,tl_deadline,pr_deadline,ed_deadline from '{table}' 
                        where tl_deadline ='{time_now}' 
                        OR pr_deadline = '{time_now}' 
                        OR ed_deadline ='{time_now}' ''')            
            result=cr.fetchall()
            if result:
                deadline_dict.update({table:result})
    return deadline_dict



def has_deadline_passed(manhua,chapter,role):
    cr.execute(f"select {role} from '{manhua}' where chapter = {chapter}")
    result=cr.fetchone()
    try:
        deadline = datetime.datetime.strptime(result[0], '%d-%m-%Y %I:%M %p').replace(tzinfo=pytz.utc)
        time_now = datetime.datetime.now(pytz.utc)
    except Exception as e:
        print(f'Error From tldone {e}')
    else:
        if deadline < time_now:
            return True
        else: return False

# -----------------------------------------------------------------------------------------

def get_remaining_deadline(manhua, chapter, target):
    target_dict = {
        "translate_st": "tl_deadline",
        "prof_st": "pr_deadline",
        "edit_st": "ed_deadline"
    }
    
    if target != "upload_st":
    
        try:
            cr.execute(f"SELECT {target_dict[target]} FROM '{manhua}' WHERE chapter = ?", (chapter,))
            deadline = cr.fetchone()
            
            if not deadline or not deadline[0]:
                print(f"No deadline found for {manhua} chapter {chapter}")
                return 0, 0
            
            deadline_str = str(deadline[0])
            
            deadline_naive = datetime.datetime.strptime(deadline_str, "%d-%m-%Y %I:%M %p")
            
            deadline_utc = pytz.utc.localize(deadline_naive)
            
            time_now = datetime.datetime.now(pytz.utc)
            
            time_diff = deadline_utc - time_now
            
            if time_diff.total_seconds() <= 0:
                print("its old")
                return 0, 0
            
            total_seconds = int(time_diff.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60
            
            return hours, minutes
            
        except sqlite3.Error as e:
            print(f"Database error for {manhua} chapter {chapter}: {e}")
            return None
        except ValueError as e:
            print(f"Invalid date format for {manhua} chapter {chapter}: {e}")
            return None





# -----------------------------------------------------------------------------------------
def check_assign_date(manhua,job):
    cr.execute(f"select {job},chapter from {manhua}")
    result=cr.fetchall()
    for r in result:
        try:
            if  r[0]=='None':
                continue
            passed_chapters = datetime.datetime.strptime(r[0], '%Y-%m-%d').replace(tzinfo=pytz.utc)
            time_now = datetime.datetime.now(pytz.utc)
        except Exception as e:
            print(f'Error From tldone {e}')
        else:
            if passed_chapters >= time_now:
                return True
            else:
                return False


# -----------------------------------------------------------------------------------------
def get_assigned_translator(manhua):
    cr.execute(f"SELECT ass_tl FROM '{manhua}' ORDER BY ROWID DESC LIMIT 1")

    result=cr.fetchone()
    return result


def get_assigned_proofreader(manhua):
    cr.execute(f"SELECT ass_pr FROM '{manhua}' ORDER BY ROWID DESC LIMIT 1")
    result=cr.fetchone()
    return result

def get_assigned_editor(manhua):
    cr.execute(f"SELECT ass_ed FROM '{manhua}' ORDER BY ROWID DESC LIMIT 1")
    result=cr.fetchone()
    return result

def assign_claim(manhua,chapter,role,user):
    print("the assign_claim is working")

    deadline=get_deadline(category="claim")

    if str(role)== "k-Translator": cr.execute(f"update '{manhua}' set tl_deadline= '{deadline}' where chapter = {chapter}")

    elif str(role)== "ProofReader": cr.execute(f"update '{manhua}' set pr_deadline= '{deadline}' where chapter = {chapter}")

    elif str(role)== "Editor": cr.execute(f"update '{manhua}' set ed_deadline= '{deadline}' where chapter = {chapter}")

    saving()



def get_rate():
    the_ultimate_dict=dict({})
    db= sqlite3.connect("manhua.db")
    all_table_names=[]
    cr=db.cursor()
    cr.execute("select name from sqlite_master where type='table'")
    table_names=cr.fetchall()

    for table in table_names:
        all_table_names.append(*table)


    with open("Staff Data/series_rate.csv") as rate_file:
        rate_file=csv.reader(rate_file)
        
        for series in rate_file:
            if series[0]== "Series Name":
                continue

            name=series[0].lower().strip().replace("-"," ")
            for table in all_table_names:
                if name in table.lower().strip().replace("-"," "):
                    the_ultimate_dict.update({table:series})

    return the_ultimate_dict




def add_manhua(server):    

    cats=["Urgent Comp","High Priority","Normal Priority"]
    for cat in cats:
        category_name = cat  
        guild = server 
        category = discord.utils.get(guild.categories, name=category_name) 
        if category:
            channels = category.channels  
            for channel in channels:
                cr.execute(f'''create table if not exists '{channel.name}' (
                            chapter integer,
                            rawprof_st string ,
                            upscale_st string ,
                            translate_st string,
                            prof_st string,
                            edit_st string,
                            upload_st string,
                            
                            rp_money float ,                            
                            pr_money float,
                            tl_money float,
                            ed_money float,
                            
                            ass_pr string,
                            ass_tl string,
                            ass_ed string,
                            
                            chapter_translator string,
                            chapter_rawprovider string,
                            chapter_proofreader string,
                            chapter_editor string,
                            chapter_uploader string,
                            
                            chapter_translate_date string,
                            chapter_rawprovide_date string,
                            chapter_proofread_date string,
                            chapter_edit_date string,
                            chapter_upload_date string,

                            tl_deadline string,
                            pr_deadline string,
                            ed_deadline string,
                            
                            role_id integer,

                            notify_tl_deadline integer,
                            notify_pr_deadline integer,
                            notify_ed_deadline integer
                            )
                            ''')
    global series_rates
    series_rates=get_rate()

# ------------------------------------------------------------------------------------------------------------
def add_chapter(manhua_name,chapter_number,category, server, rp_money, tl_money, pr_money, ed_money):

    manhua_role=0
    
    try:
        assigned_translator=get_assigned_translator(manhua_name)[0]
        assigned_proofreader=get_assigned_proofreader(manhua_name)[0]
        assigned_editor=get_assigned_editor(manhua_name)[0]
    


    except Exception as e:
        assigned_translator="None"
        assigned_proofreader="None"
        assigned_editor="None"
        
    try:
        the_name_for_name=manhua_name.replace("-"," ").replace("🔵","").replace("⚡","")
        print(the_name_for_name)        
        manhua_role = next((r for r in server if token_set_ratio(r.name.lower(),the_name_for_name) > 80), None)
        print("found =>",manhua_role)
        manhua_role=manhua_role.id
        
    except Exception as e:
        print(e)

    else:
        print("this is =>",manhua_role)

    deadline=get_deadline(category=category)

    cr.execute(f"select chapter from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()
    if fetched_chapter == None:

        cr.execute(f'''insert into '{manhua_name}' values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (int(chapter_number),
                    "waiting",
                    "waiting",
                    "waiting",
                    "waiting",
                    "waiting",
                    "waiting",

                    rp_money,
                    pr_money,
                    tl_money,
                    ed_money,

                    assigned_proofreader,
                    assigned_translator,
                    assigned_editor,

                    "None",
                    "None",
                    "None",
                    "None",
                    "None",

                    "None",
                    "None",
                    "None",
                    "None",
                    "None",

                    "None",
                    "None",
                    "None" ,                     

                    manhua_role,

                    0,
                    0,
                    0
                    ))

        saving()

        return f"Chapter {chapter_number} Is Out From {manhua_name}"
    else :
        return "0Already Added"


# -------------------------------------------------------------------------------------------------------------------------------
def rp(manhua_name,chapter_number,chapter_rawprovider,category):

    deadline=get_deadline(category=category)

    cr.execute(f"select chapter from '{manhua_name}' where chapter = {chapter_number}")
    checking_state=cr.fetchone()

    if checking_state:
    
        cr.execute(f"select rawprof_st, rp_money from '{manhua_name}' where chapter = {chapter_number}")
        fetched_chapter=cr.fetchone()

        if fetched_chapter[0] == "waiting":

            try:
                    cr.execute(f"update '{manhua_name}' set rawprof_st = 'done' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_rawprovider = '{chapter_rawprovider}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_rawprovide_date = '{str(datetime.date.today())}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set tl_deadline = '{deadline}' where chapter = {chapter_number}")
                
                    cr.execute(f"select number_of_chapters, total_money from raw_provider where unique_name = '{chapter_rawprovider}'")
                    rp_income=cr.fetchone()

                    if chapter_rawprovider not in ['volt8756',"ms_17"]:
                        cr.execute(f"update raw_provider set number_of_chapters = {rp_income[0]+1} where unique_name = '{chapter_rawprovider}'")
                        cr.execute(f"update raw_provider set total_money = {rp_income[1]+float(series_rates[manhua_name][4])} where unique_name = '{chapter_rawprovider}'")
                    
                    saving()

                    return f"Chapter {chapter_number} is now ready for Translating!"

            except Exception as e:
                print(e)

        else:
            return "The Chapter Is Already Marked As Done."

    else:
        return "0The Chapter Is Not Out Yet."

# -------------------------------------------------------------------------------------------------------------------------------

def tldone(manhua_name,chapter_number,chapter_translator,category):
    
    deadline=get_deadline(category=category)

    cr.execute(f"select rawprof_st, translate_st, tl_money from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()
    if isinstance(fetched_chapter,tuple):
        if fetched_chapter[0] =="done":
            if fetched_chapter[1] == "waiting":
                try:
                    cr.execute(f"update '{manhua_name}' set translate_st = 'done' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_translator = '{chapter_translator}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_translate_date = '{str(datetime.date.today())}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set pr_deadline = '{deadline}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set tl_deadline = 'completed' where chapter = {chapter_number}")


                    cr.execute(f"select number_of_chapters, total_money from translator where unique_name = '{chapter_translator}'")
                    translator_income=cr.fetchone()

                    if chapter_translator not in ['volt8756',"ms_17"]:
                        cr.execute(f"update translator set number_of_chapters = {translator_income[0]+1} where unique_name = '{chapter_translator}'")
                        cr.execute(f"update translator set total_money = {translator_income[1]+fetched_chapter[2]} where unique_name = '{chapter_translator}'")

                    saving()
                    return f"Chapter {chapter_number} is now ready for proofreading!"
                except Exception as e:
                    print(e)
            
            else: return f"xChapter {chapter_number} Is Already Marked As 'Done'"  
        else:
            return "wThe Chapter Is Getting Prepeared."
    else :
        return "0The Chapter Is Not Out."


# -------------------------------------------------------------------------------------------------------------------------------
def prdone(manhua_name,chapter_number,chapter_proofreader,category):

    deadline=get_deadline(category=category)

    cr.execute(f"select translate_st, prof_st, pr_money from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()

    if isinstance(fetched_chapter,tuple):

        if fetched_chapter[0] =="done":

            if fetched_chapter[1]=="waiting":
                try:
                    cr.execute(f"update '{manhua_name}' set prof_st = 'done' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_proofreader = '{chapter_proofreader}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_proofread_date = '{str(datetime.date.today())}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set ed_deadline = '{deadline}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set pr_deadline = 'completed' where chapter = {chapter_number}")


                    cr.execute(f"select number_of_chapters, total_money from proofreader where unique_name = '{chapter_proofreader}'")
                    proofreader_income=cr.fetchone()

                    if chapter_proofreader not in ['volt8756',"ms_17"]:
                        cr.execute(f"update proofreader set number_of_chapters = {proofreader_income[0]+1} where unique_name = '{chapter_proofreader}'")
                        cr.execute(f"update proofreader set total_money = {proofreader_income[1]+fetched_chapter[2]} where unique_name = '{chapter_proofreader}'")


                    saving()
                    return f"Chapter {chapter_number} Is Now Ready For Typesetting!"
                except Exception as e:
                    print(e)
            else:
                return f"xChapter {chapter_number} Is Already Marked As 'Done'"
            
        elif fetched_chapter[0] =="waiting":
            return f"wChapter {chapter_number} is getting prepared."
        
    else :
        return "0The Chapter Is Not Out."


# -------------------------------------------------------------------------------------------------------------------------------

def eddone(manhua_name,chapter_number,chapter_editor):
    cr.execute(f"select prof_st, edit_st, ed_money from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()
    if isinstance(fetched_chapter,tuple):

        if fetched_chapter[0] =="done":
            if fetched_chapter[1]=="waiting":
                try:
                    cr.execute(f"update '{manhua_name}' set edit_st = 'done' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_editor = '{chapter_editor}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set chapter_edit_date = '{str(datetime.date.today())}' where chapter = {chapter_number}")
                    cr.execute(f"update '{manhua_name}' set ed_deadline = 'completed' where chapter = {chapter_number}")


                    cr.execute(f"select number_of_chapters, total_money from editors where unique_name = '{chapter_editor}'")
                    editor_income=cr.fetchone()
                    cr.execute(f"update editors set number_of_chapters = {editor_income[0]+1} where unique_name = '{chapter_editor}'")
                    cr.execute(f"update editors set total_money = {editor_income[1]+fetched_chapter[2]} where unique_name = '{chapter_editor}'")

                    saving()
                    return f"Chapter {chapter_number} Is Now Ready For Uploading!"
                except Exception as e:
                    print(e)
            else:
                return f"xChapter {chapter_number} Is Already Marked As 'Done'"
        
        elif fetched_chapter[0] =="waiting":
            return f"wChapter {chapter_number} is getting prepared."
        
    else :
        return "0The Chapter Is Not Out."


# -------------------------------------------------------------------------------------------------------------------------------

def udone(manhua_name,chapter_number,chapter_uploader):
    cr.execute(f"select edit_st, upload_st from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()
    if isinstance(fetched_chapter,tuple):

        if fetched_chapter[0] =="done":
            if fetched_chapter[1]=="waiting":
                cr.execute(f"update '{manhua_name}' set upload_st = 'done' where chapter = {chapter_number}")
                cr.execute(f"update '{manhua_name}' set chapter_uploader = '{chapter_uploader}' where chapter = {chapter_number}")
                cr.execute(f"update '{manhua_name}' set chapter_upload_date = '{str(datetime.date.today())}' where chapter = {chapter_number}")
                saving()
                return f"Chapter {chapter_number} Is Uploaded!"
            else:
                return f"xChapter {chapter_number} Is Already Marked As 'Done'"
            
        elif fetched_chapter[0] =="waiting":
            return f"wChapter {chapter_number} is getting prepared."
        
    else :
        return "0The Chapter Is Not Out."
    
def assign_tl(manhua_name,tl,text_name):
    try:
        cr.execute(f"update '{manhua_name}' set ass_tl = '{tl}' ")
        saving()
    except Exception as e:
        return "Error Happened"
    else:
        return f"**``{text_name}``** Has Been Assigned As The **Translator** Of **``{manhua_name}``**!"
    

def assign_pr(manhua_name,pr,text_name):
    try:
        cr.execute(f"update '{manhua_name}' set ass_pr = '{pr}' ")
        saving()
    except Exception as e:
        return "Error Happened"
    else:
        return f"**``{text_name}``** Has Been Assigned As The **Proofreader** Of **``{manhua_name}``**!"

def assign_ed(manhua_name,ed,text_name):
    try:
        cr.execute(f"update '{manhua_name}' set ass_ed = '{ed}' ")
        saving()
    except Exception as e:
        # print(e)
        return "Error Happened"

    else:
        return f"**``{text_name}``** Has Been Assigned As The **Editor** Of **``{manhua_name}``**!"

def add_bonus(member,bonus):
    pages=['editors','proofreader','raw_provider','translator']
    for page in pages:
        cr.execute(f"select name from {page} where name = '{member}' ")
        result=cr.fetchone()
        if result:
            cr.execute(f"select total_money, bonus from {page} where name = '{member}'")
            money=cr.fetchone()

            old_total_income=money[0]
            old_bonus=money[1]

            cr.execute(f'''update '{page}'
                        set bonus = {bonus+old_bonus},
                        total_money = {old_total_income+bonus}
                        where name = '{member}' ''')
            saving()
            
            return("Bonus Added Successfully!")
        

def add_penalty(member,penalty):
    pages=['editors','proofreader','raw_provider','translator']
    for page in pages:
        cr.execute(f"select name from {page} where name = '{member}' ")
        result=cr.fetchone()
        if result:
            cr.execute(f"select total_money, penalty from {page} where name = '{member}'")
            money=cr.fetchone()

            old_total_income=money[0]
            old_penalty=money[1]

            cr.execute(f'''update '{page}'
                        set penalty = {penalty+old_penalty},
                        total_money = {old_total_income-penalty}
                        where name = '{member}' ''')
            saving()
            
            return("Penalty Subtracted Successfully!")


def get_members():
    try:
        cr.execute('''SELECT name FROM editors
                    UNION
                    SELECT name FROM proofreader
                    UNION
                    SELECT name FROM raw_provider
                    UNION
                    SELECT name FROM translator''')
        
        result=cr.fetchall()
    except Exception as e:
        print(e)
    else:
        for r in range(len(result)):
            result[r]= result[r][0].strip()

        return result
    

def get_pending(type):
    results={}
    
    types_dict={
        "translate_st":"tl_deadline",
        "prof_st":"pr_deadline",
        "edit_st":"ed_deadline"
    }

    cr.execute("select name from sqlite_master where type ='table'")   
    tables=cr.fetchall()
    for table in tables:
        table=table[0]
        if type != "upload_st":
            if table not in staff_tables:
                cr.execute(f"select chapter,{type} from '{table}' where {type} = 'waiting' and {types_dict[type]} != 'None' and {types_dict[type]} != 'completed' ")
                pending_chapters=cr.fetchall()
                if len(pending_chapters) != 0:
                    results.update({table:pending_chapters})

        else:
            if table not in staff_tables:
                cr.execute(f"select chapter,{type} from '{table}' where {type} = 'waiting' and ed_deadline = 'completed' ")
                pending_chapters=cr.fetchall()
                if len(pending_chapters) != 0:
                    results.update({table:pending_chapters})

    return results


print(get_pending("translate_st"))
# pending rp
# -----------------------------------------------------------------------------------------------

def get_rp_pending():
    results={}

    cr.execute("select name from sqlite_master where type ='table'")   
    tables=cr.fetchall()
    for table in tables:
        table=table[0]

        if table not in staff_tables:
            cr.execute(f"select chapter from '{table}' where rawprof_st = 'waiting'")
            pending_chapters=cr.fetchall()
            if len(pending_chapters) != 0:
                results.update({table:pending_chapters})

    return results


# Profile Functions
# -----------------------------------------------------------------------------------------------


def profile(user):
    table_names=["raw_provider","translator","proofreader","editors",]
    for table_name in table_names:
        try:
            cr.execute(f"select number_of_chapters, total_money from {table_name} where name='{user}'")
        except Exception as e:
            print(e)
        else:
            profile_data=cr.fetchone()

        if profile_data:
            return profile_data
            
# -----------------------------------------------------------------------------------------------

def get_profile_pending(user):
    results={}
    cr.execute("select name from sqlite_master where type ='table'")   
    tables=cr.fetchall()

    for member in staff_tables:
        try:
            cr.execute(f"select unique_name from '{member}' where unique_name= '{user}'")
            name=cr.fetchone()
        except Exception as e :
            print(e)
        else:
            if name:
                role=member
                break   

    def mini(search_list:list):
        
        for table in tables:
            table=table[0]
            if table not in staff_tables:
            # if table =="test":
                cr.execute(f'''select chapter from '{table}' where 
                            {search_list[0]} = 'waiting' and 
                            {search_list[1]}= '{user}' and
                            {search_list[2]} != 'completed' and
                            {search_list[2]} != 'None' ''')   

                pending_chapters=cr.fetchall()
                if len(pending_chapters) != 0:
                    pending_chapters.append(role)
                    results.update({table:pending_chapters})


    if role=="translator":
        tl_search_list=["translate_st","ass_tl","tl_deadline"]
        mini(tl_search_list)
        return results
    
    elif role =="proofreader":
        pr_search_list=["prof_st","ass_pr","pr_deadline"]
        mini(pr_search_list)
        return results

    elif role =="editors":
        ed_search_list=["edit_st","ass_ed","ed_deadline"]
        mini(ed_search_list)
        return results

    
# -----------------------------------------------------------------------------------------------

def chapters_overview(unique_name):
    results={}
    cr.execute("select name from sqlite_master where type ='table'")   
    tables=cr.fetchall()

    for member in staff_tables:
        try:
            if unique_name in ["volt8756","ms_17"]:
                cr.execute(f"select unique_name from editors where unique_name= '{unique_name}'")
            else:
                cr.execute(f"select unique_name from '{member}' where unique_name= '{unique_name}'")
            name=cr.fetchone()
        except Exception as e :
            print(e)
        else:
            if name:
                role=member
                break  

    def mini(state):
        for table in tables:
            table=table[0]

            if table not in staff_tables:
                if unique_name in ["volt8756","ms_17"]:
                    cr.execute(f"select chapter from '{table}' where chapter_editor = '{unique_name}' ")
                else:
                    cr.execute(f"select chapter from '{table}' where {state} = '{unique_name}' ")
                chapters=cr.fetchall()

                for i, chapter in zip(range(0,len(chapters)),chapters):
                    chapters[i]=chapter[0]

                if len(chapters) != 0:
                    results.update({table:chapters})
                
    
                



    if role=="translator":
        mini("chapter_translator")
        return results
    
    elif role =="proofreader":
        mini("chapter_proofreader")
        return results

    elif role =="editors":
        mini("chapter_editor")
        return results

    elif role =="raw_provider":
        mini("chapter_rawprovider")
        return results
    

# -----------------------------------------------------------------------------------------------
# update e-mail
def update_email(unique_name,email):
    for member in staff_tables:
        try:
            cr.execute(f"select unique_name from '{member}' where unique_name= '{unique_name}'")
            result=cr.fetchone()
        except Exception as e :
            print(e)
        else:
            if result:
                try:
                    cr.execute(f"update {member} set email = '{email}' where unique_name= '{unique_name}'")
                    saving()
                    break
                except Exception as e:
                    print(e)

# -----------------------------------------------------------------------------------------------
# Update pay method
def update_paymethod (unique_name, pay_method) :
    for member in staff_tables:
        try:
            cr.execute(f"select unique_name from '{member}' where unique_name= '{unique_name}'")
            result=cr.fetchone()
        except Exception as e :
            print(e)
        else:
            if result:
                try:
                    cr.execute(f"update '{member}' set payment_method = '{pay_method}' where unique_name= '{unique_name}' ") 
                    saving()
                    break
                except Exception as e:
                    print(e)


# -----------------------------------------------------------------------------------------------

def update_payment_info(unique_name, payment_method, payment_link):
    print(unique_name, payment_method, payment_link)
    if unique_name != "volt8756":
        for member in staff_tables:
            try:
                cr.execute(f"select unique_name from '{member}' where unique_name= '{unique_name}'")
                result = cr.fetchone()
            except Exception as e:
                print(e)
            else:
                if result:
                    try:
                        cr.execute(f"""
                            update '{member}'
                            set payment_method = '{payment_method}',
                                payment_link = '{payment_link}'
                            where unique_name = '{unique_name}'
                        """)
                        saving()
                        break
                    except Exception as e:
                        print(e)
    else:
        try:
                        cr.execute(f"""
                            update 'editors'
                            set payment_method = '{payment_method}',
                                payment_link = '{payment_link}'
                            where unique_name = '{unique_name}'
                        """)
                        saving()
        except Exception as e:
            print(e)


# -----------------------------------------------------------------------------------------------

def update_birthday(unique_name,birthday):
    for member in staff_tables:
        try:
            cr.execute(f"select unique_name from '{member}' where unique_name= '{unique_name}'")
            result=cr.fetchone()
        except Exception as e :
            print(e)
        else:
            if result:
                try:
                    cr.execute(f"update '{member}' set birth_date = '{birthday}' where unique_name= '{unique_name}' ") 
                    saving()
                    break
                except Exception as e:
                    print(e)

# -----------------------------------------------------------------------------------------------

def get_assigned_series(user):
    user_data={}
    user=str(user)
    cr.execute("select name from sqlite_master where type ='table'") 
    tables=cr.fetchall()
    with sqlite3.connect("series.db") as db2:

        for table in tables: 

            if table[0] not in ["raw_provider","translator","proofreader","editors"]:
                cr.execute(f"select ass_tl, ass_pr, ass_ed from '{table[0]}'")
                fetched_data=cr.fetchone()

                if isinstance(fetched_data,tuple) and user in fetched_data:
                        cr2=db2.cursor()
                        cr2.execute("select name from series") 
                        
                        series_table_names=cr2.fetchall()

                        for series_name in series_table_names:
                            series_name=series_name[0]
                            # print(token_set_ratio(table[0],series_name))
                            if token_set_ratio(table[0],series_name) > 80:
                                cr2.execute(f"select day, time, site,channel_id from series where name = '{series_name}'")
                                timing_data=cr2.fetchone()
                                
                                user_data.update({str(series_name).strip().title():list(timing_data)})
    return user_data
# -----------------------------------------------------------------------------------------------

def get_finaces_details(user):
    
    for member in staff_tables:
        try:
            # cr.execute(f"select unique_name from '{member}' where unique_name= '{user}'")
            if user in ["volt8756","ms_17"]:
                cr.execute(f"select unique_name, total_money, bonus, penalty, payment_method from editors where unique_name = '{user}'")
            else:
                cr.execute(f"select unique_name, total_money, bonus, penalty, payment_method from {member} where unique_name = '{user}'")
            finances=cr.fetchone()
        except Exception as e :
            print(e)
        else:
            if finances:
                earnings=finances[1]+finances[3]-finances[2]
                result={"Earnings":f"${earnings}",
                        "Bonus":f"${finances[2]}",
                        "Penalty":f"${finances[3]}",
                        "Total Pay":f"${finances[1]}",
                        "Payment Method":f"{finances[4]}"
                        }
                return result

# -----------------------------------------------------------------------------------------------

def get_management_info():
    results=[]
    for member in staff_tables:
        try:
            cr.execute(f"select unique_name, total_money, payment_method, payment_link from {member}")
        except Exception as e :
            print(e)
        else:
            finances=cr.fetchall()
            if member != "editors":
                for user in finances:
                    if user[0]=="volt8756":
                        finances.remove(user)
            results.extend(finances)

    return results

# Reset Data
# -----------------------------------------------------------------------------------------------

def fetch_archive_data():
    results=[]
    for member in staff_tables:
        try:
            cr.execute(f"select * from {member}")
        except Exception as e :
            print(e)
        else:
            finances=cr.fetchall()
            if member != "editors":
                for user in finances:
                    if user[0]=="volt8756":
                        finances.remove(user)

            results.extend(finances)

    return results

def store_old_statics(date,statics):
    with sqlite3.connect("statices.db") as statics_db:
        statics_cr=statics_db.cursor()
        
        statics_cr.execute(f'''create table if not exists '{date}' 
                            (unique_name string,
                            name string,
                            number_of_chapters int,
                            total_money float,
                            email string,
                            payment_method string,
                            birth_date string,
                            time_zone string,
                            bonus float,
                            penalty float,
                            payment_link string
                            )''') 
                            # UNIQUE(unique_name)
        for st in statics:
            statics_cr.execute(f"insert into '{date}' values (?,?,?,?,?,?,?,?,?,?,?)",(st[0],st[1],st[2],st[3],st[4],st[5],st[6],st[7],st[8],st[9],st[10]))     
        # except sqlite3.IntegrityError:
        #     print("Error")
        # except Exception as e:
        #     print(e)

    statics_db.commit()

def reset_statics():
    for member in staff_tables:
        try:
            cr.execute(f"update '{member}' set total_money = 0.0, number_of_chapters = 0, bonus = 0.0, penalty= 0.0 ")
            saving()
        except Exception as e:
            print(e)
        else:
            print("The Statics Has Been Reset Successfully")


# -----------------------------------------------------------------------------------------------
# The Old Statics

def get_old_statics_tables():
    with sqlite3.connect("statices.db") as db:
        cr = db.cursor()
        cr.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cr.fetchall()
        return [table[0] for table in tables]

def get_old_statics_data(table_name):
    with sqlite3.connect("statices.db") as db:
        cr = db.cursor()
        cr.execute(f"SELECT unique_name, total_money, payment_method, payment_link FROM '{table_name}'")
        return cr.fetchall()
    
# -------------------------------------------------------------------------------------------------------------------------------

def check_member(member,role):
    cr.execute(f"select unique_name from {role} where unique_name = '{member}'" )
    result=cr.fetchone()
    if result:
        return True
    return False

# Shift Translator
# -------------------------------------------------------------------------------------------------------------------------------
def shift_chapter_tl(manhua_name,chapter_number,old_holder,new_holder):
    cr.execute(f"select rawprof_st, translate_st, tl_money from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()



    old_holder_check=check_member(old_holder,"translator")
    new_holder_check=check_member(new_holder,"translator")

    if old_holder_check or old_holder in ["volt8756","ms_17"]:
        if new_holder_check or new_holder in ["volt8756","ms_17"]:
            if isinstance(fetched_chapter,tuple):
                if fetched_chapter[0] =="done":
                    if fetched_chapter[1] == "done":

                        cr.execute(f"update '{manhua_name}' set chapter_translator = '{new_holder}' where chapter = {chapter_number}")
                        try:
                            cr.execute(f"select number_of_chapters, total_money from translator where unique_name = '{new_holder}'")
                            translator_income=cr.fetchone()

                            cr.execute(f"update translator set number_of_chapters = {translator_income[0]+1} where unique_name = '{new_holder}'")
                            cr.execute(f"update translator set total_money = {translator_income[1]+fetched_chapter[2]} where unique_name = '{new_holder}'")
                            print("the new one is done")
                        
                        except Exception as e:
                            print(e)
                            return f"Error Happend While Shifting The Chapter:{e}"

                        if old_holder not in ["volt8756","ms_17"]:
                            try:
                                cr.execute(f"select number_of_chapters, total_money from translator where unique_name = '{old_holder}'")
                                translator_income=cr.fetchone()

                                cr.execute(f"update translator set number_of_chapters = {translator_income[0]-1} where unique_name = '{old_holder}'")
                                cr.execute(f"update translator set total_money = {translator_income[1]-fetched_chapter[2]} where unique_name = '{old_holder}'")

                            except Exception as e:
                                print(e)
                                return "Error Happend While Shifting The Chapter"

                        saving()

                        return f"Chapter {chapter_number} Has Been Shifted From **``{old_holder}``**  To **``{new_holder}``**."
                    
                    else:
                        return "The Chapter Is Not Translated To Be Shifted."
                else:
                    return "The Chapter Is Not Out To Be Shifted."
            else:
                return "The Chapter Is Not Out To Be Shifted."
            
        else: return "The New Holder Is Not A Translator"

    else: return "The Old Holder Is Not A Translator"

# Shift Editor
# -------------------------------------------------------------------------------------------------------------------------------
def shift_chapter_ed(manhua_name,chapter_number,old_holder,new_holder):
    cr.execute(f"select prof_st, edit_st, ed_money from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()

    old_holder_check=check_member(old_holder,"editors")
    new_holder_check=check_member(new_holder,"editors")

    if old_holder_check or old_holder in ["volt8756","ms_17"]:

        if new_holder_check or new_holder in ["volt8756","ms_17"]:

            if isinstance(fetched_chapter,tuple):
                if fetched_chapter[0] =="done":
                    if fetched_chapter[1]=="done":    
                        cr.execute(f"update '{manhua_name}' set chapter_editor = '{new_holder}' where chapter = {chapter_number}")

                        # New Holder Update
                        try:
                            cr.execute(f"select number_of_chapters, total_money from editors where unique_name = '{new_holder}'")
                            editor_income=cr.fetchone()

                            cr.execute(f"update editors set number_of_chapters = {editor_income[0]+1} where unique_name = '{new_holder}'")
                            cr.execute(f"update editors set total_money = {editor_income[1]+fetched_chapter[2]} where unique_name = '{new_holder}'")

                        except TypeError :
                            return f"{new_holder} Is Not An Editor"
                        
                        except Exception as e:
                            print(e)
                            return "Error Happend While Shifting The Chapter"
                        
                        # Old Holder Update
                        try:
                            cr.execute(f"select number_of_chapters, total_money from editors where unique_name = '{old_holder}'")
                            editor_income=cr.fetchone()

                            cr.execute(f"update editors set number_of_chapters = {editor_income[0]-1} where unique_name = '{old_holder}'")
                            cr.execute(f"update editors set total_money = {editor_income[1]-fetched_chapter[2]} where unique_name = '{old_holder}'")

                        except TypeError :
                            return f"{new_holder} Is Not An Editor"
                        
                        except Exception as e:
                            print(e)
                            return "Error Happend While Shifting The Chapter"
                        
                        saving()
                        return f"Chapter {chapter_number} Has Been Shifted From **``{old_holder}``**  To **``{new_holder}``**."
                    
                    else:
                        return "The Chapter Is Not Edited To Be Shifted."
                else:
                    return "The Chapter Is Not Proofreaded To Be Shifted."
            else:
                return "The Chapter Is Not Out To Be Shifted."
            
        else: return "The New Holder Is Not An Editor"

    else: return  "The Old Holder Is Not An Editor"  

# -------------------------------------------------------------------------------------------------------------------------------

def shift_rp(manhua_name,chapter_number,old_holder,new_holder):

    cr.execute(f"select rawprof_st from '{manhua_name}' where chapter = {chapter_number}")
    fetched_chapter=cr.fetchone()

    old_holder_check=check_member(old_holder,"raw_provider")
    new_holder_check=check_member(new_holder,"raw_provider")

    if old_holder_check or old_holder in ["volt8756","ms_17"]:

        if new_holder_check or new_holder in ["volt8756","ms_17"]:    

            if isinstance(fetched_chapter,tuple):
                if fetched_chapter[0] == "done":

                    cr.execute(f"update '{manhua_name}' set chapter_rawprovider = '{new_holder}' where chapter ={chapter_number}")

                    # New Holder Update 
                    try:
                        cr.execute(f"select number_of_chapters, total_money from raw_provider where unique_name = '{new_holder}'")
                        rp_income=cr.fetchone()

                        cr.execute(f"update raw_provider set number_of_chapters = {rp_income[0]+1} where unique_name = '{new_holder}'")

                        if manhua_name in series_rates.keys():
                            cr.execute(f"update raw_provider set total_money = {rp_income[1]+float(series_rates[manhua_name][4])} where unique_name = '{new_holder}'")

                    
                    except TypeError :
                        return f"{new_holder} Is Not A Proofreader"
                    
                    except Exception as e:
                        print(e)
                        return "Error Happend While Shifting The Chapter"
                    
                    # Old Holder Update 
                    if old_holder not in ["volt8756","ms_17"]:
                        try:
                            cr.execute(f"select number_of_chapters, total_money from raw_provider where unique_name = '{old_holder}'")
                            rp_income=cr.fetchone()

                            cr.execute(f"update raw_provider set number_of_chapters = {rp_income[0]+1} where unique_name = '{old_holder}'")

                            if manhua_name in series_rates.keys():
                                cr.execute(f"update raw_provider set total_money = {rp_income[1]+float(series_rates[manhua_name][4])} where unique_name = '{old_holder}'")

                        except TypeError :
                            return f"{new_holder} Is Not A Proofreader"
                        
                        except Exception as e:
                            print(e)
                            return "Error Happend While Shifting The Chapter"

                    saving()

                    return f"Chapter {chapter_number} Has Been Shifted From **``{old_holder}``**  To **``{new_holder}``**."

            else:
                return "The Chapter Is Not Out To Be Shifted."
    
        else: return "The New Holder Is Not A Raw Provider"

    else: return  "The Old Holder Is Not An Raw Provider"  



# Shift Proofreader
# -------------------------------------------------------------------------------------------------------------------------------
def shift_chapter_pr(manhua_name,chapter_number,old_holder,new_holder):

    cr.execute(f"select translate_st, prof_st, pr_money from '{manhua_name}' where chapter = '{chapter_number}'")
    fetched_chapter= cr.fetchone()

    old_holder_check=check_member(old_holder,"proofreader")
    new_holder_check=check_member(new_holder,"proofreader")
    
    if old_holder_check or old_holder in ["volt8756","ms_17"]:

        if new_holder_check or new_holder in ["volt8756","ms_17"]:    

            if isinstance(fetched_chapter,tuple):

                if fetched_chapter[0] =="done":

                    if fetched_chapter[1]=="done":
                        cr.execute(f"update '{manhua_name}' set chapter_proofreader = '{new_holder}' where chapter = {chapter_number}")

                        # New Holder Update
                        try:
                            cr.execute(f"select number_of_chapters, total_money from proofreader where unique_name = '{new_holder}'")
                            proofreader_income=cr.fetchone()    

                            cr.execute(f"update proofreader set number_of_chapters = {proofreader_income[0]+1} where unique_name = '{new_holder}'")
                            cr.execute(f"update proofreader set total_money = {proofreader_income[1]+fetched_chapter[2]} where unique_name = '{new_holder}'") 

                        except TypeError :
                            return f"{new_holder} Is Not A Proofreader"
                        
                        except Exception as e:
                            print(e)
                            return "Error Happend While Shifting The Chapter"

                        # Old Holder Update
                        if old_holder not in ["volt8756","ms_17"]:
                            try:
                                cr.execute(f"select number_of_chapters, total_money from proofreader where unique_name = '{old_holder}'")
                                proofreader_income=cr.fetchone()    

                                cr.execute(f"update proofreader set number_of_chapters = {proofreader_income[0]-1} where unique_name = '{old_holder}'")
                                cr.execute(f"update proofreader set total_money = {proofreader_income[1]-fetched_chapter[2]} where unique_name = '{old_holder}'") 

                            except TypeError :
                                return f"{new_holder} Is Not A Proofreader"
                            
                            except Exception as e:
                                print(e)
                                return "Error Happend While Shifting The Chapter"

                        saving()

                        return f"Chapter {chapter_number} Has Been Shifted From **``{old_holder}``**  To **``{new_holder}``**."
                    
                    else:
                        return "The Chapter Is Not Proofreaded To Be Shifted."
                else:
                    return "The Chapter Is Not Translated To Be Shifted."
            else:
                return "The Chapter Is Not Out To Be Shifted."

        else: return "The New Holder Is Not A ProofReader"

    else: return  "The Old Holder Is Not An Raw ProofReader"  

# -------------------------------------------------------------------------------------------------------------------------------

def rename_manhua_table(old_name, new_name):
    try:
        # Rename the table
        cr.execute(f"ALTER TABLE '{old_name}' RENAME TO '{new_name}'")
        saving()
        return True
    except sqlite3.OperationalError as e:
        print(f"Error renaming table: {e}")
        return False
    

# -------------------------------------------------------------------------------------------------------------------------------

def generate_csv_file(headers, data):
    csv_file = io.StringIO()
    writer = csv.DictWriter(csv_file, fieldnames=headers)
    writer.writeheader()
    for member in data:
        writer.writerow({"Name": member[0], "Total Money": member[1], "Payment Method": member[2], "Payment Link": member[3]}) 
    csv_file.seek(0)  
    csv_bytes = io.BytesIO(csv_file.getvalue().encode())    
    csv_file.close()
    return csv_bytes


def add_member(role, unique_name, name):
    try:
        cr.execute(f"insert into {role} values (?,?,?,?,?,?,?,?,?,?,?)",(unique_name,name,0,0.0,"none","none","none","none",0.0,0.0,"none"))
        saving()
    except Exception as e:
        print(e)

def get_channel_role_id(channel):
    try:
        cr.execute(f"select role_id from '{channel}'")
        result= cr.fetchone()
    except Exception as e:
        print(e)
    else:
        return result

def get_notify_counter(role,table,chapter):
    if role == "tl":
        cr.execute(f"select notify_tl_deadline from '{table}' where chapter = {chapter}")
        result=cr.fetchone()
    elif role == "pr" : 
        cr.execute(f"select notify_pr_deadline from '{table}' where chapter = {chapter}")
        result=cr.fetchone()
    elif role == "ed":
        cr.execute(f"select notify_ed_deadline from '{table}' where chapter = {chapter}")  
        result=cr.fetchone()  

    return result[0]

def add_notify_counter(role,table,chapter):
    try:
        if role == "tl":
            cr.execute(f"update '{table}' set notify_tl_deadline = 1 where chapter = {chapter}")
        elif role == "pr" : 
            cr.execute(f"update '{table}' set notify_pr_deadline = 1 where chapter = {chapter}")
        elif role == "ed":
            cr.execute(f"update '{table}' set notify_ed_deadline = 1 where chapter = {chapter}")
        saving()
    except Exception as e:
        print(e)



def get_series_info(manhua):
    try:
        cr.execute(f"select ass_tl, ass_pr, ass_ed from '{manhua}'")
        result=cr.fetchone()
    except Exception as e:
        print(e)
    else:
        return result


def delete_chapter(manhua,chapter):
    try:
        cr.execute(f"select {chapter} from '{manhua}' where chapter = {chapter}")
        checking_state=cr.fetchone()

        if checking_state:

            cr.execute(f"delete from '{manhua}' where chapter= {chapter}")
            saving()
            return f"Chapter {chapter} Is Successfully Deleted. "
            
        else:
            return "The Chapter Is Not Found To Delete."
        
    except Exception as e :
        print(e)
    