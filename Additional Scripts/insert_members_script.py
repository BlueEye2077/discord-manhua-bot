import ast
import sqlite3

db= sqlite3.connect("manhua.db")

cr=db.cursor()

cr.execute("select name from sqlite_master where type='table'")
table_names=cr.fetchall()  


def num1():
    for table in table_names:
        table=table[0]
        if table in ["translator","proofreader","editors","raw_provider"]:
            cr.execute(f"select * from '{table}'")
            data=cr.fetchall()
            print(table)
            print(data)
            print('='*50)
            with open(fr"the great/{table}.txt","w") as file :
                file.writelines(str(data))

def num2():
    for table in table_names:
        table=table[0]
        if table not in ["translator","proofreader","editors","raw_provider"]:
            with open(fr"the great/{table}.txt") as file:
                print(table)
                # data=file.read()
                ddata = ast.literal_eval(file.read()) 
                print(len(ddata))
                for data in ddata:
                    print(data)
                    print(len(data))
                    cr.execute(f"insert into '{table}' values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, ?,?,?)", (data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13],data[14],data[15],data[16],data[17],data[18],data[19],data[20],data[21],data[22],data[23],data[24],data[25],data[26],data[27],0,0,0))
                    print('='*50)
                    db.commit()
                    print('its added')

# num2()

def num3():
    for table in table_names:
        table=table[0]
        if table in ["translator","proofreader","editors","raw_provider"]:
            with open(fr"the great/{table}.txt") as file:
                print(table)
                # data=file.read()
                ddata = ast.literal_eval(file.read()) 
                print(len(ddata))
                for data in ddata:
                    print(data)
                    print(len(data))
                    cr.execute(f"insert into '{table}' values (?,?,?,?,?,?,?,?,?,?,?)", (data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10]))
                    print('='*50)
                    db.commit()
                    print('its added')

num3()








