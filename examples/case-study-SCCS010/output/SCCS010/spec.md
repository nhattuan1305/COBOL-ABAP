# SCCS010: Numeric item digit check (（精）統合 数値項目桁数チェック)

Status: READY
Analysed: 2026-11-19 by cobol-analyst (case study, reviewed by hand)

## 1. Summary

FM nhận một chuỗi số lượng có định dạng, ví dụ `-1,234.56`. Kèm theo là số
chữ số tối đa cho phần nguyên và phần thập phân. FM kiểm tra dấu `-`, `,`,
`.` có đúng vị trí không, và số chữ số có vượt giới hạn không. Hợp lệ thì
trả về giá trị số và `OK`. Không hợp lệ thì trả `NG` và giá trị 0.

Ví dụ: `'-1,234.56'`, nguyên tối đa 13, thập phân tối đa 5 → `-1234.56`, `OK`.

| Item | Value |
|---|---|
| Function module | `Z_SCCS010` (function group `Z_SCCS`) |
| Parameter | `CHANGING cs_sccs01r TYPE zsccs01r` (by reference) |
| Calls other FMs | none |
| Database / files | none |
| State between calls | none (fresh local data every call) |

## 2. Interface: structure `ZSCCS01R`

| Field | Type | In / Out | Meaning | Example |
|---|---|---|---|---|
| `BEFR_CNVR_QTY` | CHAR 20 | in | Chuỗi số lượng cần đổi | `'-1,234.56'` |
| `INT_DNUM_DAT` | NUMC 2 | in | Số chữ số phần nguyên tối đa. Hợp lệ `00`-`13` | `13` |
| `DEC_DNUM_DAT` | NUMC 2 | in | Số chữ số thập phân tối đa. Hợp lệ `00`-`05` | `05` |
| `AFTR_CNVR_QTY` | DEC 18, 5 decimals | out | Giá trị số sau khi đổi | `-1234.56` |
| `RTN_CD` | CHAR 2 | out | Kết quả | `OK` |

Result codes:

| `RTN_CD` | Meaning | Other outputs |
|---|---|---|
| `OK` | Chuỗi hợp lệ | `AFTR_CNVR_QTY` = giá trị đã đổi |
| `NG` | Tham số hoặc chuỗi không hợp lệ | `AFTR_CNVR_QTY` = 0 |

## 3. Rules

**Tham số giới hạn**

| Field | Lỗi (`NG`) khi |
|---|---|
| `INT_DNUM_DAT` | có ký tự không phải số, hoặc > 13 |
| `DEC_DNUM_DAT` | có ký tự không phải số, hoặc > 5 |

**Từng ký tự của `BEFR_CNVR_QTY`** (đọc từ trái sang phải, đủ 20 ký tự)

"Chữ số" trong bảng tính cả dấu `.`: sau khi gặp `.` thì coi như đã có chữ số.

| Ký tự | Lỗi (`NG`) khi |
|---|---|
| `-` | Trước nó đã có `-`, `.`, `,` hoặc chữ số |
| `.` | Đã có `.` trước đó. Hoặc đã có `,` mà từ `,` cuối tới `.` không đúng 3 chữ số |
| `,` | Đã có `.` trước đó. Hoặc chưa có chữ số nào. Hoặc đây là dấu phẩy thứ 2 trở đi mà nhóm giữa hai dấu phẩy không đúng 3 chữ số |
| khoảng trắng | Chưa có chữ số: luôn hợp lệ. Đã có chữ số: khoảng trắng đầu tiên phải đứng ngay sau chữ số hoặc `.`; các khoảng trắng sau phải đứng ngay sau một khoảng trắng |
| `0`-`9` | Đã có khoảng trắng nào đứng sau chữ số trước đó |
| ký tự khác | Luôn lỗi (`+`, chữ cái, tab, ký tự full-width...) |

Dấu `-` không được tính là "ký tự đứng trước" khi xét khoảng trắng.
Dấu phẩy đầu tiên không kiểm độ dài nhóm đứng trước nó.

**Số chữ số**

| Đếm | Lỗi (`NG`) khi |
|---|---|
| Chữ số đứng trước `.` (hoặc tất cả, nếu không có `.`) | nhiều hơn `INT_DNUM_DAT` |
| Chữ số đứng sau `.` | nhiều hơn `DEC_DNUM_DAT` |

Số 0 ở đầu và ở cuối cũng được đếm (`'01'` là 2 chữ số).

## 4. Processing steps

