import datetime

def get_date_from_iso_string(iso_date_string: str) -> datetime.date:
    assert isinstance(iso_date_string,str) and iso_date_string
    parts = str.split(iso_date_string,'T')    
    return datetime.datetime.strptime(parts[0],'%Y-%m-%d')   
