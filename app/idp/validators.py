from datetime import date
from typing import Optional

_WIEGHTS = (7, 3, 1)

def _char_value(c: str) -> int:
    if c.isdigit():
        return int(c)
    if "A" <= c <= "Z":
        return ord(c) - 55
    if c == "<":
        return 0
    raise ValueError(f"Invalid MRZ character: {c!r}")

def mrz_check_digit(data: str) -> int:
    return sum(_char_value(c) * _WIEGHTS[i % 3] for i, c in enumerate(data)) % 10

def _parse_yymmdd(s: str, is_birth: bool, today: date) -> Optional[date]:
    try:
        yy, mm, dd = int(s[0:2]), int(s[2:4]), int(s[4:6])
        year = 2000 + yy
        if is_birth and year > today.year:
            year -= 100
        return date(year, mm, dd)
    except ValueError:
        return None


def _check(name: str, passed: bool, detail: str = "") -> dict:
    return {"check": name, "passed": passed, "detail": detail}


def validate_td3_mrz(line1: str, line2: str, today: Optional[date] = None) -> dict:
    today = today or date.today()
    line1, line2 = line1.strip().upper(), line2.strip().upper()
    if len(line1) != 44 or len(line2) != 44:
        return {"fields": {}, "checks": [_check("mrz_format", False, "MRZ lines must be 44 characters each")]}

    names = line1[5:].rstrip("<")
    surname, _, given = names.partition("<<")
    dob = _parse_yymmdd(line2[13:19], True, today)
    expiry = _parse_yymmdd(line2[21:27], False, today)

    fields = {
        "document_type": line1[0:2].replace("<", ""),
        "issuing_country": line1[2:5],
        "surname": surname.replace("<", " ").strip(),
        "given_names": given.replace("<", " ").strip(),
        "document_number": line2[0:9].replace("<", ""),
        "nationality": line2[10:13],
        "date_of_birth": dob.isoformat() if dob else None,
        "sex": line2[20],
        "expiry_date": expiry.isoformat() if expiry else None,
    }

    def digit_ok(data: str, check_char: str) -> bool:
        try:
            return str(mrz_check_digit(data)) == check_char
        except ValueError:
            return False

    composite = line2[0:10] + line2[13:20] + line2[21:43]
    personal = line2[28:42]
    personal_ok = (digit_ok(personal, line2[42]) if personal.strip("<")
                   else line2[42] in ("<", "0"))   # empty personal number is allowed

    checks = [
        _check("mrz_document_number_checksum", digit_ok(line2[0:9], line2[9])),
        _check("mrz_birth_date_checksum", digit_ok(line2[13:19], line2[19])),
        _check("mrz_expiry_date_checksum", digit_ok(line2[21:27], line2[27])),
        _check("mrz_personal_number_checksum", personal_ok),
        _check("mrz_composite_checksum", digit_ok(composite, line2[43])),
        _check("birth_date_valid", dob is not None and dob < today,
               "" if dob else "unparseable date"),
        _check("not_expired", expiry is not None and expiry >= today,
               f"expires {expiry}" if expiry else "unparseable date"),
    ]
    return {"fields": fields, "checks": checks}