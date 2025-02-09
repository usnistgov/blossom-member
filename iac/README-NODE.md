### Maintaining the Node and NPM 

#### 1. To assure necessary patching follow the node package update and upgrades suggested by @dependabot
#### 2. To be proactive in assuring necessary patching use the node audit commands:
  - ##### To scan node packages for the known vulnerabilities run the following:
```
    npm audit
```
  - ##### To fix non-breaking node packages for the known vulnerabilities run the following:
```
    npm audit fix
```
#### 3. To force (**possibly breaking**) vulnerability fixes use the following:
  - ##### !!! Be very careful and test thoroughly after forcing fixes of (**possibly breaking**) packages  
```
    npm audit fix --force
```