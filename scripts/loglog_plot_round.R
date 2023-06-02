# Preamble ----
# preliminary analysis of the scale free analysis (log-log plot)
# covimod data preprocessing script
# analyse the number of non-household contacts + group contacts that first showing up participants
# 2023.3.23

# Load the required packages----
require(data.table)
require(ggplot2)
require(tidyverse)

args <- list()
args$seed <- 18L
#
#
# Load data----
args$infile.data <- file.path( "data",'COVIMOD', "COVIMOD_data_2022-03-21.RData") # get the gender and id of the respondents
args$prj.dir <- here::here()
args$out.dir <- here::here()
load(file.path(args$prj.dir, args$infile.data))

# load the participants data
dpart <- as.data.table(readRDS(file = file.path(args$prj.dir, 'data', 'COVIMOD', 'part.rds')))
# dpart <- dpart[part.sex %in% c('Female', 'Male') & (!is.na(part.age))]
setnames(dpart, 'pt.id', 'id')

# get the time of each survey round
tm <- unique(dpart[, list(wave, date)])
tm <- tm[, list(date.min = min(date),
                date.max = max(date)),
         by = 'wave']
# wave1-2: first lockdown
# wave3-12: relaxed measure
# wave13-20: second lockdown
# wave21-25: relaxed measures again
# wave26-: vaccination/testing checks

# change the wave to round times:
change_time <- function(data)
{
  data$round <- ifelse(data$wave %in% 1:2, 1,
                       ifelse(data$wave %in% 3:12, 2,
                              ifelse(data$wave %in% 13:20, 3,
                                     ifelse(data$wave %in% 21:25, 4, 5))))
  return(data)
}

round_descp <- function(data)
{
  data$round.pt <- ifelse(data$round == 1, 'survey wave 1-2',
                          ifelse(data$round == 2, 'survey wave 3-12',
                                 ifelse(data$round == 3, 'survey wave 13-20',
                                        ifelse(data$round == 4, 'survey wave 21-25', 'survey wave 26-33'))))

  return(data)
}

dpart <- change_time(dpart)
# Convert to data.table
# dt.hh <- as.data.table(hh_data)
dt.nhh <- as.data.table(non_hh_data)
dt.part <- as.data.table(part_data)

# process non-household
if (0)
{
unique(dt.nhh$age_group)
dt.nhh$age_group <- ifelse(dt.nhh$age_group %in% c("<1", "Under 1", "1-4"), "0-4",
                           ifelse(dt.nhh$age_group == "85 years or older", "85+", dt.nhh$age_group))
age_group_levels <- c("0-4","5-9","10-14","15-19","20-24","25-34","35-44",
                      "45-54","55-64","65-69","70-74","75-79","80-84","85+")
setnames(dt.nhh, old = c("age_group", "sex"), new = c("cont.age", "cont.sex"))
dt.nhh$cont.age <- factor(dt.nhh$cont.age, levels = age_group_levels)
dt.nhh$cont.sex <- factor(dt.nhh$cont.sex, levels = c('Male', 'Female'))

unique(dt.nhh$cont.age)
unique(dt.nhh$cont.sex)
}

# add group contacts ----
# including the unknown age and sex
unique(dt.part$sex)
unique(dt.part$age_group)

SDcols_Q75 <- c("Q75_u18_work", "Q75_u18_school", "Q75_u18_else",
                "Q75_1864_work", "Q75_1864_school", "Q75_1864_else",
                "Q75_o64_work", "Q75_o64_school", "Q75_o64_else")
dt.part[, y_grp := rowSums(.SD, na.rm = T), .SDcols = SDcols_Q75]
dt.part[y_grp > 60, y_grp := 60]
dt.grp.all <- dt.part[, .(grp.cntcts = sum(y_grp)), by=.(wave_0, age_group, sex, new_id)]
setnames(dt.grp.all, c("wave_0", 'new_id'), c("wave", 'id'))
setkey(dt.grp.all, id, wave)
dt.grp.all[, rp.nb.grp := seq_len(length(grp.cntcts)), by = 'id']
# dt.grp.all <- dt.grp.all[rp.nb == 1]
tmp <- dt.grp.all[, list(t.part = .N),
                 by = 'wave']
sum(tmp$t.part)
# 7851 participants first join this survey
# 59585 participants join this survey reporting group contacts

