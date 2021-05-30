#import csv
import numpy as np
from datetime import timedelta
import os
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

import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler

PATH = "C:\\Program Files (x86)\\chromedriver.exe"
driver = webdriver.Chrome(PATH)

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
        print("Scraping page " + str(page))
        time.sleep(random.randint(3, 4))
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
                value = driver.find_element_by_xpath(
                    "/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr["+str(r)+"]/td["+str(c)+"]").text
                values_list[c - 1].append(value)

    driver.quit()

    print("Header Length: " + str(len(header_list)))
    print("Header List:")
    print(header_list)
    values_length = len(values_list[1])
    print("Number of rows: " + str(values_length))

    # create dataframe from dictionary
    monroe_df = pandas.DataFrame(dict(zip(header_list, values_list)))

    # convert dates from string to Datetime
    monroe_df['Apply Date']= pandas.to_datetime(monroe_df['Apply Date'], format = '%m-%d-%Y', errors = 'coerce')
    monroe_df['Permit Issue']= pandas.to_datetime(monroe_df['Permit Issue'], format = '%m-%d-%Y', errors = 'coerce')

    # end timer
    toc = timedelta(seconds=time.perf_counter() - tic)
    print("Scraped monroe county in: ", toc)

    monroe_df['County'] = 'monroe'
    monroe_df['State'] = 'FL'

    return monroe_df

def scrape_maricopa():
    """Scrapes pool permits from Maricopa, AZ and returns a dataframe"""

    url = "https://accela.maricopa.gov/CitizenAccessMCOSS/Cap/CapHome.aspx?module=PnD&TabName=PnD"
    driver.get(url)

    # set type and date parameters
    # we want: 
    #   Commercial Pools and Spas
    #   Expedited Models - Pools and Spas
    #   Expedited Pools and Spas
    #   Residential Pools and Spas

    types = ["Commercial Pools and Spas", 
             "Expedited Models - Pools and Spas",
             "Expedited Pools and Spas",
             "Residential Pools and Spas"]
    
    start_date = driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_txtGSStartDate")
    start_date.send_keys("01011990")

    for i in range(0, len(types)):
        permit_type = Select(driver.find_element_by_id("ctl00_PlaceHolderMain_generalSearchForm_ddlGSPermitType"))
        permit_type.select_by_visible_text(types[i])

        time.sleep(random.randint(2, 3))

        search_button = driver.find_element_by_id("ctl00_PlaceHolderMain_btnNewSearch")
        search_button.click()

        time.sleep(random.randint(4, 6))

        try:
            next_button = driver.find_element_by_partial_link_text("Next")
        except:
            next_enabled = False
        else:
            next_enabled = True

        while(next_enabled):
            time.sleep(random.randint(3, 4))
            try:
                next_button = driver.find_element_by_partial_link_text("Next")
            except:
                print("Reached last page.")
                next_enabled = False
            else:
                next_button.click()
                # Problem: stale element reference exception or click intercepted exception
                # wait times after clicking next increase as the page numbers get higher
                # implicit waiting isn't enough, must use explicit

def scrape_clark():
    url = "https://citizenaccess.clarkcountynv.gov/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building"
    driver.get(url)

    types = ["Commercial Pool",
             "Commercial Spa",
             "Residential Pools Spas Water Features"]

def scrape_wake():
    url = "https://energovcitizenaccess.tylertech.com/WakeCountyNC/SelfService#/search"
    driver.get(url)

    # must select Permit and Advanced to get to type
    types = ["Commercial Pool, Spa or Hot Tub",
             "Public Pool Permit",
             "Residential Pool, Spa & Hot Tub"]

    type_select = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "SearchModule")))


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
    for i in range(0, len(urls)):
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
            df.rename({'Record Number' : 'Permit Number', 'Record Type' : 'Permit Type'}, 
                      axis = "columns",
                      inplace = True)
        if 'Application Date' in df.columns:
            df.rename({'Application Date' : 'Date'}, axis = "columns", inplace = True)

        # TODO: manually filter san_mateo by Permit Type = "Building Permit" 
        # and description contains "pool" case-insensitive
        # Problem: no apparent effect
        if (counties[i] == 'san_mateo'):
            df = df[('pool' in df['Description'].str.contains('pool', case = False)) & 
                    (df['Permit Type'] == 'Building Permit')]

        site_frames.append(df)

        toc = timedelta(seconds=time.perf_counter() - tic)
        print("Scraped " + counties[i] + " county in: ", toc)

    multiple_site_df = concat(site_frames)
    return multiple_site_df

d = scrape_csv()

print(d)

d.to_csv(path_or_buf = cwd + '\\data\\1.csv')

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