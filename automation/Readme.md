# Account Management Workflow
### Workflow description of GitHub-S3 interactions used to automate account management tracking in SSP.

- The **requester** creates a new **GitHub issue** (**Account Request Form**) *to request* an account for the **Account Holder**.
- The **Blossom Management group** is automatically notified *to review* this request through GitHub.
- A **Blossom Management member** reviews the request and *adds a new label* to the issue: ACCOUNT_APPROVED or ACCOUNT_REJECTED
- If **ACCOUNT_APPROVED**, the **Blossom Sysdevs group** is automatically notified to implement the account.
- **Sys-Dev** creates account
- **Sys-Dev** submits a new issue (**Account Management - Authorization Form**) for the Account Holder.

- If **ACCOUNT_REJECTED**, the account request issue is automatically closed.



```mermaid
sequenceDiagram
    actor Rq as Requester
    actor Man as Manager
        
    box Form + Actions
        participant GH as GitHub
    end
    
    box  AWS-Infrastructure
        participant EC2 as EC2-VPC
        participant Cog as CognitoX
    end
    loop Approval Process
        loop Admin Request  
            Rq->>+GH: Creates Account Request
            GH--)+Man: Notifies of Request
            Man--)Man: Reviews Request
            Man->>-GH: Adds Label [ACCOUNT_APPROVED or ACCOUNT_REJECTED]
        end

        loop Implementation
            create actor Sys as Sys-Dev
            GH--)+Sys: On ACCOUNT_APPROVED: 'Creating Account Holder'
            Note left of Sys: Create Account    

            Sys->>Cog: Creates [Account Holder] Record and Attributes
            Sys->>EC2: Registers [Account Holder] With Blockchain
            Note right of Sys: Account Created 

            Sys->>GH: Account Created
        end
    end
    
    Sys->>-GH: Start Account Management - Authorization Form

    create actor AH as Account Holder
    GH--)AH: Maybe Welcome, Created User!

```



## The GitHub to S3 activity diagram

```mermaid

sequenceDiagram

    actor SO as System Owner
    actor AO as Authorizing Officer
    box Github & S3 Communication
        participant GH as GitHub
        participant S3 as AWS-S3
    end


    SO -->> GH: Begins Account Creation [GH:Action/Email]
    GH -->> AO: Notified [GH:Action/Email]
    AO -->> GH: Approves Account Creation [GH:Action]
    GH -->> GH: Creates Operation/Request Files in Repository [GH:Action]
    GH -->> S3: Transfers the Request File [GH:Action]
```


## AWS-GitHub Components Interaction Illustrated

```mermaid
sequenceDiagram

    box S3, AWS-λ, EC2 & GitHub Communication
        participant GH as GitHub
        participant AWS-λ as λ-Function
        participant S3 as AWS-S3
        participant EC2 as AWS-EC2
    end


  S3 -> AWS-λ: Event of New File(Request) in S3 [Results from GH:Action by User]
  AWS-λ -->> EC2: BEgins VM-side Code Execution for Account Creation [PY: Code on both ends]
  EC2 -->> EC2: Parse Configuration Files [EC2 PY-Code]
  EC2 -->> EC2: Delete Previous GitHub Repository [EC2 PY-Code]
  EC2 -->> GH: Send Request to Clone Repository [SSH Communication & EC2 PY-Code]
  GH -->> EC2: Clone Repository [SSH Communication & EC2 PY-Code]
  EC2 -->> EC2: Copy Operation File [EC2 PY-Code]
  EC2 -->> EC2: Parse & Validate Request/Operation Files [EC2 PY-Code]
  EC2 -->> EC2: Compose User XML-Fragment [EC2 PY-Code]
  EC2 -->> EC2: Update SSP FIle [EC2 PY-Code]
  EC2 -->> GH: Add, Commit & Push Changes [EC2 PY-Code]
  EC2 -->> EC2: Delete Local GitHub Repository [EC2 PY-Code]
```
