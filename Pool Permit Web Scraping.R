library(tidyverse)
library(openxlsx)
library(lubridate)

pool <- read_csv("pool_permits_Monroe_FL.csv")

pool_dates <- pool %>% 
  mutate(`Apply Date` = as_date(pool$`Apply Date`, format = "%m-%d-%Y"),
         `Permit Issue` = as_date(pool$`Permit Issue`, format = "%m-%d-%Y")
         )

write.xlsx(pool_dates, "pool_permits_Monroe_FL.xlsx")
