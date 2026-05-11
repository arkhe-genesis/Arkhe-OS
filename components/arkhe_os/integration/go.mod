module arkhe_os/integration

go 1.24.3

replace arkhe_os/sensors => ../sensors

replace arkhe_os/photonic => ../photonic

require (
	arkhe_os/photonic v0.0.0-00010101000000-000000000000
	arkhe_os/sensors v0.0.0-00010101000000-000000000000
)