# # fill in the missing age infor
# unique(dpart[, list(id, wave)])
# # 59414
# unique(dt.grp.all[, list(id, wave)])
# #  59585

# non-household contacts
tlb.nhh <- dt.nhh[,
                  list(cntcts = .N),
                  by = c('wave', 'new_id')]
setnames(tlb.nhh, 'new_id', 'id')
setkey(tlb.nhh, id, wave)
tlb.nhh[, rp.nb := seq_len(length(cntcts)), by = 'id']
# tlb.nhh <- tlb.nhh[rp.nb == 1]

# tlb.nhh is the individual level dataset

# Similar to Fig2 ----
# stratified by wave
# similar to FIG2 referred to backer paper
# we are interested in participants who are in the survey at the first time
if (0)
{
  df.f1.nhh <- tlb.nhh[rp.nb == 1]
  tmp <- df.f1.nhh[, list(t.part = .N),
                   by = 'wave']
  sum(tmp$t.part)
  # 15945 cntcts
  # 5027 participants

  setkey(df.f1.nhh, wave, cntcts)

  # count the number of participants with the same contacts in that wave
  df.f1.nhh <- df.f1.nhh[, list(nb.part = .N),
                         by = c('wave', 'cntcts')]
  # df.f1.nhh <- df.f1.nhh[, list(cntcts = sum(cntcts)),
  #                        by = c('wave', 'cntcts')]
  df.f1.nhh <- merge(df.f1.nhh, tmp, by = 'wave')
  # cum nb part if people reported more contacts then they are included in lower contacts groups
  df.f1.nhh[, cntcts := -cntcts]
  setkey(df.f1.nhh, wave, cntcts)
  df.f1.nhh[, cum.part := cumsum(nb.part), by = 'wave']
  df.f1.nhh[, cntcts := -cntcts]
  setkey(df.f1.nhh, wave, cntcts)



  df.f1.nhh[, prob := cum.part/t.part]
  unique(df.f1.nhh$prob)

  f1.nhh <- tlb.nhh[rp.nb == 1]
  setkey(f1.nhh, wave, cntcts)
  f1.nhh[, cum.cntcts := cumsum(cntcts), by = 'wave']

  df.f1.nhh <- merge(df.f1.nhh, f1.nhh, by = c('wave', 'cntcts'), all.y = T)
  df1 <- df.f1.nhh[wave == 1, list(cum.cntcts, prob)]
  # setnames(df1, c('prob'), 'ref.prob')
  df.f1.nhh <- df.f1.nhh[, list(wave,prob,cum.cntcts)]
  tmp <- as.data.table(expand.grid(wave = 2:33, cum.cntcts = unique(df.f1.nhh$cum.cntcts)))
  df1 <- as.data.table(merge(df1, tmp, by = 'cum.cntcts', all.y = T))
  df1[, type := 'wave 1']
  df.f1.nhh[, type := 'current wave']
  df.f1.nhh <- rbind(df.f1.nhh, df1)
  # df.f1.nhh <- merge(df.f1.nhh, df1, by = c('cum.cntcts'), all = T)
  # df.f1.nhh <- as.data.table(reshape2::melt(df.f1.nhh[, list(cum.cntcts,wave,cum.part, prob, ref.prob)],
  #                                            id = c('cum.cntcts', 'wave', 'cum.part')))
  df.f1.nhh$wave <- as.integer(df.f1.nhh$wave)
  df.f1.nhh$wave <- factor(df.f1.nhh$wave, levels = unique(sort(df.f1.nhh$wave)))
  setkey(df.f1.nhh, wave)
  df.f1.nhh[, wave.pt := paste0('Wave ', wave)]

  ggplot(df.f1.nhh, aes(x = cum.cntcts)) +
    geom_line(aes(x = cum.cntcts, y = log(prob), col = type)) +
    facet_wrap(.~factor(wave.pt, levels = unique(df.f1.nhh$wave.pt)), scales = 'free', ncol = 6) +
    labs(x = 'Cum contacts', y = 'log of the prob that participants reporting more contacts') +
    theme(legend.position = "right",
          panel.grid.minor = element_blank(),
          panel.grid.major = element_line(size = 0.2),
          panel.border = element_rect(fill = NA, size = 0.3),
          axis.line = element_line(size = 0.2),
          axis.ticks = element_line(size = 0.2),
          # panel.grid.major = element_blank(),
          # panel.border = element_rect(fill = NA, size = 0.5),
          # axis.line = element_line(size = 0.3),
          # axis.ticks = element_line(size = 0.3),
          panel.background = element_blank(),
          strip.background = element_blank(),
          legend.title = element_blank(),
          axis.text = element_text(size = 5, family = 'sans'),
          legend.text = element_text(size = 5, family = 'sans'),
          strip.text = element_text(size = 7, family = 'sans'),
          axis.title = element_text(size = 7, family = 'sans'))

  ggsave('sim_fig2.png', w = 12, h = 8)
}