```
1. cs_sccs01r-aftr_cnvr_qty = 0.  cs_sccs01r-rtn_cd = 'NG'.

2. Check INT_DNUM_DAT / DEC_DNUM_DAT (section 3).        error -> RETURN

3. DO 20 TIMES.  ldf_idx = sy-index.  ldf_char = character at ldf_idx.
     CASE ldf_char.                                       error -> RETURN
       '-'   : check rule; ldf_flg_minus = true.
       '.'   : check rule; ldf_flg_period = true; ldf_flg_digit = true;
               ldf_byte_before = 'PERIOD'; ldf_period_digit = ldf_idx.
       ','   : check rule; ldf_cnt_delimit = 0; ldf_flg_delimit = true;
               ldf_byte_before = 'DELIMI'.
       space : check rule; IF ldf_flg_digit = true: ldf_flg_space = true.
               ldf_byte_before = 'SPACE'.
       '0'-'9': check rule;
               IF ldf_flg_period = false: ldf_cnt_int_dnum + 1,
                  ldf_cnt_delimit + 1, ldf_period_digit = ldf_idx + 1.
               ELSE: ldf_cnt_dec_dnum + 1.
               ldf_flg_digit = true; ldf_byte_before = 'DIGIT'.
       OTHERS: RETURN.
   ENDDO.

4. IF ldf_cnt_int_dnum > int_dnum_dat OR ldf_cnt_dec_dnum > dec_dnum_dat
   -> RETURN.

5. DO 20 TIMES again. For each digit:
     position < ldf_period_digit -> next free place of ldf_int_dnum_x
                                   (right-aligned: start at offset 13 - ldf_cnt_int_dnum)
     otherwise                  -> next free place of ldf_dec_dnum_x (left-aligned)

6. cs_sccs01r-aftr_cnvr_qty = '<ldf_int_dnum_x>.<ldf_dec_dnum_x>'.
   IF ldf_flg_minus = true: multiply by -1.
   cs_sccs01r-rtn_cd = 'OK'.
```

## 5. Local variables

| ABAP variable | Type | Purpose |
|---|---|---|
| `ldf_char` | c LENGTH 1 | Ký tự đang xét |
| `ldf_idx` | i | Vị trí đang xét, 1-20 |
| `ldf_off` | i | Offset của ký tự đang xét (`ldf_idx - 1`) |
| `ldf_flg_minus` | abap_bool | Đã gặp `-` |
| `ldf_flg_period` | abap_bool | Đã gặp `.` |
| `ldf_flg_delimit` | abap_bool | Đã gặp `,` |
| `ldf_flg_digit` | abap_bool | Đã gặp chữ số hoặc `.` |
| `ldf_flg_space` | abap_bool | Đã gặp khoảng trắng sau chữ số |
| `ldf_byte_before` | c LENGTH 6 | Loại ký tự liền trước: `DIGIT`, `PERIOD`, `DELIMI`, `SPACE` |
| `ldf_cnt_delimit` | i | Số chữ số kể từ dấu `,` gần nhất |
| `ldf_cnt_int_dnum` | i | Số chữ số phần nguyên |
| `ldf_cnt_dec_dnum` | i | Số chữ số phần thập phân |
| `ldf_period_digit` | i | Vị trí ranh giới nguyên / thập phân |
| `ldf_int_dnum_x` | n LENGTH 13 | 13 chữ số phần nguyên, căn phải |
| `ldf_dec_dnum_x` | n LENGTH 5 | 5 chữ số thập phân, căn trái |
| `ldf_idx_ia` / `ldf_idx_ib` | i | Chỗ trống tiếp theo trong `ldf_int_dnum_x` / `ldf_dec_dnum_x` |
| `ldf_num_c` | c LENGTH 20 | Chuỗi `<13 số>.<5 số>` trước khi gán vào kết quả |

## 6. Behavior to keep

| # | Input | Result | Why, in one sentence | Looks intended? |
|---|---|---|---|---|
| Q1 | Toàn khoảng trắng | `OK`, 0 | Không có chữ số nên không có gì sai | probably not |
| Q2 | `1,23` | `OK`, 123 | Nhóm sau dấu phẩy cuối chỉ bị kiểm khi có `.` phía sau | probably not |
| Q3 | `12345,678` | `OK`, 12345678 | Dấu phẩy đầu tiên không kiểm nhóm đứng trước nó | probably not |
| Q4 | `- 5` | `OK`, -5 | Khoảng trắng trước chữ số đầu tiên luôn được bỏ qua | probably not |
| Q5 | `.` hoặc `-` một mình | `OK`, 0 | Không có chữ số nên không có gì sai | probably not |
| Q6 | `12.` | `OK`, 12 | `.` ở cuối hợp lệ, phần thập phân bằng 0 | yes |
| Q7 | `1,234,` căn trái | `NG` | Khoảng trắng đứng ngay sau `,` | yes |
| Q8 | `1,234,` căn phải (dấu `,` ở vị trí 20) | `OK`, 1234 | Không còn ký tự nào sau `,` nên không bị lỗi như Q7 | probably not |
| Q9 | `1 .` căn phải | `OK`, 1 | Dấu `.` không bị chặn sau khoảng trắng, chỉ chữ số và khoảng trắng bị chặn | probably not |
| Q10 | `.5` với `INT_DNUM_DAT = 00` | `OK`, 0.5 | Không có chữ số phần nguyên nào | yes |
| Q11 | `0.5` với `INT_DNUM_DAT = 00` | `NG` | Số `0` cũng là một chữ số phần nguyên | yes |

