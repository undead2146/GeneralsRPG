from pathlib import Path

def bundled_data_path(cog):
    # Return a path under the cog directory named 'data'
    return Path(cog.__file__).parent / "data"


def cog_data_path(cog):
    return Path(cog.__file__).parent / "data"
