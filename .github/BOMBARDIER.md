# Bombardier with proxy
Adopted from [github.com/mariotrucco/bombardier/tree/78-add-proxy-support](https://github.com/mariotrucco/bombardier/tree/78-add-proxy-support)

## Installation

1. Download and install Golang [go.dev/dl/#stable](https://go.dev/dl/#stable)
2. Run in bash/PowerShell:
```shell script
mkdir bombardier_tmp
cd bombardier_tmp
go mod init bombardier_tmp
go mod edit -replace github.com/codesenberg/bombardier=github.com/PXEiYyMH8F/bombardier@78-add-proxy-support
go get github.com/codesenberg/bombardier
cd ..
rm -r bombardier_tmp
```
3. The executable file location is `$GOPATH/bin/bombardier` (Linux) or  `%GOPATH%\bin\bombardier.exe` (Windows)