## 7. ABAP implementation notes

- Được `RETURN` ngay khi gặp lỗi đầu tiên. Output lúc đó đã là 0 và `NG`.
- Kiểm tham số bằng `CN '0123456789'` trước khi so sánh `> 13`. Không đổi
  NUMC sang `i` trước khi kiểm.
- Lấy ký tự bằng offset: `cs_sccs01r-befr_cnvr_qty+ldf_off(1)`, với
  `ldf_off = ldf_idx - 1`.
- Không cộng từng chữ số. Ghép chuỗi `|{ ldf_int_dnum_x }.{ ldf_dec_dnum_x }|`
  rồi gán vào `AFTR_CNVR_QTY`. Đúng 5 số lẻ nên không bị làm tròn.
- Khoảng trắng full-width không phải `space`, nên rơi vào `OTHERS` và lỗi.
  Như vậy là đúng.
- Không `MESSAGE`, không `WRITE` trong FM.

## 8. Open questions

| # | Question | Assumption used | BLOCKING? |
|---|---|---|---|
| OQ1 | Có giữ các hành vi Q1-Q5, Q8, Q9 (chấp nhận input không chuẩn) không? | Giữ nguyên như hệ thống cũ | no |

## 9. Test cases

Input căn trái, phần còn lại là khoảng trắng, trừ khi ghi "căn phải".

| # | `BEFR_CNVR_QTY` | `INT_DNUM_DAT` | `DEC_DNUM_DAT` | → `AFTR_CNVR_QTY` | → `RTN_CD` | Covers |
|---|---|---|---|---|---|---|
| T1 | `1234` | 13 | 05 | 1234 | `OK` | chữ số |
| T2 | `-1,234.56` | 13 | 05 | -1234.56 | `OK` | `-` `,` `.` |
| T3 | `1,234,567.89` | 13 | 05 | 1234567.89 | `OK` | nhiều nhóm phẩy |
| T4 | `-.5` | 13 | 05 | -0.5 | `OK` | không có phần nguyên |
| T5 | `  12.5 ` | 13 | 05 | 12.5 | `OK` | khoảng trắng đầu / cuối |
| T6 | `12.` | 13 | 05 | 12 | `OK` | Q6 |
| T7 | `9999999999999.99999` | 13 | 05 | 9999999999999.99999 | `OK` | giá trị lớn nhất |
| T8 | `12 34` | 13 | 05 | 0 | `NG` | khoảng trắng giữa chữ số |
| T9 | `1,23.4` | 13 | 05 | 0 | `NG` | nhóm trước `.` khác 3 |
| T10 | `,123` | 13 | 05 | 0 | `NG` | `,` trước chữ số |
| T11 | `1.2,3` | 13 | 05 | 0 | `NG` | `,` sau `.` |
| T12 | `12a` | 13 | 05 | 0 | `NG` | ký tự lạ |
| T13 | `5-` | 13 | 05 | 0 | `NG` | `-` sau chữ số |
| T14 | `--5` | 13 | 05 | 0 | `NG` | hai dấu `-` |
| T15 | `1.2.3` | 13 | 05 | 0 | `NG` | hai dấu `.` |
| T16 | `123456` | 05 | 05 | 0 | `NG` | vượt số chữ số nguyên |
| T17 | `1.234567` | 13 | 05 | 0 | `NG` | vượt số chữ số thập phân |
| T18 | `1` | 14 | 05 | 0 | `NG` | tham số > 13 |
| T19 | `1` | 13 | 06 | 0 | `NG` | tham số > 5 |
| T20 | `1` | 00 | 00 | 0 | `NG` | giới hạn 0 |
| T21 | `1,234,` | 13 | 05 | 0 | `NG` | Q7 |
| T22 | (toàn khoảng trắng) | 13 | 05 | 0 | `OK` | Q1 |
| T23 | `1,23` | 13 | 05 | 123 | `OK` | Q2 |
| T24 | `12345,678` | 13 | 05 | 12345678 | `OK` | Q3 |
| T25 | `- 5` | 13 | 05 | -5 | `OK` | Q4 |
| T26 | `.` | 13 | 05 | 0 | `OK` | Q5 |
| T27 | `-` | 13 | 05 | 0 | `OK` | Q5 |
| T28 | `1,234,` căn phải (14 khoảng trắng + `1,234,`) | 13 | 05 | 1234 | `OK` | Q8 |
| T29 | `1 .` căn phải (17 khoảng trắng + `1 .`) | 13 | 05 | 1 | `OK` | Q9 |
| T30 | `.5` | 00 | 05 | 0.5 | `OK` | Q10 |
| T31 | `0.5` | 00 | 05 | 0 | `NG` | Q11 |

