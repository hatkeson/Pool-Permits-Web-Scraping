from typing import Text
import numpy as np
from datetime import timedelta
import os
from os import path
import datetime
import glob
import pandas
import time
import random
from pandas.core.reshape.concat import concat
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from winreg import *

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException

import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler

total_tic = time.perf_counter()

PATH = "C:\\Program Files (x86)\\chromedriver.exe"
driver = webdriver.Chrome(PATH)
driver.implicitly_wait(10)

download_dir = ''
with OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
    download_dir = QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
print("Downloads Folder: " + download_dir)

cwd = os.getcwd()
print("Current Working Directory: " + cwd)

class MyEventHandler(FileSystemEventHandler):
    def __init__(self, observer):
        self.observer = observer

    def on_created(self, event):
        print("e=", event)
        if not event.is_directory:
            print ("file created")
            self.observer.stop()

def scrape_csv():
    # kern, charlotte, contra_costa, atlanta, martin, san_mateo
    urls = ["https://accela.co.kern.ca.us/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Home",
            "https://secureapps.charlottecountyfl.gov/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building",
            "https://epermits.cccounty.us/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building",
            "https://aca-prod.accela.com/atlanta_ga/Cap/CapHome.aspx?module=Building&TabName=Building",
            "https://aca-prod.accela.com/MARTINCO/Cap/CapHome.aspx?module=Building&TabName=Building",
            "https://aca-prod.accela.com/SMCGOV/Cap/CapHome.aspx?module=Building&TabName=Home"]    
    counties = ["kern", "charlotte", "contra_costa", "atlanta", "martin", "san_mateo"]
    states = ["CA", "FL", "CA", "GA", "FL", "CA"]

    types = [["City Commercial Pool",
              "City Residential Pool",
              "Commercial Pool",
              "Residential Pool"],
             ["Commercial Pool Heat Pump",
              "Commercial Swimming Pool",
              "Res Pool Heat Pump",
              "Residential Pool Solar System",
              "Residential Swimming Pool"],
             ["Building/Commercial/CP/Pool",
              "Building/Project/Pool/NA",
              "Building/Residential/P/Pool",
              "Building/Residential/SP/Spa"],
             ["Commercial Pool",
              "Residential Pool"],
             ["Commercial Jacuzzi/Spa",
              "Commercial Pool Deck",
              "Commercial Swimming Pool With Deck",
              "Residential Above Ground Pool",
              "Residential Jacuzzi/Spa",
              "Residential Pool Barrier",
              "Residential Pool Deck",
              "Residential Pool Enclosure",
              "Residential Pool Enclosure W/Slab",
              "Residential Swimming Pool No Deck",
              "Residential Swimming Pool With Deck"],
             ["San Mateo Dummy Value"]]
    site_frames = []
    for i in range(0, len(counties)):
        print("Scraping " + counties[i] + " county...")
        tic = time.perf_counter()

        driver.get(urls[i])

        time.sleep(random.randint(3, 5))

        start_date = driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_txtGSStartDate")
        start_date.send_keys("01011990")

        for j in range(0, len(types[i])):

            if (counties[i] != 'san_mateo'): # can't search san mateo by Permit Type, must filter manually (by Description, Type = 'Building Permit')
                permit_type = Select(driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_ddlGSPermitType"))
                permit_type.select_by_visible_text(types[i][j])

            time.sleep(random.randint(2, 3))

            search_button = driver.find_element_by_id("ctl00_PlaceHolderMain_btnNewSearch")
            search_button.click()

            time.sleep(5)

            download_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_gdvPermitListtop4btnExport")))

            download_button.click()

            # monitor downloads
            observer = Observer()
            event_handler = MyEventHandler(observer)
            observer.schedule(event_handler, download_dir, recursive=False)
            observer.start()
            observer.join()

            if (counties[i] == "san_mateo"):
                time.sleep(5)
            else:
                time.sleep(1)

            # get name of downloaded file
            list_of_files = glob.glob(download_dir + '\\*.csv') 
            latest_file = max(list_of_files, key=os.path.getctime)
            # Problem: fails on San Mateo, need a longer sleep
            print(latest_file)

            # move files to csv_files
            # remove illegal characters in types names
            if (counties[i] == 'san_mateo'):
                os.replace(latest_file, cwd + '\\data\\csv_files\\'+ counties[i] + '\\san_mateo.csv')
            else:
                time.sleep(1)
                if '/' in types[i][j]:
                    types[i][j] = types[i][j].replace('/', ' ')
                os.replace(latest_file, cwd + '\\data\\csv_files\\'+ counties[i] + '\\' + types[i][j] + ".csv")
            
        # take csv files, join them into a single dataframe
        if (counties[i] == 'san_mateo'):
            df = pandas.read_csv(cwd + '\\data\\csv_files\\' + counties[i] + '\\san_mateo.csv')
        else:
            frames = []
            for j in range(0, len(types[i])):
                c = pandas.read_csv(cwd + '\\data\\csv_files\\' + counties[i] + '\\' + types[i][j] + ".csv")
                frames.append(c)
            df = concat(frames)

        # tag with county and state
        df['County'] = counties[i]
        df['State'] = states[i]

        if 'Record Number' in df.columns:
            df.rename({'Record Number' : 'Permit Number', 
                       'Record Type' : 'Permit Type',
                       'File Date' : 'Date',
                       }, 
                      axis = "columns",
                      inplace = True)
        if 'Application Date' in df.columns:
            df.rename({'Application Date' : 'Date'}, axis = "columns", inplace = True)

        # manually filter san_mateo by Permit Type = "Building Permit"
        # and description contains "pool" case-insensitive
        if (counties[i] == 'san_mateo'):
            df = df[df['Permit Type'] == 'Building Permit']
            df = df[df['Description'].str.contains('pool', regex = False, case = False, na = False)]

        site_frames.append(df)

        toc = timedelta(seconds=time.perf_counter() - tic)
        print("Scraped " + counties[i] + " county in: ", toc)

    multiple_site_df = concat(site_frames)

    multiple_site_df['Date']= pandas.to_datetime(multiple_site_df['Date'], format = '%m/%d/%Y', errors = 'coerce')

    return multiple_site_df

def scrape_monroe():
    """Scrapes pool permits from Monroe County, FL from 1990 until now and returns a dataframe"""
    # start timer
    tic = time.perf_counter()

    # start driver
    url = "https://mcesearch.monroecounty-fl.gov/search/permits/"
    driver.get(url)

    # set search parameters - uncomment status to search for only Open permits
    permit_type = Select(driver.find_element_by_id("permit_type"))
    permit_type.select_by_visible_text("POOL & SPA")

    # if a file already exists, scrape using the day after the last entry
    file_exists = path.exists("data\\monroe.csv")
    if (file_exists):
        print("Monroe file exists: " + str(file_exists))
        # open the csv file and find the most recent date
        existing_file = pandas.read_csv("data//monroe.csv")
        existing_file['Date'] = pandas.to_datetime(existing_file['Date'])
        most_recent_date = existing_file['Date'].max()
        # input the day after that date into the start date for the search
        most_recent_date += datetime.timedelta(days=1)
        most_recent_date = most_recent_date.strftime("%m%d%Y")
        print("Most recent date: " + most_recent_date)
        date_from = driver.find_element_by_id("from")
        date_from.send_keys(most_recent_date)
        # must also set end date as today
        current_date = pandas.datetime.now().strftime("%m%d%Y")
        date_to = driver.find_element_by_id("to")
        date_to.send_keys(current_date)

    # status = Select(driver.find_element_by_id('status'))
    # status.select_by_visible_text('OPEN')

    results_length = Select(driver.find_element_by_name("permits-result_length"))
    results_length.select_by_visible_text("100")

    time.sleep(random.randint(2, 10))

    # get rows and columns of each page
    rows = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr"))
    print("Rows per Page: " + str(rows))

    cols = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr[1]/td"))
    print("Columns: " + str(cols))

    # scrape table header
    header_list = []
    for c in range(1, cols + 1):
        header = driver.find_element_by_xpath(
            "/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/thead/tr[1]/th["+str(c)+"]").text
        header_list.append(header)

    # scrape table body and click next until last page, sleep after each one
    value = ""
    values_list = []
    page = 1

    # scrape first page
    for c in range(1, cols + 1):
        col_list = []
        for r in range(1, rows + 1):
            value = driver.find_element_by_xpath(
                "/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr["+str(r)+"]/td["+str(c)+"]").text
            col_list.append(value)
        values_list.append(col_list)


    # get next button
    next_button_link = driver.find_element_by_link_text("Next") # actually click this
    next_button = driver.find_element_by_id("permits-result_next") # use only to see if disabled
    next_enabled = "disabled" not in next_button.get_attribute("class")

    # iterate over pages, scrape each 
    # takes approx. 10 min without Status tag
    while(next_enabled):
        next_button_link.click()
        page += 1
        # wait for loading screen
        loading = True
        while(loading):
            time.sleep(1)
            try:
                loading_screen = driver.find_element_by_id("overlayundefined")
            except NoSuchElementException:
                loading = False
        print("Scraping page " + str(page))
        # time.sleep(random.randint(3, 4))
        next_button_link = driver.find_element_by_link_text("Next")
        next_button = driver.find_element_by_id("permits-result_next") 
        next_enabled = "disabled" not in next_button.get_attribute("class")
        if(not next_enabled):
            # recalculate rows
            rows = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr"))
            print("Rows on Last Page: " + str(rows))
        #scrape table page
        for c in range(1, cols + 1):
            col_list = []
            for r in range(1, rows + 1):
                value = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr["+str(r)+"]/td["+str(c)+"]"))).text
                values_list[c - 1].append(value)


    print("Header Length: " + str(len(header_list)))
    print("Header List:")
    print(header_list)
    values_length = len(values_list[1])
    print("Number of rows: " + str(values_length))

    # create dataframe from dictionary
    monroe_df = pandas.DataFrame(dict(zip(header_list, values_list)))

    # convert dates from string to Datetime
    monroe_df.rename({'Apply Date' : 'Date'}, axis = "columns", inplace = True)

    # change to datetime after combining with all others
    monroe_df['Date']= pandas.to_datetime(monroe_df['Date'], format = '%m-%d-%Y', errors = 'coerce')
    monroe_df['Permit Issue']= pandas.to_datetime(monroe_df['Permit Issue'], format = '%m-%d-%Y', errors = 'coerce')

    # end timer
    toc = timedelta(seconds=time.perf_counter() - tic)
    print("Scraped monroe county in: ", toc)

    monroe_df['County'] = 'monroe'
    monroe_df['State'] = 'FL'

    if (file_exists):
        # append to existing file
        frames = [existing_file, monroe_df]
        monroe_df = concat(frames)

    return monroe_df

def scrape_maricopa():
    """Scrapes pool permits from Maricopa, AZ and returns a dataframe"""
    # estimated 17,000 entries in residential pool category, 
    # must iterate over 1,700 pages
    # 85 pages or 850 entries per year
    # at page 600, loading time is 30 seconds, assuming a linear increase of +0.05 sec/page
    # last page should take 850 seconds or 14 minutes
    url = "https://accela.maricopa.gov/CitizenAccessMCOSS/Cap/CapHome.aspx?module=PnD&TabName=PnD"
    driver.get(url)

    types = ["Commercial Pools and Spas", 
             "Expedited Models - Pools and Spas",
             "Expedited Pools and Spas",
             "Residential Pools and Spas"]
    
    start_date = driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_txtGSStartDate")

    # if a file already exists, scrape using the day after the last entry
    file_exists = path.exists("data\\maricopa.csv")
    if (file_exists):
        print("Maricopa file exists: " + str(file_exists))
        # open the csv file and find the most recent date
        existing_file = pandas.read_csv("data\\maricopa.csv")
        existing_file['Date'] = pandas.to_datetime(existing_file['Date'])
        most_recent_date = existing_file['Date'].max()
        # input the day after that date into the start date for the search
        most_recent_date += datetime.timedelta(days=1)
        most_recent_date = most_recent_date.strftime("%m%d%Y")
        print("Most recent date: " + most_recent_date)
        start_date.send_keys(most_recent_date)
        types = ["Residential Pools and Spas"]
    else:
        start_date.send_keys("01012010")
    # Maricopa and Clark only get 2010 because of their slow loading times, 
    # all others get 1990

    frames = []

    for i in range(0, len(types)):
        time.sleep(2)

        print("Scraping " + types[i])
        permit_type = Select(driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_ddlGSPermitType"))
        permit_type.select_by_visible_text(types[i])

        time.sleep(2)

        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_PlaceHolderMain_btnNewSearch")))
        search_button.click()

        time.sleep(random.randint(4, 6))

        next_button = driver.find_element_by_partial_link_text("Next")
        next_enabled = next_button.is_enabled()
        if not next_enabled:
            print("Reached last page.")
            # calculate rows
            count_str = driver.find_element_by_xpath('//*[@id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList"]/tbody/tr[1]/td/div/table/tbody/tr/td/span').text
            res = [int(k) for k in count_str.split() if k.isdigit()]
            count = res[1] - res[0]
            print("Elements on Page: " + str(count))
        else:
            count = 10
        
        # scrape first page
        date_list = []
        number_list = []
        status_list = []
        for r in range(2, count + 2):
            date_value = driver.find_element_by_id('ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl' + str(r).zfill(2) + '_lblUpdatedTime').text
            try:
                number_value = driver.find_element_by_id('ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl' + str(r).zfill(2) + '_lblPermitNumber1').text
                status_value = driver.find_element_by_id('ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl' + str(r).zfill(2) + '_lblStatus').text
            except NoSuchElementException:
                number_value = driver.find_element_by_id('ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl' + str(r).zfill(2) + '_lblPermitNumber').text
                status_value = np.NaN

            number_list.append(number_value)          
            date_list.append(date_value)
            status_list.append(status_value)

        while(next_enabled):
            next_button.click()
            # get loading message, wait for it to go away
            loading = driver.find_element_by_id("divGlobalLoading")
            loading_style = loading.get_attribute("style")
            while ("block" in loading_style):
                time.sleep(1)
                loading = driver.find_element_by_id("divGlobalLoading")
                loading_style = loading.get_attribute("style")
            try:
                next_button = driver.find_element_by_partial_link_text("Next")
            except NoSuchElementException:
                print("Reached last page.")
                count_str = driver.find_element_by_xpath('//*[@id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList"]/tbody/tr[1]/td/div/table/tbody/tr/td/span').text
                print(count_str)
                count_str = count_str.replace("-", " ")
                res = [int(k) for k in count_str.split() if k.isdigit()]
                print(res)
                count = res[1] - res[0] + 1
                print("Elements on Page: " + str(count))
                next_enabled = False
            # scrape page    
            for r in range(2, count + 2):
                print("Scraping row " + str(r))
                date_value = driver.find_element_by_id("ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblUpdatedTime").text 
                try:
                    number_value = driver.find_element_by_id("ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblPermitNumber1").text
                    status_value = driver.find_element_by_id("ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblStatus").text
                except NoSuchElementException:
                    # the ID starts with 21TMP, no status
                    number_value = driver.find_element_by_id("ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblPermitNumber").text
                    status_value = np.NaN

                number_list.append(number_value)          
                date_list.append(date_value)
                status_list.append(status_value)

        header_list = ["Date", "Permit Number", "Status"]
        value_list = [date_list, number_list, status_list]
        type_df = pandas.DataFrame(dict(zip(header_list, value_list)))

        # add permit type, county, state
        type_df['Permit Type'] = types[i]
        type_df['County'] = 'maricopa'
        type_df['State'] = 'AZ'
        frames.append(type_df)

    maricopa_df = pandas.concat(frames)
    maricopa_df['Date']= pandas.to_datetime(maricopa_df['Date'], format = '%m/%d/%Y', errors = 'coerce')

    if (file_exists):
        # append to existing file
        frames = [existing_file, maricopa_df]
        maricopa_df = concat(frames)


    return maricopa_df

def scrape_clark():
    url = "https://citizenaccess.clarkcountynv.gov/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building"
    driver.get(url)
    # 34,000 estimated results in Residential category
    types = ["Commercial Spa",
             "Commercial Pool",
             "Residential Pools Spas Water Features"]

    start_date = driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_txtGSStartDate")

    file_exists = path.exists("data\\clark.csv")
    if (file_exists):
        print("Maricopa file exists: " + str(file_exists))
        # open the csv file and find the most recent date
        existing_file = pandas.read_csv("data\\clark.csv")
        existing_file['Date'] = pandas.to_datetime(existing_file['Date'])
        most_recent_date = existing_file['Date'].max()
        # input the day after that date into the start date for the search
        most_recent_date += datetime.timedelta(days=1)
        most_recent_date = most_recent_date.strftime("%m%d%Y")
        print("Most recent date: " + most_recent_date)
        start_date.send_keys(most_recent_date)
        types = ["Residential Pools Spas Water Features"]

    else:
        start_date.send_keys("01012010")
    # clark and maricopa only get 2010, all others get 1990

    frames = []

    for i in range(0, len(types)):
        time.sleep(2)

        print("Scraping " + types[i])
        permit_type = Select(driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_ddlGSPermitType"))
        permit_type.select_by_visible_text(types[i])

        # get loading message, wait for it to go away
        loading = driver.find_element_by_id("divGlobalLoading")
        loading_style = loading.get_attribute("style")
        while ("block" in loading_style):
            time.sleep(1)
            loading = driver.find_element_by_id("divGlobalLoading")
            loading_style = loading.get_attribute("style")

        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_PlaceHolderMain_btnNewSearch")))
        search_button.click()

        time.sleep(random.randint(4, 6))

        
        next_button = driver.find_element_by_partial_link_text("Next")
        next_enabled = next_button.is_enabled()
        if not next_enabled:
            next_enabled = False
            print("Reached last page.")
            # calculate rows
            count_str = driver.find_element_by_xpath('//*[@id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList"]/tbody/tr[1]/td/div/table/tbody/tr/td[1]/span').text
            count_str = count_str.replace("-", " ")
            res = [int(k) for k in count_str.split() if k.isdigit()]
            count = res[1] - res[0]
            print("Elements on Page: " + str(count))
        else:
            count = 10

        number_list = []
        date_list = []
        status_list = []

        while(next_enabled):
            # get loading message, wait for it to go away
            loading = driver.find_element_by_id("divGlobalLoading")
            loading_style = loading.get_attribute("style")
            while ("block" in loading_style):
                time.sleep(1)
                loading = driver.find_element_by_id("divGlobalLoading")
                loading_style = loading.get_attribute("style")
            next_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Next")))
            next_button.click()
            # get loading message, wait for it to go away
            loading = driver.find_element_by_id("divGlobalLoading")
            loading_style = loading.get_attribute("style")
            while ("block" in loading_style):
                time.sleep(1)
                loading = driver.find_element_by_id("divGlobalLoading")
                loading_style = loading.get_attribute("style")
            try:
                next_button = driver.find_element_by_partial_link_text("Next")
            except NoSuchElementException:
                next_enabled = False
                print("Reached last page.")
                # calculate rows
                count_str = driver.find_element_by_xpath('//*[@id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList"]/tbody/tr[1]/td/div/table/tbody/tr/td[1]/span').text
                count_str = count_str.replace("-", " ")
                res = [int(k) for k in count_str.split() if k.isdigit()]
                count = res[1] - res[0] + 1
                print("Elements on Page: " + str(count))
            # scrape page    
            for r in range(2, count + 2):
                print("Scraping row " + str(r))

                date_value = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblUpdatedTime"))).text
                try:
                    number_value = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.ID, "ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblPermitNumber1"))).text
                    status_value = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.ID, "ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblStatus"))).text
                except TimeoutException:
                    # the ID starts with 21TMP, no status
                    number_value = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.ID, "ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_ctl" + str(r).zfill(2) + "_lblPermitNumber"))).text
                    status_value = np.NaN
                
                number_list.append(number_value)          
                date_list.append(date_value)
                status_list.append(status_value)

        header_list = ["Date", "Permit Number", "Status"]
        value_list = [date_list, number_list, status_list]
        type_df = pandas.DataFrame(dict(zip(header_list, value_list)))

        # add permit type, county, state
        type_df['Permit Type'] = types[i]
        type_df['County'] = 'clark'
        type_df['State'] = 'NV'
        frames.append(type_df)

    clark_df = pandas.concat(frames)
    clark_df['Date']= pandas.to_datetime(clark_df['Date'], format = '%m/%d/%Y', errors = 'coerce')

    if (file_exists):
        # append to existing file
        frames = [existing_file, clark_df]
        clark_df = concat(frames)


    return clark_df
            
