# Terraform-Building the BloSS@M Project

## If/When you want to change the dashboard (e.g. blossom-dashboard or blossom-dashboard-GreatCorp) at the moment there are **2(TWO)** places where you will need to make the changes:

1. The Makefile located at `iac/Makefile`

```makefile
DASHBOARD_DIR:= ../../blossom-dashboard
### ~/github/blossom-dashboard
### Particular ORG-Member Dashboard, preferably forked form blossom-dashboard [This one is NIST]
# DASHBOARD_DIR:=../../blossom-dashboard-nist
```

Note!: Make sure that the relative(recommended) or absolute-path(discouraged) properly points to the dashboard location `relative to /iac directory`

2. Currently, the line 14 of the `iac/web-content.tf` terraform file contains reference to the dashboard build target directory. Make sure that it correctly points to `/../../blossom-dashboard/dist` if you are building the default dashboard

```t
  # TODO: !!! Change this line to point to the correct RELATIVE PATH !!!
  webcontent_builddir = "${path.module}/../../blossom-dashboard/dist"
```

or to your specific fork implementation (if that's what you intended to do)

```t
  # TODO: !!! Change this line to point to the correct RELATIVE PATH !!!
  webcontent_builddir = "${path.module}/../../blossom-dashboard-GreatCorp/dist"
```