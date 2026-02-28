# Operator Quickcheck v1

## 1) Verify structure (expected)
root: C:\Users\greas\Documents\layered_ventures
- root .git: False
- workspace\.git: True
- ops\.git: True
- projects\<id>\.git: True

## 2) Verify scheduled task
(Admin PowerShell)
schtasks /Query /TN lv_capsule_tick_all /V /FO LIST | Select-String "Task To Run|Run As User|Next Run Time|Last Run Time|Last Result"

Expected:
- Run As User: SYSTEM
- Last Result: 0
- Task To Run: ...\ops\tools\lv_capsule_tick_all.ps1

## 3) Verify snapshot output exists
Get-ChildItem C:\Users\greas\Documents\layered_ventures\ops\ops\logs\capsule_tick_all -Directory |
  Sort-Object Name -Descending | Select-Object -First 1
