class VersionInfo:
    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def from_str(cls, s: str):
        parts = s.split(".")
        parts = [int(p) for p in parts]
        while len(parts) < 3:
            parts.append(0)
        return cls(*parts[:3])

    def __ge__(self, other):
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)


version_info = VersionInfo.from_str("3.4.0")

__all__ = ["VersionInfo", "version_info"]
