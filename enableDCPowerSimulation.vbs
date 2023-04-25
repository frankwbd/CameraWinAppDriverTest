
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
'  set up for testing
'

'  enable the simulated battery
SimulatedBatterySystemSystemAction.EnableSimulatedBattery()

'  disable real batteries
SimulatedBatterySystemSystemAction.DisableRealBatteries()

'  set to DC power status
SimulatedBatterySystemSystemAction.SetSimulatedBatteryToDC()

'  set to 50% charge level
SimulatedBatterySystemSystemAction.SetSimulatedBatteryChargePercentage(50)

'
' It might be necessary to wait for second order effects of changing to DC propagate
' through the system before continuing the test, otherwise the effects can interfere
' with test operation.
'     Example: Switching to DC while in CS will cause the system to briefly exit
'     CS, thus interfering with automation that immediately tries to enter CS after
'     changing to DC.
' This is not done inside the SimulatedBatterySystem interface because the test
' might want to monitor and/or verify the second order effects (policy changing,
' display changing brightness, etc.) instead of getting them out of the way before
' continuing.
'
WScript.Sleep 1000
