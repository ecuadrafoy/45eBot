from sqlalchemy import create_engine
import pandas as pd
from google.oauth2 import service_account
import pygsheets
import json
def gsheets():
    # Connect the Databases and modify the column date so it's suitable with Google Sheets
    engine = create_engine('sqlite:///official-db.db', echo=False)
    attendance = pd.read_sql_table('attendance', con=engine)
    member = pd.read_sql_table('member', con=engine)
    event = pd.read_sql_table('event', con=engine)
    event['date_only'] = event['date'].dt.strftime('%m/%d/%Y')

    # Merge event and attendance datasets, filter on holdfast only. 
    merge = attendance.merge(event, left_on='event_id', right_on='id')
    merge = merge.query('event_type == "Holdfast"')
    groupby = merge.groupby(['member_name','date_only']).size().reset_index()

    pivot = groupby.pivot(index = 'member_name', columns=['date_only'], values=0)
    pivot.loc[:,'Total'] = pivot.sum(numeric_only=True, axis=1)
    pivot = pivot.reset_index()

    groupby_players = merge.groupby(['member_name']).size().reset_index()
    groupby_players.columns = ['Name', 'Total Attendance']
    
    # Connect to the Google Sheets
    client = pygsheets.authorize(service_account_file='Blueprint-8b24adbab947.json')
    sheet = client.open_by_key('1CbmQXiiq1geK4s4gCzECsHyVItexH4DR0MBLVZy0ong')
    
    # Feed the data to Google Sheets
    wks = sheet.worksheet_by_title('DateEvents')
    wks.set_dataframe(pivot, start=(1,1))

    wks2 = sheet.worksheet_by_title('Aggregate')
    wks2.set_dataframe(groupby_players, start=(1,1))

