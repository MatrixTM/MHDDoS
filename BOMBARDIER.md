# Bombardier with proxy
Adopted from github.com/mariotrucco/bombardier@78-add-proxy-support

## Installation
```shell script
mkdir bombardier_tmp
cd bombardier_tmp
go mod init bombardier_tmp
go mod edit -replace github.com/codesenberg/bombardier=github.com/mariotrucco/bombardier@78-add-proxy-support
go get github.com/codesenberg/bombardier
cd ..
rm -r bombardier_tmp
```
