import csv
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

# Set dropdown menus and search
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

# scrape first page
for r in range(1, rows + 1):
    for c in range(1, cols + 1):
        value = driver.find_element_by_xpath(
            "/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr["+str(r)+"]/td["+str(c)+"]").text
        values_list.append(value)

# get next button
next_button_link = driver.find_element_by_link_text("Next") # actually click this
next_button = driver.find_element_by_id("permits-result_next") # use only to see if disabled
next_enabled = "disabled" not in next_button.get_attribute("class")

while(next_enabled):
    next_button_link.click()
    time.sleep(random.randint(2, 10))
    next_button_link = driver.find_element_by_link_text("Next")
    next_button = driver.find_element_by_id("permits-result_next") 
    next_enabled = "disabled" not in next_button.get_attribute("class")
    if(not next_enabled):
        # recalculate rows
        rows = len(driver.find_elements_by_xpath("/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr"))
        print("Rows on Last Page: " + str(rows))

    #scrape table page
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            value = driver.find_element_by_xpath(
                "/html/body/div[2]/div/div[2]/div/div/div/div[2]/div/table/tbody/tr["+str(r)+"]/td["+str(c)+"]").text
            values_list.append(value)

print("Header Length: " + str(len(header_list)))
print(header_list)
values_length = len(values_list)
print("Values Length: " + str(values_length))

# write to csv
with open('pool_permits_Monroe_FL.csv', mode='w', newline = '') as pool_file:
    pool_writer = csv.writer(pool_file, delimiter=',', quotechar='"')

    pool_writer.writerow(header_list)
    for i in range(0, values_length, cols):
        pool_writer.writerow(values_list[i:i+cols])

driver.quit()

### Maricopa County, Arizona
# Do we want both residential and commercial?
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
# Has a download button for csv

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
