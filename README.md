# Pool-Permit-Web-Scraping
Web Scraping Project

This program takes the table from https://mcesearch.monroecounty-fl.gov/search/permits/ and scrapes it for all open pool and spa permits in Monroe County, Florida.
It first uses Selenium with Python to scrape and create a csv file, then uses an R script to convert the csv into a Microsoft Excel file. 

TODO:
Add the following websites:

Arizona:

·         https://accela.maricopa.gov/CitizenAccessMCOSS/Cap/CapHome.aspx?module=PnD&TabName=PnD

Nevada

·         https://citizenaccess.clarkcountynv.gov/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building

North Carolina

·         https://energovcitizenaccess.tylertech.com/WakeCountyNC/SelfService#/search

BUGS:

Martin County's information is tagged with San Mateo
Maricopa: next button becomes stale because wait times between pages increase with page number
San Mateo: download sometimes fails, use explicit wait
San Mateo: check if filtering actually works
 
