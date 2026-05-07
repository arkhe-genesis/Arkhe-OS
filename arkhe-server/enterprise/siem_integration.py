class SIEMIntegration:
    def send_to_splunk(self, event):
        return f"Sent {event} to Splunk HEC"

    def send_to_elk(self, event):
        return f"Sent {event} to ELK"

def integrate_siem():
    siem = SIEMIntegration()
    return siem
