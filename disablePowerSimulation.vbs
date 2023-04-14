
'
' Variable defenition 
'

Dim WDTF
Dim SimulatedBatterySystemSystemAction


'
' Create WDTF object
'

Set WDTF = CreateObject("WDTF2.WDTF")

'
'  Get your newly created SimulatedBatterySystem action interface
'

Set SimulatedBatterySystemSystemAction = WDTF.SystemDepot.ThisSystem.GetInterface("SimulatedBatterySystem")



'
'  clean up
'

'  set to AC power status
SimulatedBatterySystemSystemAction.SetSimulatedBatteryToAC()

'  enable real batteries
SimulatedBatterySystemSystemAction.EnableRealBatteries()

'  disable the simulated battery
SimulatedBatterySystemSystemAction.DisableSimulatedBattery()

