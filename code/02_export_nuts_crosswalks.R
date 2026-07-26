# Export the JRC-based NUTS conversion matrices shipped with the `nuts` package
library(nuts)
res <- data(package = "nuts")
print(res$results[, c("Item", "Title")])

# load whatever crosswalk objects exist
items <- res$results[, "Item"]
for (it in items) {
  data(list = it, package = "nuts")
  obj <- get(it)
  cat("\n====", it, "====\n")
  cat("class:", class(obj), " dim:", paste(dim(obj), collapse = "x"), "\n")
  if (is.data.frame(obj)) {
    print(names(obj))
    print(head(obj, 3))
    out <- file.path("D:/EU LFS/eu-parliamentary-elections/crosswalks",
                     paste0("nutsRpkg_", it, ".csv"))
    write.csv(obj, out, row.names = FALSE)
    cat("written:", out, "\n")
  }
}
