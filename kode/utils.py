def isnumber(val: str) -> bool:
    return all(x.isnumeric() for x in val.split("."))
