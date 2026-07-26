d <- readRDS("D:/EU LFS/DATA/03_Elections/Municipal/germany/federal_cty_harm.rds")
cat("dim:", dim(d), "\n")
cat("names:", names(d), "\n")
cat("years:", sort(unique(d$election_year)), "\n")
print(head(as.data.frame(d), 3))
# write to csv for python
write.csv(d, "D:/EU LFS/eu-parliamentary-elections/raw/de_federal_cty_harm.csv",
          row.names = FALSE)
cat("written\n")
