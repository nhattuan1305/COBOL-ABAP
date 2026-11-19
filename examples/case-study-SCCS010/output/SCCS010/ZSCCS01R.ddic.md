# ZSCCS01R (SE11 structure)

- Short description: `SCCS010 numeric item digit check parameter`
  (project rule: `数値項目桁数チェック パラメータ構造`)
- Source copybook: `SCCS01R`
- Enhancement category: Cannot be enhanced
- Package: `$TMP` (see `CLAUDE.md`)

In SE11 press **Predefined Type** to enter built-in types directly.

| Component | Data type | Length | Decimals | Short description | COBOL |
|---|---|---|---|---|---|
| BEFR_CNVR_QTY | CHAR | 20 | | Quantity string before conversion | `BEFR-CNVR-QTY PIC X(20)` |
| INT_DNUM_DAT | NUMC | 2 | | Max integer digits (0-13) | `INT-DNUM-DAT PIC 9(02)` |
| DEC_DNUM_DAT | NUMC | 2 | | Max decimal digits (0-5) | `DEC-DNUM-DAT PIC 9(02)` |
| AFTR_CNVR_QTY | DEC | 18 | 5 | Quantity after conversion | `AFTR-CNVR-QTY PIC S9(13)V9(05)` |
| RTN_CD | CHAR | 2 | | Return code OK / NG | `RTN-CD PIC X(02)` |