def scrape_wake():
    url = "https://energovcitizenaccess.tylertech.com/WakeCountyNC/SelfService#/search"
    driver.get(url)

    # must select Permit and Advanced to get to type

    time.sleep(8)

    type_select = Select(driver.find_element_by_id("SearchModule"))
    type_select.select_by_visible_text("Permit")

    advanced_button = driver.find_element_by_id("button-Advanced")
    advanced_button.click()

    permit_type = Select(driver.find_element_by_id("PermitCriteria_PermitTypeId"))
    types = ["Commercial Pool, Spa or Hot Tub",
             "Public Pool Permit",
             "Residential Pool, Spa & Hot Tub"]
    date_from = driver.find_element_by_id("ApplyDateFrom")
    file_exists = path.exists("data\\clark.csv")
    if (file_exists):
        print("Maricopa file exists: " + str(file_exists))
        # open the csv file and find the most recent date
        existing_file = pandas.read_csv("data\\clark.csv")
        existing_file['Date'] = pandas.to_datetime(existing_file['Date'])
        most_recent_date = existing_file['Date'].max()
        # input the day after that date into the start date for the search
        most_recent_date += datetime.timedelta(days=1)
        most_recent_date = most_recent_date.strftime("%m/%d/%Y")
        print("Most recent date: " + most_recent_date)
        date_from.send_keys(most_recent_date)
        types = ["Residential Pool, Spa & Hot Tub"]
    else:
        date_from.send_keys("01/01/1990")

    frames = []

    for i in range(0, len(types)):
        permit_numbers = []
        applied_dates = []
        statuses = []
        addresses = []

        print("Scraping " + types[i] + "...")
        permit_type.select_by_visible_text(types[i])

        time.sleep(2)

        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "button-Search")))
        search_button.click()

        time.sleep(5)

        list_size = Select(driver.find_element_by_id("pageSizeList"))
        list_size.select_by_visible_text("100")

        time.sleep(2)

        next_button = driver.find_element_by_id("link-NextPage")
        parent_li = next_button.find_element_by_xpath("..")
        next_enabled = True
        parent_class = parent_li.get_attribute("class")
        if parent_class == "disabled":
            next_enabled = False
            print("Reached last page.")
            # last page, get rows
            count_str = driver.find_element_by_id("startAndEndCount").text
            # extract digits
            res = [int(k) for k in count_str.split() if k.isdigit()]
            count = res[1] - res[0]
            print("Elements on Page: " + str(count))
        else:
            count = 100
            
        # scrape first page
        for j in range(0, count):

            permit_number = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id=\"entityRecord" + str(j) + "\"]/a/tyler-highlight/span"))).text
            applied_date = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id=\"entityRecordDiv" + str(j) + "\"]/div[2]/div[3]/span"))).text
            status = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id=\"entityRecordDiv" + str(j) + "\"]/div[2]/div[8]/tyler-highlight/span"))).text
            address = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id=\"entityRecordDiv" + str(j) + "\"]/div[2]/div[11]/tyler-highlight/span"))).text
 
            permit_numbers.append(permit_number)
            applied_dates.append(applied_date)
            statuses.append(status)
            addresses.append(address)

        #iterate through pages
        while next_enabled and parent_class != "disabled":
            next_button = driver.find_element_by_id("link-NextPage")
            parent_li = next_button.find_element_by_xpath("..")
            parent_class = parent_li.get_attribute("class")
            if parent_class == "disabled":
                next_enabled = False
                print("Reached last page.")
                # last page, get rows
                count_str = driver.find_element_by_id("startAndEndCount").text
                # extract digits
                res = [int(k) for k in count_str.split() if k.isdigit()]
                count = res[1] - res[0]
            else:
                count = 100

            # scrape Permit Number, (Applied) Date, Status, Address
            # zero-based index
            for j in range(0, count):
                permit_number = driver.find_element_by_xpath("//*[@id=\"entityRecord" + str(j) + "\"]/a/tyler-highlight/span").text
                applied_date = driver.find_element_by_xpath("//*[@id=\"entityRecordDiv" + str(j) + "\"]/div[2]/div[3]/span").text
                status = driver.find_element_by_xpath("//*[@id=\"entityRecordDiv" + str(j) + "\"]/div[2]/div[8]/tyler-highlight/span").text
                address = driver.find_element_by_xpath("//*[@id=\"entityRecordDiv" + str(j) + "\"]/div[2]/div[11]/tyler-highlight/span").text

                permit_numbers.append(permit_number)
                applied_dates.append(applied_date)
                statuses.append(status)
                addresses.append(address)

            # click next button
            if next_enabled:
                next_button.click()

            time.sleep(5)

        # create a dataframe
        header_list = ["Permit Number", "Date", "Status", "Address"]
        value_list = [permit_numbers, applied_dates, statuses, addresses]

        type_df = pandas.DataFrame(dict(zip(header_list, value_list)))

        # add permit type, county, state
        type_df['Permit Type'] = types[i]
        type_df['County'] = 'wake'
        type_df['State'] = 'NC'

        frames.append(type_df)
        # weird: there seems to be more rows in the table than the website reports
        print(type_df)
    wake_df = pandas.concat(frames)

    wake_df['Date']= pandas.to_datetime(wake_df['Date'], format = '%m/%d/%Y', errors = 'coerce')

    if (file_exists):
        # append to existing file
        frames = [existing_file, wake_df]
        wake_df = concat(frames)

    return wake_df


