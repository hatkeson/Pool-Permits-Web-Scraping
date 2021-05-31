library(robotstxt)
library(lubridate)
library(magrittr)
library(tidyverse)
library(openxlsx)
library(here)

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

sum(is.na(pool_permits$Address))

pool_permits_trimmed <- pool_permits %>% 
  select(Date, `Permit Number`, `Permit Type`, Status, Address, County, State)

sum(is.na(pool_permits_trimmed))
sum(is.na(pool_permits_trimmed$Date)) # missing dates for monroe, contra costa
sum(is.na(pool_permits_trimmed$Status))

pool_permits_trimmed %>% 
  filter(County == 'contra_costa') %>% 
  nrow

pool_permits <- read_csv("Pool Permits/data/pool_permits.csv")


# use R to join dataframes

# monroe
monroe <- read_csv("Pool Permits/data/monroe.csv")
wake <- read_csv("Pool Permits/data/wake.csv")
csv <- read_csv("Pool Permits/data/csv.csv")

trimmed_csv <- csv %>% 
  select(Date, `Permit Number`, `Permit Type`, Status, Address, County, State)

trimmed_monroe <- monroe %>% 
  select(Date, `Permit Number`, Type, Status, Address, County, State) %>% 
  rename(`Permit Type` = Type)

trimmed_wake <- wake %>% 
  select(Date, `Permit Number`, `Permit Type`, Status, Address, County, State)

full <- rbind(trimmed_csv, trimmed_monroe, trimmed_wake)

full_na <- full[rowSums(is.na(full)) > 0,]
nrow(full_na) # 528 entries have at least 1 value missing

# by variable and county, how many values are missing?
full %>% 
  group_by(County) %>% 
  summarise(date_na = sum(is.na(Date)),
            status_na = sum(is.na(Status)),
            type_na = sum(is.na(`Permit Type`)),
            number_na = sum(is.na(`Permit Number`)),
            address_na = sum(is.na(Address))) 

write.xlsx(full, here::here("eight_counties.xlsx"))
write.csv(full, here::here("eight_counties.csv"))


# histogram by year for 2019 - 2020

full %>% 
  filter(year(Date) >= 2019) %>% 
  mutate(month = month(Date, label = TRUE),
         month = as.factor(month),
         year = as.factor(year(Date))) %>% 
  ggplot(aes(x = month)) +
  geom_bar() +
  facet_grid(cols = vars(year)) +
  labs(y = "Pool Permit Applications",
       x = "Month",
       title = "Pool Permit Applications by Month",
       caption = "Data gathered on May 30th, 2021")

full %>%
  mutate(County = as.factor(County),
         State = as.factor(State)) %>% 
  group_by(County) %>% 
  ggplot(aes(y = County)) +
  geom_bar() + 
  labs(title = "Pool Permits by County, 1987 - Present",
       y = "County",
       x = "Pool Permit Applications", 
       caption = "Data gathered on May 30th, 2021")
  
full %>%
  filter(year(Date) >= 2019) %>% 
  mutate(County = as.factor(County),
         State = as.factor(State)) %>% 
  group_by(County) %>% 
  ggplot(aes(y = County)) +
  geom_bar() + 
  labs(title = "Pool Permits by County, 2019 - Present",
       y = "County",
       x = "Pool Permit Applications",
       caption = "Data gathered on May 30th, 2021")

# how many entries have a type that contain "Residential" or "Commercial"?
full %>% 
  filter(str_detect(string = `Permit Type`, 
                    pattern = regex('residential', ignore_case = T))) %>% 
  distinct(County)
# monroe and san mateo don't tag residential in type

full %>% 
  filter(str_detect(string = `Permit Type`, 
                    pattern = regex('commercial', ignore_case = T))) %>% 
  distinct(County)
# same, monroe and san mateo don't tag

commercial_residential_proportions <- full %>% 
  filter(!is.na(Date)) %>% 
  mutate(after_2019 = case_when(year(Date) > 2019 ~ TRUE,
                                year(Date) <= 2019 ~ FALSE),
         comm_or_res = case_when(str_detect(string = `Permit Type`, 
                                            pattern = regex('commercial', ignore_case = T)) ~ "Commercial",
                                 str_detect(string = `Permit Type`, 
                                            pattern = regex('residential', ignore_case = T)) ~ "Residential",
                                 TRUE ~ "Unknown")) %>% 
  group_by(after_2019, comm_or_res) %>% 
  summarize(count = n()) %>% 
  mutate(proportion = count / sum(count))

write.xlsx(commercial_residential_proportions, 
           here::here("commercial_residential_proportions.xlsx"))
