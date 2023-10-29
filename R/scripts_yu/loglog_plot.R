# covimod data preprocessing script
# analyse the number of contacts that first showing up participants
# Preamble ----
# the covimod preprocess wave 33 dataset script

# Load the required packages----
require(data.table)
require(ggplot2)
library(tidyverse)

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
# dt.hh <- as.data.table(hh_data)
dt.nhh <- as.data.table(non_hh_data)
dt.part <- as.data.table(part_data)


# process non-household
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

# stratified by wave
# similar to FIG2 refered to SCHNEEBERGER_2004
tlb.nhh <- dt.nhh[!(is.na(cont.age) | is.na(cont.sex)),
                  list(cntcts = .N),
                  by = c('wave', 'new_id')]
setnames(tlb.nhh, 'new_id', 'id')
setkey(tlb.nhh, id, wave)
tlb.nhh[, rp.nb := seq_len(length(cntcts)), by = 'id']
# tlb.nhh is the individual level dataset

# Similar to Fig2 ----
# we are interested in participants who are in the survey at the first time
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


# calculate the probability that a participants has n such contacts ----
# so that over n this sums to 1

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
df.f1.nhh <- merge(df.f1.nhh, tmp, by = 'wave')
df.f1.nhh[, prob := nb.part/t.part]

setkey(df.f1.nhh, wave, cntcts)
# get the reference prob (wave 1)
df1 <- df.f1.nhh[wave == 1, list(cntcts, prob)]
# setnames(df1, c('prob'), 'ref.prob')
df.f1.nhh <- df.f1.nhh[, list(wave,cntcts,prob)]
tmp <- as.data.table(expand.grid(wave = 2:33, cntcts = unique(df.f1.nhh$cntcts)))
df1 <- as.data.table(merge(df1, tmp, by = 'cntcts', all.y = T))
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
ggplot(df.f1.nhh, aes(x = cntcts)) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = type)) +
  facet_wrap(.~factor(wave.pt, levels = unique(df.f1.nhh$wave.pt)), scales = 'free', ncol = 6) +
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
        legend.title = element_blank(),
        axis.text = element_text(size = 5, family = 'sans'),
        legend.text = element_text(size = 5, family = 'sans'),
        strip.text = element_text(size = 7, family = 'sans'),
        axis.title = element_text(size = 7, family = 'sans'))

ggsave('log-log_cntct-prob.png', w = 12, h = 8)


# repeat stratified by men / women in each facet  ----
# load the participant information to get the gender, age information
dpart <- as.data.table(readRDS(file = file.path(args$prj.dir, 'data', 'COVIMOD', 'part.rds')))
dpart <- dpart[part.sex %in% c('Female', 'Male') & (!is.na(part.age))]
setnames(dpart, 'pt.id', 'id')

df.f1.nhh <- tlb.nhh[rp.nb == 1]
df <- as.data.table(merge(df.f1.nhh,
                          unique(dpart[, list(id, wave, part.age, part.sex)]),
                          by = c('id', 'wave'), all.x = T))
df.f1.nhh <- df[!is.na(part.sex)]
unique(df.f1.nhh$part.sex)

tmp <- df.f1.nhh[, list(t.part = .N),
                 by = c('wave', 'part.sex')]
sum(tmp$t.part)
# 15945 cntcts
# 5027 participants

setkey(df.f1.nhh, wave, cntcts)

# count the number of participants with the same contacts in that wave
df.f1.nhh <- df.f1.nhh[, list(nb.part = .N),
                       by = c('wave', 'cntcts', 'part.sex')]
df.f1.nhh <- merge(df.f1.nhh, tmp, by = c('wave', 'part.sex'))
df.f1.nhh[, prob := nb.part/t.part]

setkey(df.f1.nhh, wave, cntcts, part.sex)
# get the reference prob (wave 1)
df1 <- df.f1.nhh[wave == 1, list(cntcts, prob, part.sex)]
# setnames(df1, c('prob'), 'ref.prob')
df.f1.nhh <- df.f1.nhh[, list(wave,cntcts,prob, part.sex)]
tmp <- as.data.table(expand.grid(wave = 2:33,
                                 cntcts = unique(df.f1.nhh$cntcts),
                                 part.sex = unique(df.f1.nhh$part.sex)))
