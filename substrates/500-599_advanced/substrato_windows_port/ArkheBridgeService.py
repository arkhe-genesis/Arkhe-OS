#!/usr/bin/env python3
"""
Arkhe Windows Bridge Service
Instalar: python ArkheBridgeService.py install
Iniciar:  python ArkheBridgeService.py start
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import subprocess

class ArkheBridgeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ArkheBridge"
    _svc_display_name_ = "ARKHE OS Constitutional Bridge"
    _svc_description_ = "Runtime ARKHE v∞.Ω.∇+++ nativo Windows"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        venv_python = r"C:\Arkhe\venv\Scripts\python.exe"
        while self.is_alive:
            try:
                r = subprocess.run(
                    [venv_python, r"C:\Arkhe\verify_constitution.py", "--quick"],
                    capture_output=True, text=True, timeout=30
                )
                if r.returncode != 0:
                    servicemanager.LogErrorMsg("ARKHE healthcheck FAIL: {0}".format(r.stderr))
                else:
                    servicemanager.LogInfoMsg("ARKHE healthcheck PASS")
            except Exception as e:
                servicemanager.LogErrorMsg("ARKHE error: {0}".format(str(e)))
            rc = win32event.WaitForSingleObject(self.hWaitStop, 60_000)
            if rc == win32event.WAIT_OBJECT_0:
                break
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ArkheBridgeService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ArkheBridgeService)