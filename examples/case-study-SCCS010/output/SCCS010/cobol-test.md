# SCCS010: COBOL test run (GnuCOBOL)

Cases: `cases.json`. Result: 32 PASS, 0 FAIL, 1 probe.

## Run conditions

- Compile: `cobc -x -std=ibm -ext txt -fnot-reserved=SHIFT-OUT,SHIFT-IN,NEW -fdefaultbyte=0 -I . -o ctdriver.exe ctdriver.cbl SCCS010.txt`
- IBM-only syntax removed in the work copy (originals unchanged): SCCS010.txt L1: PROCESS APOST GRAPHIC CVTPICGGRAPHIC CHGPOSSGN STDINZHEX00.; SCCS010.txt L48: DATA-AREA  IS  DTAARA.
- Stubbed programs (do nothing): none
- Programs with file I/O: none
- Runs in ASCII, not EBCDIC: comparisons / sorting that mix letters and digits may differ from IBM i.

## Cases

| # | Input | Expected | COBOL result | Status |
|---|---|---|---|---|
| T1 | {"BEFR_CNVR_QTY": "1234"} | {"AFTR_CNVR_QTY": "1234", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000001234.00000", "RTN_CD": "OK"} | PASS |
| T2 | {"BEFR_CNVR_QTY": "-1,234.56"} | {"AFTR_CNVR_QTY": "-1234.56", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "-0000000001234.56000", "RTN_CD": "OK"} | PASS |
| T3 | {"BEFR_CNVR_QTY": "1,234,567.89"} | {"AFTR_CNVR_QTY": "1234567.89", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000001234567.89000", "RTN_CD": "OK"} | PASS |
| T4 | {"BEFR_CNVR_QTY": "-.5"} | {"AFTR_CNVR_QTY": "-0.5", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "-0000000000000.50000", "RTN_CD": "OK"} | PASS |
| T5 | {"BEFR_CNVR_QTY": "  12.5 "} | {"AFTR_CNVR_QTY": "12.5", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000012.50000", "RTN_CD": "OK"} | PASS |
| T6 | {"BEFR_CNVR_QTY": "12."} | {"AFTR_CNVR_QTY": "12", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000012.00000", "RTN_CD": "OK"} | PASS |
| T7 | {"BEFR_CNVR_QTY": "9999999999999.99999"} | {"AFTR_CNVR_QTY": "9999999999999.99999", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "9999999999999.99999", "RTN_CD": "OK"} | PASS |
| T8 | {"BEFR_CNVR_QTY": "12 34"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T9 | {"BEFR_CNVR_QTY": "1,23.4"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T10 | {"BEFR_CNVR_QTY": ",123"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T11 | {"BEFR_CNVR_QTY": "1.2,3"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T12 | {"BEFR_CNVR_QTY": "12a"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T13 | {"BEFR_CNVR_QTY": "5-"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T14 | {"BEFR_CNVR_QTY": "--5"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T15 | {"BEFR_CNVR_QTY": "1.2.3"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T16 | {"BEFR_CNVR_QTY": "123456", "INT_DNUM_DAT": 5} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T17 | {"BEFR_CNVR_QTY": "1.234567"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T18 | {"BEFR_CNVR_QTY": "1", "INT_DNUM_DAT": 14} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T19 | {"BEFR_CNVR_QTY": "1", "DEC_DNUM_DAT": 6} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T20 | {"BEFR_CNVR_QTY": "1", "INT_DNUM_DAT": 0, "DEC_DNUM_DAT": 0} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T21 | {"BEFR_CNVR_QTY": "1,234,"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T22 | {"BEFR_CNVR_QTY": ""} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "OK"} | PASS |
| T23 | {"BEFR_CNVR_QTY": "1,23"} | {"AFTR_CNVR_QTY": "123", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000123.00000", "RTN_CD": "OK"} | PASS |
| T24 | {"BEFR_CNVR_QTY": "12345,678"} | {"AFTR_CNVR_QTY": "12345678", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000012345678.00000", "RTN_CD": "OK"} | PASS |
| T25 | {"BEFR_CNVR_QTY": "- 5"} | {"AFTR_CNVR_QTY": "-5", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "-0000000000005.00000", "RTN_CD": "OK"} | PASS |
| T26 | {"BEFR_CNVR_QTY": "."} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "OK"} | PASS |
| T27 | {"BEFR_CNVR_QTY": "-"} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "OK"} | PASS |
| T28 | {"BEFR_CNVR_QTY": "              1,234,"} | {"AFTR_CNVR_QTY": "1234", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000001234.00000", "RTN_CD": "OK"} | PASS |
| T29 | {"BEFR_CNVR_QTY": "                 1 ."} | {"AFTR_CNVR_QTY": "1", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000001.00000", "RTN_CD": "OK"} | PASS |
| T30 | {"BEFR_CNVR_QTY": ".5", "INT_DNUM_DAT": 0} | {"AFTR_CNVR_QTY": "0.5", "RTN_CD": "OK"} | {"AFTR_CNVR_QTY": "0000000000000.50000", "RTN_CD": "OK"} | PASS |
| T31 | {"BEFR_CNVR_QTY": "0.5", "INT_DNUM_DAT": 0} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| T32 | {"BEFR_CNVR_QTY": "1", "INT_DNUM_DAT": {"raw": "1 "}} | {"AFTR_CNVR_QTY": "0", "RTN_CD": "NG"} | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PASS |
| P1 | {"BEFR_CNVR_QTY": "1,2345.6"} |  | {"AFTR_CNVR_QTY": "0000000000000.00000", "RTN_CD": "NG"} | PROBE |
