"""
Domain Profiles
"""
class DomainProfiles:
    def __init__(self):
        self.profiles = {}

    def get_profile(self, domain):
        return self.profiles.get(domain, {})
