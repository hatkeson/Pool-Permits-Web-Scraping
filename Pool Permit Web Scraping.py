#import csv
import numpy as np
import pandas
import time
import random
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import Select

PATH = "C:\\Program Files (x86)\\chromedriver.exe"
driver = webdriver.Chrome(PATH)

### Monroe County, Florida
url = "https://mcesearch.monroecounty-fl.gov/search/permits/"

driver.get(url)

# Set dropdown menus and search - status no longer relevant
status = Select(driver.find_element_by_id('status'))
status.select_by_visible_text('OPEN')

permit_type = Select(driver.find_element_by_id('permit_type'))
permit_type.select_by_visible_text('POOL & SPA')

results_length = Select(driver.find_element_by_name("permits-result_length"))
results_length.select_by_visible_text("100")

time.sleep(random.randint(2, 10))

# scrape table
# get rows
rows = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr"))
print("Rows: " + str(rows))

# get columns
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

# iterate over pages, scrape each, takes approx. 10 min
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

print("Header Length: " + str(len(header_list)))
print("Header List:")
print(header_list)
values_length = len(values_list)
print("Number of rows: " + str(values_length))

# # write to csv
# with open('pool_permits_Monroe_FL.csv', mode='w', newline = '') as pool_file:
#     pool_writer = csv.writer(pool_file, delimiter=',', quotechar='"')

#     pool_writer.writerow(header_list)
#     for i in range(0, values_length, cols):
#         pool_writer.writerow(values_list[i:i+cols])

# write to xlsx (can't modify existing xlsx, so do at end?)
# workbook = xlsxwriter.Workbook('.xlsx')
# worksheet = workbook.add_worksheet()

# use pandas to write to xlsx
# create dict from values, use header for column names

# chop up values_list into 2D list of row x col
# initialize dict 
d = dict(zip(header_list, values_list))
print("Dictionary: ")
print(d)

df = pandas.DataFrame(data=d)
print(df)


driver.quit()

### Maricopa County, Arizona
# Do we want both residential and commercial?
# Not possible to search by status, but shows in results. Issued, Reissued, Final
# Application or Issue date is given, Expiration date looks sparse
# no download button

### Kern County, California
# Advanced Search -> Search for Records -> Building
# Status: Issued, Finaled, Reviewed
# POOL IS NOT IN RECORD TYPE, MUST SEARCH DESCRIPTION!!!
# One date given
# has a download button for csv

### San Mateo County, California
# Can't search for record type?
# Has a download button for csv

### Contra Costa County, California
# 

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

# Kern, San Mateo, Martin, Charlotte, Atlanta: 
# use selenium to get results and click download

# https://kaijento.github.io/2017/05/04/web-scraping-requests-eventtarget-viewstate/
# https://stackoverflow.com/questions/55918415/is-there-any-way-to-download-csv-file-from-website-button-click-using-python/55919705
# inspect the download button
# find name of Javascript function: _doPostBack
# https://stackoverflow.com/questions/42032932/python-requests-and-dopostback-function

# Download Results (element)
# <a id="ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList_gdvPermitListtop4btnExport" 
#  class="ACA_SmLabel ACA_SmLabel_FontSize" 
#  href="javascript:__doPostBack('ctl00$PlaceHolderMain$dgvPermitList$gdvPermitList$gdvPermitListtop4btnExport','');var p = new ProcessLoading();p.showLoading(false);">Download results</a>

# Use network tab in developer console, click download button to get form:
# ctl00$ScriptManager1: ctl00$PlaceHolderMain$dgvPermitList$updatePanel|ctl00$PlaceHolderMain$dgvPermitList$gdvPermitList$gdvPermitListtop4btnExport
# txtSearchCondition: Search...
# ctl00$HeaderNavigation$hdnShoppingCartItemNumber: 
# ctl00$HeaderNavigation$hdnShowReportLink: N
# ctl00$PlaceHolderMain$addForMyPermits$collection: rdoNewCollection
# ctl00$PlaceHolderMain$addForMyPermits$txtName: name
# ctl00$PlaceHolderMain$addForMyPermits$txtDesc: 
# ctl00$PlaceHolderMain$ddlSearchType: 0
# ctl00$PlaceHolderMain$generalSearchForm$txtGSPermitNumber: 
# ctl00$PlaceHolderMain$generalSearchForm$ddlGSPermitType: Building/Kern Residential/Pool/NA
# ctl00$PlaceHolderMain$generalSearchForm$txtGSProjectName: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate: 05/23/2001
# ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate_ext_ClientState: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSEndDate: 05/18/2021
# ctl00$PlaceHolderMain$generalSearchForm$txtGSEndDate_ext_ClientState: 
# ctl00$PlaceHolderMain$generalSearchForm$ddlGSCapStatus: 
# ctl00$PlaceHolderMain$generalSearchForm$ddlGSLicenseType: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSLicenseNumber: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSFirstName: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSLastName: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSBusiName: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSParcelNo: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSNumber$ChildControl0: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSNumber$ctl00_PlaceHolderMain_generalSearchForm_txtGSNumber_ChildControl0_watermark_exd_ClientState: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSNumber$ChildControl1: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSNumber$ctl00_PlaceHolderMain_generalSearchForm_txtGSNumber_ChildControl1_watermark_exd_ClientState: 
# ctl00$PlaceHolderMain$generalSearchForm$txtGSStreetName: 
# ctl00$PlaceHolderMain$generalSearchForm$ddlGSStreetSuffix: 
# ctl00$PlaceHolderMain$hfASIExpanded: 
# ctl00$PlaceHolderMain$txtHiddenDate: 
# ctl00$PlaceHolderMain$txtHiddenDate_ext_ClientState: 
# ctl00$PlaceHolderMain$dgvPermitList$lblNeedReBind: 
# ctl00$PlaceHolderMain$dgvPermitList$gdvPermitList$hfSaveSelectedItems: ,
# ctl00$PlaceHolderMain$dgvPermitList$inpHideResumeConf: 
# ctl00$PlaceHolderMain$hfGridId: 
# ctl00$HDExpressionParam: 
# Submit: Submit
# __EVENTTARGET: ctl00$PlaceHolderMain$dgvPermitList$gdvPermitList$gdvPermitListtop4btnExport
# __EVENTARGUMENT: 
# __LASTFOCUS: 
# __VIEWSTATE: Large hash value
# __VIEWSTATEGENERATOR: A9414CD7
# ACA_CS_FIELD: c5873908e7a245e6abd3457c4f2f0ac8
# __ASYNCPOST: true
# (empty)

# have to update __VIEWSTATE each time