# merge the group contacts and reclean the participants ----
tlb.nhh <- change_time(tlb.nhh)
dt.grp <- change_time(dt.grp.all)

# df.f1.nhh <- copy(tlb.nhh)
# tmp <- df.f1.nhh[, list(t.part = .N),
#                  by = 'round']
# sum(tmp$t.part)
# # 15945 cntcts
# # 5260 participants
#
# setkey(df.f1.nhh, round, cntcts)
df <- merge(tlb.nhh, dt.grp, by = c('wave', 'id', 'round'), all = T)

# check if this participant first attend... agin
df[, rp.nb := seq_len(length(round)), by = 'id']
df[rp.nb != 1]
df <- df[rp.nb == 1]

unique(df$age_group)
unique(df$sex)

df$cntcts <- ifelse(is.na(df$cntcts), df$grp.cntcts,
                           ifelse(is.na(df$grp.cntcts), df$cntcts,
                                  df$cntcts + df$grp.cntcts))

df <- df[, list(id,round,cntcts,wave,age_group,sex)]
#
# calculate the probability that a participants has n such contacts ----
# so that over n this sums to 1
# change the wave to round
# count the number of participants with the same contacts in that round
df.f1.nhh <- df[, list(nb.part = .N),
                       by = c('round', 'cntcts')]
tmp <- df[, list(t.part = .N),
                 by = 'round']
df.f1.nhh <- merge(df.f1.nhh, tmp, by = 'round')
df.f1.nhh[, prob := nb.part/t.part]

df.f1.nhh[, sum(prob, na.rm = T), by = 'round']

setkey(df.f1.nhh, round, cntcts)
# get the reference prob (round 1)
df1 <- df.f1.nhh[round == 1, list(cntcts, prob)]
# setnames(df1, c('prob'), 'ref.prob')
df.f1.nhh <- df.f1.nhh[, list(round,cntcts,prob)]
tmp <- as.data.table(expand.grid(round = 2:5, cntcts = unique(df.f1.nhh$cntcts)))
df1 <- as.data.table(merge(df1, tmp, by = 'cntcts', all.y = T))
df1[, type := 'baseline']
df.f1.nhh[, type := 'current waves']
df.f1.nhh <- rbind(df.f1.nhh, df1)
# df.f1.nhh <- merge(df.f1.nhh, df1, by = c('cum.cntcts'), all = T)
# df.f1.nhh <- as.data.table(reshape2::melt(df.f1.nhh[, list(cum.cntcts,round,cum.part, prob, ref.prob)],
#                                            id = c('cum.cntcts', 'round', 'cum.part')))
df.f1.nhh$round <- as.integer(df.f1.nhh$round)
df.f1.nhh$round <- factor(df.f1.nhh$round, levels = unique(sort(df.f1.nhh$round)))
setkey(df.f1.nhh, round)
df.f1.nhh <- round_descp(df.f1.nhh)

tmp <- df.f1.nhh[!is.na(log(prob ))]
tmp <- tmp[cntcts > 0]

fitted_models <-  tmp %>% group_by(round) %>%
  do(model = lm(log(prob) ~ log(cntcts), data = .))

fitted_models$model

txt <- data.table()
for (i in 1:5)
{
  tmp <- as.data.table(t(fitted_models$model[[i]]$coefficients))
  tmp[, round := i]

  txt  <- rbind(txt, tmp)

}
txt <- round_descp(txt)
txt$`(Intercept)` <- round(txt$`(Intercept)`, 2)
txt$`log(cntcts)` <- round(txt$`log(cntcts)`, 2)

txt$round.pt <- gsub('survey wave ', '', txt$round.pt)
set(txt, NULL, 'round', NULL)
txt

