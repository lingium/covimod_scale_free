# covimod data preprocessing script

# Preamble ----
# the covimod preprocess wave 33 dataset script

# Load the required packages----
require(data.table)
# require(optparse)
require(ggplot2)

# library(tidyverse)

args <- list()
args$seed <- 18L
#
#
# Load data----
args$infile.data <- file.path( "data",'COVIMOD', "COVIMOD_data_2022-03-21.RData") # get the gender and id of the respondents
args$prj.dir <- here::here()
args$out.dir <- here::here()
load(file.path(args$prj.dir, args$infile.data))

# Convert to data.table
dt.hh <- as.data.table(hh_data)
dt.nhh <- as.data.table(non_hh_data)
dt.part <- as.data.table(part_data)

# # region
# unique(dt.part$kreis_0)
# length(unique(dt.part$kreis_0))

# Convert from character to binary
# dt.hh[, hh_met_this_day := ifelse(hh_met_this_day == "Yes", 1, 0)]

# Preprocess the participant information----
dpart <- subset(dt.part, select = c('new_id', 'wave_0', 'date', 'age_0', 'age_group', 'sex'))
setnames(dpart, c('new_id', 'wave_0', 'age_0', 'sex'),
         c('pt.id', 'wave', 'part.age', 'part.sex'))
dpart[is.na(part.age), table(age_group)]

# check the time of the first 20 waves
t.wave <- unique(dpart[, list(wave, date)])
setkey(t.wave, wave)
t.wave[wave <= 20]

#

tmp <- subset(dpart, !is.na(part.age) & part.sex %in% c('Female', 'Male'), select = c(pt.id, part.age, part.sex, wave))
length(unique(tmp$pt.id))
tmp[, list(part = .N), by = wave]
saveRDS(tmp, file = file.path(args$prj.dir, 'data', 'COVIMOD', 'simulate_part.rds'))
# Impute for age----
runif.int <- function(min, max) floor(runif(1, min = min, max = max + 0.999))
dpart[, part.age := ifelse(age_group == '<1', '0', part.age)]
length(unique(dpart$pt.id))
dpart[, table(wave, part.sex)]
# ignore those didn't report age groups
tmp <- unique(subset(dpart, is.na(part.age) & grepl('-', age_group), select = c(pt.id, age_group, wave)))

# TODO: take care of people who passed the birthday
# dpart[pt.id == '011fac11'] f9bfe3af
tmp[, min_age := as.numeric(unlist(lapply(strsplit(age_group, "-"),'[' ,1)))]
tmp[, max_age := as.numeric(unlist(lapply(strsplit(age_group, "-"),'[' ,2)))]
tmp[, part.age := runif.int(min_age, max_age), by = 'pt.id']
set(tmp, NULL, c('min_age', 'max_age'), NULL)
tmp[, label := 'impute']

rep.age <- dpart[!is.na(part.age)]
rep.age <- subset(rep.age, pt.id %in% tmp$pt.id, select = c(pt.id, part.age, age_group, wave))
rep.age[, label := 'report']
rep.age <- rbind(tmp[pt.id %in% rep.age$pt.id], rep.age)
setkey(rep.age, pt.id, wave)
rep.age
unique(rep.age$pt.id)

# correct the imputed age
rep.age[label == 'report', part.age.correct := part.age]

set(rep.age, which(is.na(rep.age$part.age.correct) & rep.age$age_group == '1-4'), 'part.age.correct', 1L )
tmp2 <- rbind(unique(dpart[!is.na(part.age), list(pt.id, wave, part.age)]), tmp[, list(pt.id, wave, part.age)])
set(dpart, NULL, 'part.age', NULL)
dpart <- merge(dpart, tmp2, by = c('pt.id', 'wave'), all.x = TRUE)
dpart$part.age <- as.integer(dpart$part.age)
setkey(dpart, date, wave, part.age, part.sex)
saveRDS(dpart, file = file.path(args$prj.dir, 'data', 'COVIMOD', 'part.rds'))
