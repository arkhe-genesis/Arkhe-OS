using System;
using System.Diagnostics;
using System.ServiceProcess;
using System.Timers;
using System.IO;

namespace ArkheOS.NativeService
{
    public partial class ArkheBridgeService : ServiceBase
    {
        private Timer healthTimer;
        private string logFilePath = @"C:\Arkhe\Logs\arkhe_service.log";

        public ArkheBridgeService()
        {
            ServiceName = "ArkheBridge";
            CanStop = true;
            CanPauseAndContinue = false;
            AutoLog = true;
        }

        protected override void OnStart(string[] args)
        {
            LogMessage("ARKHE OS Constitutional Bridge Service starting...");
            healthTimer = new Timer(60000); // 60s healthcheck
            healthTimer.Elapsed += new ElapsedEventHandler(OnTimer);
            healthTimer.Start();
        }

        protected override void OnStop()
        {
            LogMessage("ARKHE OS Constitutional Bridge Service stopping...");
            healthTimer.Stop();
        }

        private void OnTimer(object sender, ElapsedEventArgs args)
        {
            try
            {
                ProcessStartInfo startInfo = new ProcessStartInfo();
                startInfo.FileName = @"C:\Arkhe\venv\Scripts\python.exe";
                startInfo.Arguments = @"C:\Arkhe\verify_constitution_windows.py --quick";
                startInfo.UseShellExecute = false;
                startInfo.RedirectStandardOutput = true;
                startInfo.RedirectStandardError = true;
                startInfo.CreateNoWindow = true;

                using (Process process = Process.Start(startInfo))
                {
                    process.WaitForExit(30000);
                    if (process.ExitCode == 0)
                    {
                        LogMessage("ARKHE healthcheck PASS (Native C# Bridge)");
                    }
                    else
                    {
                        string stderr = process.StandardError.ReadToEnd();
                        LogMessage("ARKHE healthcheck FAIL: " + stderr);
                    }
                }
            }
            catch (Exception ex)
            {
                LogMessage("ARKHE healthcheck ERROR: " + ex.Message);
            }
        }

        private void LogMessage(string message)
        {
            try
            {
                string entry = string.Format("[{0}] {1}\n", DateTime.UtcNow.ToString("O"), message);
                File.AppendAllText(logFilePath, entry);
            }
            catch
            {
                // Fallback to event log if file fails
                EventLog.WriteEntry(message, EventLogEntryType.Information);
            }
        }
    }

    static class Program
    {
        static void Main()
        {
            ServiceBase[] ServicesToRun;
            ServicesToRun = new ServiceBase[]
            {
                new ArkheBridgeService()
            };
            ServiceBase.Run(ServicesToRun);
        }
    }
}