ggplot(df.f1.nhh) +
  # geom_smooth(method = 'lm',aes(x = (cntcts), y = (prob), col = type),
  #             fill = 'grey90', size = .3) +
  geom_point(aes(x = (cntcts), y = (prob), col = type), size = .8) +
  facet_wrap(factor(round.pt, levels = unique(df.f1.nhh$round.pt))~.) +
  labs(x = 'log of contacts', y = 'log of the prob that participants reporting contacts') +
  theme(legend.position = "right",
        panel.grid.minor = element_blank(),
        panel.grid.major = element_line(linewidth = 0.2),
        panel.border = element_rect(fill = NA, linewidth = 0.3),
        axis.line = element_line(linewidth = 0.2),
        axis.ticks = element_line(linewidth = 0.2),
        panel.background = element_blank(),
        strip.background = element_blank(),
        legend.title = element_blank()
        # axis.text = element_text(size = 5, family = 'sans'),
        # legend.text = element_text(size = 5, family = 'sans'),
        # strip.text = element_text(size = 7, family = 'sans'),
        # axis.title = element_text(size = 7, family = 'sans')
        )

ggsave('log-log_cntct-prob_round.png', w = 8, h = 6)


# repeat stratified by men / women in each facet  ----
# load the participant information to get the gender, age informati
df
# dpart <- change_time(dpart)

# df.f1.nhh <- tlb.nhh[rp.nb == 1]
# df <- as.data.table(merge(df.f1.nhh,
#                           unique(dpart[, list(id, round, part.age, part.sex)]),
#                           by = c('id', 'round'), all.x = T))
df.f1.nhh <- df[sex %in% c('Male', 'Female')]
setnames(df.f1.nhh, 'sex', 'part.sex')
unique(df.f1.nhh$part.sex)

tmp <- df.f1.nhh[, list(t.part = .N),
                 by = c('round', 'part.sex')]
sum(tmp$t.part)
# 15945 cntcts
# 7819 participants

setkey(df.f1.nhh, round, cntcts)

# count the number of participants with the same contacts in that round
df.f1.nhh <- df.f1.nhh[, list(nb.part = .N),
                       by = c('round', 'cntcts', 'part.sex')]
df.f1.nhh <- merge(df.f1.nhh, tmp, by = c('round', 'part.sex'))
df.f1.nhh[, prob := nb.part/t.part]

setkey(df.f1.nhh, round, cntcts, part.sex)
# get the reference prob (round 1)
df1 <- df.f1.nhh[round == 1, list(cntcts, prob, part.sex)]
# setnames(df1, c('prob'), 'ref.prob')
df.f1.nhh <- df.f1.nhh[, list(round,cntcts,prob, part.sex)]
tmp <- as.data.table(expand.grid(round = 2:5,
                                 cntcts = unique(df.f1.nhh$cntcts),
                                 part.sex = unique(df.f1.nhh$part.sex)))
df1 <- as.data.table(merge(df1, tmp, by = c('cntcts', 'part.sex'), all.y = T))
df1[, type := 'baseline']
df.f1.nhh[, type := 'current waves']
df.f1.nhh <- rbind(df.f1.nhh, df1)
# df.f1.nhh <- merge(df.f1.nhh, df1, by = c('cum.cntcts'), all = T)
# df.f1.nhh <- as.data.table(reshape2::melt(df.f1.nhh[, list(cum.cntcts,round,cum.part, prob, ref.prob)],
#                                            id = c('cum.cntcts', 'round', 'cum.part')))
df.f1.nhh$round <- as.integer(df.f1.nhh$round)
df.f1.nhh$round <- factor(df.f1.nhh$round, levels = unique(sort(df.f1.nhh$round)))
setkey(df.f1.nhh, round)
# df.f1.nhh[, round.pt := paste0('Round ', round)]
df.f1.nhh <- round_descp(df.f1.nhh)

# lm model
tmp <- df.f1.nhh[part.sex == 'Female']

tmp <- tmp[!is.na(log(prob ))]
tmp <- tmp[cntcts > 0]
fitted_models <-  tmp %>% group_by(round) %>%
  do(model = lm(log(prob) ~ log(cntcts), data = .))
txt <- data.table()
for(i in 1:5)
{
  tmp <- as.data.table(t(fitted_models$model[[i]]$coefficients))
  tmp[, round := i]

  txt  <- rbind(txt, tmp)

}
txt[, part.sex := 'Female']
txt.f <- copy(txt)

