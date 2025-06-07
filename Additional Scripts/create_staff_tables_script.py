import sqlite3
import csv



db=sqlite3.connect("manhua.db")
cr=db.cursor()

cr.execute('''create table if not exists translator 
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
            payment_link string,
            UNIQUE(unique_name))''')

cr.execute('''create table if not exists proofreader 
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
            payment_link string,
            UNIQUE(unique_name))''')

cr.execute('''create table if not exists editors 
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
            payment_link string,
            UNIQUE(unique_name))''')

cr.execute('''create table if not exists raw_provider
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
            payment_link string,
            UNIQUE(unique_name))''')

