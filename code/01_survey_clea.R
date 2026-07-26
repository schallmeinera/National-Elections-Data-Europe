# Survey CLEA post-2020 European coverage
load("D:/EU LFS/DATA/03_Elections/CLEA_GRED/clea_lc_20251015.RData")
d <- clea_lc_20251015
eur <- c("Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic",
         "Czechia","Denmark","Estonia","Finland","France","Germany","Greece",
         "Hungary","Iceland","Ireland","Italy","Latvia","Lithuania","Luxembourg",
         "Malta","Netherlands","Norway","Poland","Portugal","Romania","Slovakia",
         "Slovenia","Spain","Sweden","Switzerland","UK","United Kingdom")
e <- d[d$ctr_n %in% eur & d$yr >= 2021, ]
tab <- aggregate(cst ~ ctr_n + yr, e, function(x) length(unique(x)))
tab <- tab[order(tab$ctr_n, tab$yr), ]
write.csv(tab, "D:/EU LFS/eu-parliamentary-elections/output/_clea_post2020_survey.csv", row.names = FALSE)
print(tab, row.names = FALSE)

# sample constituency names for a few countries
for (cc in c("Spain", "Portugal", "Finland", "Denmark", "Norway", "Sweden", "Greece", "Italy", "Germany", "Netherlands", "Austria")) {
  s <- unique(e$cst_n[e$ctr_n == cc])
  cat("\n--", cc, "(", length(s), "):", paste(head(s, 12), collapse = " | "), "\n")
}