#
tmp <- df.f1.nhh[part.sex == 'Male']
tmp <- tmp[!is.na(log(prob ))]
tmp <- tmp[cntcts > 0]
fitted_models <-  tmp %>% group_by(round) %>%
  do(model = lm(log(prob) ~ log(cntcts), data = .))
txt <- data.table()
for(i in 1:5)
{
  tmp <- as.data.table(t(fitted_models$model[[i]]$coefficients))
  tmp[, round := i]

  txt  <- rbind(txt, tmp)

}
txt[, part.sex := 'Male']

txt <- rbind(txt.f, txt)
txt <- round_descp(txt)
txt$`(Intercept)` <- round(txt$`(Intercept)`, 2)
txt$`log(cntcts)` <- round(txt$`log(cntcts)`, 2)
txt$round.pt <- gsub('survey wave ', '', txt$round.pt)
set(txt, NULL, 'round', NULL)
txt

ggplot(df.f1.nhh, aes(x = cntcts)) +
  # geom_line(aes(x = log(cntcts), y = log(prob), col = part.sex, linetype = type)) +
  geom_smooth(data = df.f1.nhh[grepl('current', type)], method = 'lm',aes(x = log(cntcts), y = log(prob), col = part.sex, linetype = type), size = .3, fill = 'grey90' ) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = part.sex, shape = type), size = 1) +

  facet_wrap(factor(round.pt, levels = unique(df.f1.nhh$round.pt))~.) +
  labs(x = 'log of contacts', y = 'log of the prob that participants reporting contacts') +
  theme(legend.position = "right",
        panel.grid.minor = element_blank(),
        panel.grid.major = element_line(size = 0.2),
        panel.border = element_rect(fill = NA, size = 0.3),
        axis.line = element_line(size = 0.2),
        axis.ticks = element_line(size = 0.2),
        # panel.grid.major = element_blank(),
        # panel.border = element_rect(fill = NA, size = 0.5),
        # axis.line = element_line(size = 0.3),
        # axis.ticks = element_line(size = 0.3),
        panel.background = element_blank(),
        strip.background = element_blank(),
        legend.title = element_blank()
        # axis.text = element_text(size = 5, family = 'sans'),
        # legend.text = element_text(size = 5, family = 'sans'),
        # strip.text = element_text(size = 7, family = 'sans'),
        # axis.title = element_text(size = 7, family = 'sans')
        )

ggsave('log-log_cntct-prob_sex_round.png', w = 8, h = 6)

# repeat stratified by age in each facet  ----
# 18-24, 24-34, 35-44, 45-54, 55-64, 65+
# dpart <- as.data.table(readRDS(file = file.path(args$prj.dir, 'data', 'COVIMOD', 'part.rds')))
# dpart <- dpart[part.sex %in% c('Female', 'Male') & (!is.na(part.age))]
# setnames(dpart, 'pt.id', 'id')
# dpart <- change_time(dpart)
#  TODO: tbc if we will include missing sex, age information
df

dt.grp <- as.data.table(merge(dpart[, list(id,wave,part.sex,part.age)], df, by = c('id', 'wave'), all.y = T))
dt.grp$age_group <- ifelse(dt.grp$part.age %in% 18:24, '18-24', dt.grp$age_group)
dt.grp$age_group <- ifelse(dt.grp$age_group %in% c('65-69', '70-74',
                                                   '75-79', '80-84',
                                                   '85+'), '65+', dt.grp$age_group)
unique(dt.grp$age_group)

df.f1.nhh <- dt.grp[age_group %in% c('18-24', '25-34', '35-44', '45-54', '55-64', '65+')]
df.f1.nhh$age.group <- factor(df.f1.nhh$age_group, levels = c('18-24', '25-34', '35-44', '45-54', '55-64', '65+'))
if (0)
{
df <- as.data.table(merge(df.f1.nhh,
                          unique(dpart[, list(id, round, part.age, part.sex)]),
                          by = c('id', 'round'), all.x = T))
df.f1.nhh <- df[!is.na(part.sex)]
unique(df.f1.nhh$part.age)
df.f1.nhh$age.group <- ifelse(df.f1.nhh$part.age %in% 18:24, '18-24',
                              ifelse(df.f1.nhh$part.age %in% 25:34, '25-34',
                                     ifelse(df.f1.nhh$part.age %in% 35:44, '35-44',
                                            ifelse(df.f1.nhh$part.age %in% 45:54, '45-54',
                                                   ifelse(df.f1.nhh$part.age %in% 55:64, '55-64',
                                                          ifelse(df.f1.nhh$part.age >= 65, '65+', 'others'))))))

df.f1.nhh <- df.f1.nhh[age.group != 'others']
}
tmp <- df.f1.nhh[, list(t.part = .N),
                 by = c('round', 'age.group')]