df1 <- as.data.table(merge(df1, tmp, by = c('cntcts', 'part.sex'), all.y = T))
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
ggplot(df.f1.nhh, aes(x = cntcts)) +
  geom_line(aes(x = log(cntcts), y = log(prob), col = part.sex, linetype = type)) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = part.sex, shape = type), size = .8) +

  facet_wrap(.~factor(wave.pt, levels = unique(df.f1.nhh$wave.pt)),
             scales = 'free', ncol = 6) +
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
        legend.title = element_blank(),
        axis.text = element_text(size = 5, family = 'sans'),
        legend.text = element_text(size = 5, family = 'sans'),
        strip.text = element_text(size = 7, family = 'sans'),
        axis.title = element_text(size = 7, family = 'sans'))

ggsave('log-log_cntct-prob_sex.png', w = 12, h = 8)




# repeat stratified by age in each facet  ----
# 18-24, 24-34, 35-44, 45-54, 55-64, 65+
dpart <- as.data.table(readRDS(file = file.path(args$prj.dir, 'data', 'COVIMOD', 'part.rds')))
dpart <- dpart[part.sex %in% c('Female', 'Male') & (!is.na(part.age))]
setnames(dpart, 'pt.id', 'id')

df.f1.nhh <- tlb.nhh[rp.nb == 1]
df <- as.data.table(merge(df.f1.nhh,
                          unique(dpart[, list(id, wave, part.age, part.sex)]),
                          by = c('id', 'wave'), all.x = T))
df.f1.nhh <- df[!is.na(part.sex)]
unique(df.f1.nhh$part.age)
df.f1.nhh$age.group <- ifelse(df.f1.nhh$part.age %in% 18:24, '18-24',
                              ifelse(df.f1.nhh$part.age %in% 25:34, '25-34',
                                     ifelse(df.f1.nhh$part.age %in% 35:44, '35-44',
                                            ifelse(df.f1.nhh$part.age %in% 45:54, '45-54',
                                                   ifelse(df.f1.nhh$part.age %in% 55:64, '55-64',
                                                          ifelse(df.f1.nhh$part.age >= 65, '65+', 'others'))))))

df.f1.nhh <- df.f1.nhh[age.group != 'others']

tmp <- df.f1.nhh[, list(t.part = .N),
                 by = c('wave', 'age.group')]
sum(tmp$t.part)
# 15945 cntcts
# 5027 participants

setkey(df.f1.nhh, wave, cntcts)

# count the number of participants with the same contacts in that wave
df.f1.nhh <- df.f1.nhh[, list(nb.part = .N),
                       by = c('wave', 'cntcts', 'age.group')]
df.f1.nhh <- merge(df.f1.nhh, tmp, by = c('wave', 'age.group'))
df.f1.nhh[, prob := nb.part/t.part]

setkey(df.f1.nhh, wave, cntcts, age.group)
# get the reference prob (wave 1)
df1 <- df.f1.nhh[wave == 1, list(cntcts, prob, age.group)]
# setnames(df1, c('prob'), 'ref.prob')
df.f1.nhh <- df.f1.nhh[, list(wave,cntcts,prob, age.group)]
tmp <- as.data.table(expand.grid(wave = 2:33,
                                 cntcts = unique(df.f1.nhh$cntcts),
                                 age.group = unique(df.f1.nhh$age.group)))
df1 <- as.data.table(merge(df1, tmp, by = c('cntcts', 'age.group'), all.y = T))
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
ggplot(df.f1.nhh[age.group %in% unique(df.f1.nhh$age.group)[1:3]], aes(x = cntcts)) +
  geom_line(aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type)) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = age.group, shape = type), size = .8) +

  facet_wrap(.~factor(wave.pt, levels = unique(df.f1.nhh$wave.pt)),
             scales = 'free', ncol = 6) +
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
        legend.title = element_blank(),
        axis.text = element_text(size = 5, family = 'sans'),
        legend.text = element_text(size = 5, family = 'sans'),
        strip.text = element_text(size = 7, family = 'sans'),
        axis.title = element_text(size = 7, family = 'sans'))

ggsave('log-log_cntct-prob_age1.png', w = 12, h = 8)


ggplot(df.f1.nhh[age.group %in% unique(df.f1.nhh$age.group)[4:6]], aes(x = cntcts)) +
  geom_line(aes(x = log(cntcts), y = log(prob), col = age.group, linetype = type)) +
  geom_point(aes(x = log(cntcts), y = log(prob), col = age.group, shape = type), size = .8) +

  facet_wrap(.~factor(wave.pt, levels = unique(df.f1.nhh$wave.pt)),
             scales = 'free', ncol = 6) +
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
        legend.title = element_blank(),
        axis.text = element_text(size = 5, family = 'sans'),
        legend.text = element_text(size = 5, family = 'sans'),
        strip.text = element_text(size = 7, family = 'sans'),
        axis.title = element_text(size = 7, family = 'sans'))

ggsave('log-log_cntct-prob_age2.png',w = 12, h = 8)
