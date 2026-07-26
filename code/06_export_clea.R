# Export CLEA lower-chamber rows for Europe >= 2021 to CSV
load("D:/EU LFS/DATA/03_Elections/CLEA_GRED/clea_lc_20251015.RData")
d <- clea_lc_20251015
eur <- c("Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic",
         "Czechia","Denmark","Estonia","Finland","France","Germany","Greece",
         "Hungary","Iceland","Ireland","Italy","Latvia","Lithuania","Luxembourg",
         "Malta","Netherlands","Norway","Poland","Portugal","Romania","Slovakia",
         "Slovenia","Spain","Sweden","Switzerland","UK","United Kingdom")
e <- d[d$ctr_n %in% eur & d$yr >= 2021,
       c("ctr_n","ctr","yr","mn","cst_n","cst","pty_n","pty",
         "pev1","vot1","vv1","pv1","pvs1","cv1","seat")]
write.csv(e, "D:/EU LFS/eu-parliamentary-elections/raw/clea_europe_2021plus.csv",
          row.names = FALSE, fileEncoding = "UTF-8")
cat("rows:", nrow(e), "\n")