sum(tmp$t.part)
# 5027 participants
# 6502 with group contacts

setkey(df.f1.nhh, round, cntcts)

# count the number of participants with the same contacts in that round
df.f1.nhh <- df.f1.nhh[, list(nb.part = .N),
                       by = c('round', 'cntcts', 'age.group')]
df.f1.nhh <- merge(df.f1.nhh, tmp, by = c('round', 'age.group'))
df.f1.nhh[, prob := nb.part/t.part]

setkey(df.f1.nhh, round, cntcts, age.group)
# get the reference prob (round 1)
df1 <- df.f1.nhh[round == 1, list(cntcts, prob, age.group)]
# setnames(df1, c('prob'), 'ref.prob')
df.f1.nhh <- df.f1.nhh[, list(round,cntcts,prob, age.group)]

# lm
# lm model
txt <- data.table()
for (age in unique(df.f1.nhh$age.group))
{
  tp <- df.f1.nhh[age.group == age]
  tp <- tp[!is.na(log(prob ))]
  tp <- tp[cntcts > 0]
  fitted_models <-  tp %>% group_by(round) %>%
    do(model = lm(log(prob) ~ log(cntcts), data = .))
  j <- 0
  for (i in unique(tp$round))
  {
    j <- j + 1
    tmp <- as.data.table(t(fitted_models$model[[j]]$coefficients))
    tmp[, round := i]
    tmp[, age.group := age]

    txt  <- rbind(txt, tmp)

  }

}
txt <- round_descp(txt)
txt$`(Intercept)` <- round(txt$`(Intercept)`, 2)
txt$`log(cntcts)` <- round(txt$`log(cntcts)`, 2)
txt$round.pt <- gsub('survey wave ', '', txt$round.pt)
set(txt, NULL, 'round', NULL)
txt

tmp <- as.data.table(expand.grid(round = 2:5,
                                 cntcts = unique(df.f1.nhh$cntcts),
                                 age.group = unique(df.f1.nhh$age.group)))
df1 <- as.data.table(merge(df1, tmp, by = c('cntcts', 'age.group'), all.y = T))
df1[, type := 'baseline']
df.f1.nhh[, type := 'current waves']
df.f1.nhh <- rbind(df.f1.nhh, df1)
# df.f1.nhh <- merge(df.f1.nhh, df1, by = c('cum.cntcts'), all = T)
# df.f1.nhh <- as.data.table(reshape2::melt(df.f1.nhh[, list(cum.cntcts,round,cum.part, prob, ref.prob)],
#                                            id = c('cum.cntcts', 'round', 'cum.part')))
df.f1.nhh$round <- as.integer(df.f1.nhh$round)
df.f1.nhh$round <- factor(df.f1.nhh$round, levels = unique(sort(df.f1.nhh$round)))
setkey(df.f1.nhh, round)
df.f1.nhh <- round_descp(df.f1.nhh)
# df.f1.nhh[, round.pt := paste0('Round ', round)]
ggplot(df.f1.nhh[age.group %in% unique(df.f1.nhh$age.group)[1:3]], aes(x = cntcts)) +
  # geom_smooth(method = 'lm',aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type) ) +
  geom_smooth(data = df.f1.nhh[grepl('current', type) & age.group %in% unique(df.f1.nhh$age.group)[1:3]], method = 'lm', se = FALSE, aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type), fill = 'grey90', size = .3 ) +

  # geom_line(data = df.f1.nhh[grepl('current', type)& age.group %in% unique(df.f1.nhh$age.group)[1:3]], aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type), size = .3) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = age.group, shape = type), size = 1) +

  facet_wrap(.~factor(round.pt, levels = unique(df.f1.nhh$round.pt))
            ) +
  labs(x = 'log of contacts', y = 'log of the prob that participants reporting contacts') +
  theme(legend.position = "right",
        panel.grid.minor = element_blank(),
        panel.grid.major = element_line(size = 0.2),
        panel.border = element_rect(fill = NA, size = 0.3),
        axis.line = element_line(size = 0.2),
        axis.ticks = element_line(size = 0.2),
        # panel.grid.major = element_blank(),
        # panel.border = element_rect(fill = NA, size = 0.5),
        # axis.line = element_line(size = 0.3),
        # axis.ticks = element_line(size = 0.3),
        panel.background = element_blank(),
        strip.background = element_blank(),
        legend.title = element_blank()
        # axis.text = element_text(size = 5, family = 'sans'),
        # legend.text = element_text(size = 5, family = 'sans'),
        # strip.text = element_text(size = 7, family = 'sans'),
        # axis.title = element_text(size = 7, family = 'sans')
        )

