from datetime import date
from app.idp.validators import validate_td3_mrz, mrz_check_digit

L1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
L2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"


def _by_name(result):
    return {c["check"]: c for c in result["checks"]}


def test_check_digit_known_values():
    assert mrz_check_digit("L898902C3") == 6
    assert mrz_check_digit("740812") == 2


def test_specimen_passes_all_checksums():
    r = validate_td3_mrz(L1, L2, today=date(2010, 1, 1))
    assert all(c["passed"] for c in r["checks"]), r["checks"]
    assert r["fields"]["surname"] == "ERIKSSON"
    assert r["fields"]["given_names"] == "ANNA MARIA"
    assert r["fields"]["date_of_birth"] == "1974-08-12"


def test_tampered_document_number_is_caught():
    bad = "L898902C46" + L2[10:]          # changed one digit of the number
    r = _by_name(validate_td3_mrz(L1, bad, today=date(2010, 1, 1)))
    assert not r["mrz_document_number_checksum"]["passed"]
    assert not r["mrz_composite_checksum"]["passed"]


def test_expired_passport_is_flagged():
    r = _by_name(validate_td3_mrz(L1, L2, today=date(2020, 1, 1)))
    assert not r["not_expired"]["passed"]


def test_wrong_length_rejected():
    r = validate_td3_mrz("P<UTO", L2)
    assert not r["checks"][0]["passed"]