---

## Appendix A. COBOL traceability (for reviewers)

Source: `input/SCCS010/SCCS010.txt`, 355 lines.

### A.1 Steps → COBOL

| Step (section 4) | COBOL section / paragraph | Lines |
|---|---|---|
| 1 | `MAIN-PROC` | L108-110 |
| 2 | `CHECK1-PROC` | L139-170 |
| 3 | `CHECK2-PROC` (loop) | L174-295 |
| 3 `'-'` / `'.'` / `','` / space / digit / other | `EVALUATE BEFORE-TBL (IX)` | L190-204 / L205-225 / L226-249 / L250-273 / L274-290 / L291-293 |
| 4 | `CHECK2-PROC` (count check) | L297-309 |
| 5-6 | `ITEM-SET-PROC` | L315-353 |

### A.2 Fields → COBOL

| ABAP name | COBOL field | PIC / initial value |
|---|---|---|
| `BEFR_CNVR_QTY` | `BEFR-CNVR-QTY` | `X(20)` |
| `INT_DNUM_DAT` / `DEC_DNUM_DAT` | `INT-DNUM-DAT` / `DEC-DNUM-DAT` | `9(02)` |
| `AFTR_CNVR_QTY` | `AFTR-CNVR-QTY` | `S9(13)V9(05)` |
| `RTN_CD` | `RTN-CD` | `X(02)` |
| `ldf_flg_minus` ... `ldf_flg_space` | `MINUS-FLG`, `PERIOD-FLG`, `DELIMIT-FLG`, `DIGIT-FLG`, `SPACE-FLG` | `X(03)`, `'ON '` / `'NOT'` |
| `ldf_byte_before` | `BYTE-BEFORE` | `X(06)` |
| `ldf_cnt_delimit`, `ldf_cnt_int_dnum`, `ldf_cnt_dec_dnum` | `DELIMIT-CNT`, `INT-DNUM-CNT`, `DEC-DNUM-CNT` | `9(02)` |
| `ldf_period_digit` | `PERIOD-DIGIT` | `9(02)`, not initialised |
| `ldf_int_dnum_x` / `ldf_dec_dnum_x` | `INT-DNUM-TABLE` → `INT-DNUM-X` / `DEC-DNUM-TABLE` → `DEC-DNUM-X` | `X(01) OCCURS 13` / `OCCURS 5` |

### A.3 Source facts and proofs

- `PROGRAM-ID ... IS INITIAL` (L3): working storage is fresh on every call,
  so local `DATA` in the FM is correct.
- Error flag `CHECK-FLG` is set to `'ERR'` on every error and never reset
  after L110. The loop keeps running after an error but writes no output.
  Output on error is always 0 / `NG` from L108-109. So early `RETURN` gives
  the same result. Also checked by comparing a port of the FM with a
  line-by-line simulation of the COBOL on 300,000 random inputs: 0
  differences.
- `PERIOD-DIGIT` is not initialised (`STDINZHEX00`, L1). It is only read at
  L327, for a digit, and is then always set (L285 before `.`, L225 after).
  Initial value 0 in ABAP is enough.
- `COPY CVTCOMMON` (L56), `DATA-AREA` (L48) and `C01 IS PCHANGE` (L47) are
  declared but not used by the logic.
- `NUMERIC` on `9(02)` (L144, L158) checks raw bytes. ABAP NUMC filters on
  normal assignment, so `CN '0123456789'` only matters for values passed by
  casting. Kept for equivalence.
- `WHEN '0' THRU '9'` (L274): pure digit range, so EBCDIC order makes no
  difference.
- `.` sets `DIGIT-FLG` (L223); `-` does not change `BYTE-BEFORE` (L190-204);
  the `.` and `,` branches do not test `SPACE-FLG` (L205-249). These three
  facts explain Q4, Q8 and Q9.