ggsave('log-log_cntct-prob_age1_round.png', w = 8, h = 6)

#
ggplot(df.f1.nhh[age.group %in% unique(df.f1.nhh$age.group)[4:6]], aes(x = cntcts)) +
  geom_smooth(data = df.f1.nhh[grepl('current', type) & age.group %in% unique(df.f1.nhh$age.group)[4:6]], method = 'lm',se = FALSE, aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type), fill = 'grey90', size = .3 ) +
  # geom_line(data = df.f1.nhh[grepl('current', type)& age.group %in% unique(df.f1.nhh$age.group)[4:6]], aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type), size = .3) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = age.group, shape = type), size = 1) +

  facet_wrap(.~factor(round.pt, levels = unique(df.f1.nhh$round.pt))
  ) +
  labs(x = 'log of contacts', y = 'log of the prob that participants reporting contacts') +
  theme(legend.position = "right",
        panel.grid.minor = element_blank(),
        panel.grid.major = element_line(size = 0.2),
        panel.border = element_rect(fill = NA, size = 0.3),
        axis.line = element_line(size = 0.2),
        axis.ticks = element_line(size = 0.2),
        # panel.grid.major = element_blank(),
        # panel.border = element_rect(fill = NA, size = 0.5),
        # axis.line = element_line(size = 0.3),
        # axis.ticks = element_line(size = 0.3),
        panel.background = element_blank(),
        strip.background = element_blank(),
        legend.title = element_blank()
        # axis.text = element_text(size = 5, family = 'sans'),
        # legend.text = element_text(size = 5, family = 'sans'),
        # strip.text = element_text(size = 7, family = 'sans'),
        # axis.title = element_text(size = 7, family = 'sans')
  )

ggsave('log-log_cntct-prob_age2_round.png', w = 8, h = 6)


ggplot(df.f1.nhh[age.group %in% unique(df.f1.nhh$age.group)], aes(x = cntcts)) +
  geom_smooth(data = df.f1.nhh[grepl('current', type) & age.group %in% unique(df.f1.nhh$age.group)], method = 'lm',se = FALSE, aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type), fill = 'grey90', size = .3 ) +
  # geom_line(data = df.f1.nhh[grepl('current', type)& age.group %in% unique(df.f1.nhh$age.group)[4:6]], aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type), size = .3) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = age.group, shape = type), size = 1) +

  facet_wrap(.~factor(round.pt, levels = unique(df.f1.nhh$round.pt))
  ) +
  labs(x = 'log of contacts', y = 'log of the prob that participants reporting contacts') +
  theme(legend.position = "right",
        panel.grid.minor = element_blank(),
        panel.grid.major = element_line(size = 0.2),
        panel.border = element_rect(fill = NA, size = 0.3),
        axis.line = element_line(size = 0.2),
        axis.ticks = element_line(size = 0.2),
        # panel.grid.major = element_blank(),
        # panel.border = element_rect(fill = NA, size = 0.5),
        # axis.line = element_line(size = 0.3),
        # axis.ticks = element_line(size = 0.3),
        panel.background = element_blank(),
        strip.background = element_blank(),
        legend.title = element_blank()
        # axis.text = element_text(size = 5, family = 'sans'),
        # legend.text = element_text(size = 5, family = 'sans'),
        # strip.text = element_text(size = 7, family = 'sans'),
        # axis.title = element_text(size = 7, family = 'sans')
  )

ggsave('log-log_cntct-prob_age-all_round.png', w = 12, h = 8)
