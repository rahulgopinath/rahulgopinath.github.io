library(ggplot2)
library(magrittr)
library(dplyr)

toI<- function(x) as.numeric(x, origin = "1970-01-01")
toD <- function(x) as.Date(x, origin = "1970-01-01")
vswitch <- function(expr, ...) {
  lookup <- list(...)
  vec <- as.character(expr)
  vec[is.na(vec)] <- "NA"
  unname(do.call(c, lookup[vec]))
}


cve.x <- read.csv('linux-cve-lifetime.csv', header=F)
names(cve.x) <- c(
  'cve'
  ,'impact'
  ,'bugno'
  ,'v.introduced'
  ,'d.introduced'
  ,'v.found'
  ,'d.found')
cve.x$d.introduced <- toD(cve.x$d.introduced)
cve.x$d.found <- toD(cve.x$d.found)
cve.x$i.introduced <- toI(cve.x$d.introduced)
cve.x$i.found <- toI(cve.x$d.found)
cve.x$v.introduced <- as.character(cve.x$v.introduced)
cve.x$Impact <- vswitch(cve.x$impact,
                      "critical" = 4,
                      "high" = 3,
                      "medium" = 2,
                      "low" = 1,
                      "negligible" = 0)


c.loc <- read.csv('linux-c.csv', header=F)
names(c.loc) <- c('version', 'src', 'loc')
c.loc$version <- as.character(c.loc$version)

cve.x <- cve.x %>% filter(d.introduced != toD('2005-06-17'))
c.loc %<>% filter((version %in% cve.x$v.introduced))

cve <- left_join(cve.x, c.loc, by=c('v.introduced' = 'version'))

d = lm(i.introduced~i.found*loc, data=cve)
cve$predicted <- predict(d)


ggplot(cve) +
  geom_point(aes(x=d.found, y=d.introduced, size=Impact, alpha=0.4), 
              shape=1, alpha=0.7) +
  geom_smooth(aes(x=d.found, y=toD(predicted)), 
              method='lm', formula=y~x, color="darkblue", fill="blue") +
  geom_smooth(aes(x=d.found, y=d.introduced), method='lm', formula=y~x,
              color="darkred", fill="red") +
  geom_abline(slope=1, color='red', intercept=20) +
  ggtitle("Vulnerabilities in Linux kernel") +
  labs(x="Found",y="Introduced")

l.cve <- cve %>% group_by(v.introduced) %>% 
  summarize(nbugs = length(loc), loc=mean(loc), d.introduced = mean(d.introduced))

ggplot(l.cve, aes(x=d.introduced, y=loc, color=nbugs)) +
  geom_jitter(shape=1, alpha=0.7) + 
  geom_smooth(method='lm')