csv_df = scrape_csv()
csv_df.to_csv("data\\csv.csv")

monroe_df = scrape_monroe()
print("Monroe Final")
print(monroe_df)
monroe_df.to_csv("data\\monroe.csv")

wake_df = scrape_wake()
print("Wake Final")
print(wake_df)
wake_df.to_csv("data\\wake.csv")

clark_df = scrape_clark()
print("Clark Final")
print(clark_df)
clark_df.to_csv("data\\clark.csv")

maricopa_df = scrape_maricopa()
print("Maricopa Final")
print(maricopa_df)
maricopa_df.to_csv("data\\maricopa.csv")

frames = [clark_df, maricopa_df, monroe_df, wake_df, csv_df]


final_frame = concat(frames)
final_frame = final_frame[['Date', 'Permit Number', 'Permit Type', 'Status', 'County', 'State']]
print(final_frame)

final_frame.to_excel("data\\pool_permits.xlsx")
final_frame.to_csv("data\\pool_permits.csv")

driver.quit()
total_toc = timedelta(seconds=time.perf_counter() - total_tic)

print("Total time elapsed: " + str(total_toc))


### Maricopa County, Arizona
# Not possible to search by status, but shows in results. Issued, Reissued, Final
# Application or Issue date is given, Expiration date looks sparse
# no download button

### Kern County, California
# Advanced Search -> Search for Records -> Building
# Status: Issued, Finaled, Reviewed
# One date given
# has a download button for csv

### San Mateo County, California
# Can't search for record type?
# POOL IS NOT IN RECORD TYPE, MUST SEARCH DESCRIPTION!!!
# Has a download button for csv

### Contra Costa County, California
# has downloadable csv

### Martin County, Florida
# Has permit types for pool deck, pool barrier, pool enclosure
# Has downloadable csv

### Charlotte County, Florida
# Can't search status
# has downloadable csv

### City of Atlanta, Georgia
# downloadable results

### Clark County, Nevada
# no downloadable results

### Wake County, North Carolina
# Do we want both commercial and residential?
# Can search status. What permit statuses do we want? Approved, Complete, Issued, Submitted?
# slow load time
# no dowloadable results

# Must only scrape 3 more websites, can use csv for others

# Kern, San Mateo, Martin, Charlotte, Contra Costa, Atlanta: 
# use selenium to get results and click download

# Monroe, Maricopa, Clark, Wake
# no download, must scrape each page