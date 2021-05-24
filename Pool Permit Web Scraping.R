library(robotstxt)

urls = c("https://mcesearch.monroecounty-fl.gov/search/permits/",
         "https://accela.maricopa.gov/CitizenAccessMCOSS/Cap/CapHome.aspx?module=PnD&TabName=PnD",
         "https://accela.kerncounty.com/CitizenAccess/Default.aspx", 
         "https://aca-prod.accela.com/SMCGOV/Cap/CapHome.aspx?module=Building&TabName=Home",
         "https://epermits.cccounty.us/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building",
         "https://aca-prod.accela.com/MARTINCO/Cap/CapHome.aspx?module=Building&TabName=Building",
         "https://secureapps.charlottecountyfl.gov/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building",
         "https://aca-prod.accela.com/atlanta_ga/Cap/CapHome.aspx?module=Building&TabName=Building",
         "https://citizenaccess.clarkcountynv.gov/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building",
         "https://energovcitizenaccess.tylertech.com/WakeCountyNC/SelfService#/search")

paths_allowed(urls)
