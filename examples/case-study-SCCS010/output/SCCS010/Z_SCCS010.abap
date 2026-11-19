FUNCTION z_sccs010.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  CHANGING
*"     REFERENCE(CS_SCCS01R) TYPE  ZSCCS01R
*"----------------------------------------------------------------------
* COBOL SCCS010: numeric item digit check (spec section 1 has the JP title)
* Validates a numeric-edited string (sign, comma, period, digits) against
* the max integer / decimal digits and converts it to a number.
* Spec: output/SCCS010/spec.md

  DATA: ldf_char         TYPE c LENGTH 1,
        ldf_idx          TYPE i,            " 1-based position as in COBOL
        ldf_off          TYPE i,
        " COBOL flags X(03) 'ON '/'NOT' mapped to abap_bool
        ldf_flg_digit    TYPE abap_bool,
        ldf_flg_minus    TYPE abap_bool,
        ldf_flg_period   TYPE abap_bool,
        ldf_flg_delimit  TYPE abap_bool,
        ldf_flg_space    TYPE abap_bool,
        ldf_byte_before  TYPE c LENGTH 6,
        ldf_cnt_delimit  TYPE i,
        ldf_cnt_int_dnum TYPE i,
        ldf_cnt_dec_dnum TYPE i,
        ldf_period_digit TYPE i,
        ldf_idx_ia       TYPE i,            " next free offset in ldf_int_dnum_x
        ldf_idx_ib       TYPE i,            " next free offset in ldf_dec_dnum_x
        ldf_int_dnum_x   TYPE n LENGTH 13,
        ldf_dec_dnum_x   TYPE n LENGTH 5,
        ldf_num_c        TYPE c LENGTH 20.

  " COBOL MAIN-PROC (L108-110)
  cs_sccs01r-aftr_cnvr_qty = 0.
  cs_sccs01r-rtn_cd        = 'NG'.

  " COBOL CHECK1-PROC (L139-170)
  " CHECK-FLG is never reset in COBOL, so every error can return at once
  IF cs_sccs01r-int_dnum_dat CN '0123456789'
  OR cs_sccs01r-int_dnum_dat > 13
  OR cs_sccs01r-dec_dnum_dat CN '0123456789'
  OR cs_sccs01r-dec_dnum_dat > 5.
    RETURN.
  ENDIF.

  " COBOL CHECK2-PROC (L174-311)
  DO 20 TIMES.
    ldf_idx = sy-index.
    ldf_off = sy-index - 1.
    ldf_char = cs_sccs01r-befr_cnvr_qty+ldf_off(1).

    CASE ldf_char.
      WHEN '-'.                                          " L190-204
        IF ldf_flg_minus = abap_true
        OR ldf_flg_period = abap_true
        OR ldf_flg_delimit = abap_true
        OR ldf_flg_digit = abap_true.
          RETURN.
        ENDIF.
        ldf_flg_minus = abap_true.

      WHEN '.'.                                          " L205-225
        IF ldf_flg_period = abap_true.
          RETURN.
        ENDIF.
        IF ldf_flg_delimit = abap_true AND ldf_cnt_delimit <> 3.
          RETURN.
        ENDIF.
        ldf_flg_period   = abap_true.
        ldf_flg_digit    = abap_true.
        ldf_byte_before  = 'PERIOD'.
        ldf_period_digit = ldf_idx.

      WHEN ','.                                          " L226-249
        IF ldf_flg_period = abap_true.
          RETURN.
        ENDIF.
        IF ldf_flg_delimit = abap_true.
          IF ldf_cnt_delimit <> 3.
            RETURN.
          ENDIF.
        ELSEIF ldf_flg_digit = abap_false.
          RETURN.
        ENDIF.
        " first comma: group length before it is not checked (spec Q3)
        ldf_cnt_delimit = 0.
        ldf_flg_delimit = abap_true.
        ldf_byte_before = 'DELIMI'.

      WHEN space.                                        " L250-273
        IF ldf_flg_digit = abap_true.
          IF ldf_flg_space = abap_true.
            IF ldf_byte_before <> 'SPACE'.
              RETURN.
            ENDIF.
          ELSEIF ldf_byte_before <> 'DIGIT' AND ldf_byte_before <> 'PERIOD'.
            RETURN.
          ENDIF.
          ldf_flg_space = abap_true.
        ENDIF.
        ldf_byte_before = 'SPACE'.

      WHEN '0' OR '1' OR '2' OR '3' OR '4' OR '5' OR '6' OR '7' OR '8' OR '9'.
        IF ldf_flg_space = abap_true.                    " L274-290
          RETURN.
        ENDIF.
        IF ldf_flg_period = abap_false.
          ldf_cnt_int_dnum = ldf_cnt_int_dnum + 1.
          ldf_cnt_delimit  = ldf_cnt_delimit + 1.
          ldf_period_digit = ldf_idx + 1.
        ELSE.
          ldf_cnt_dec_dnum = ldf_cnt_dec_dnum + 1.
        ENDIF.
        ldf_flg_digit   = abap_true.
        ldf_byte_before = 'DIGIT'.

      WHEN OTHERS.                                       " L291-293
        RETURN.
    ENDCASE.
  ENDDO.

  " L297-309
  IF ldf_cnt_int_dnum > cs_sccs01r-int_dnum_dat
  OR ldf_cnt_dec_dnum > cs_sccs01r-dec_dnum_dat.
    RETURN.
  ENDIF.

  " COBOL ITEM-SET-PROC (L315-353): integer digits right-aligned in 13,
  " decimal digits left-aligned in 5
  ldf_idx_ia = 13 - ldf_cnt_int_dnum.
  ldf_idx_ib = 0.
  DO 20 TIMES.
    ldf_idx = sy-index.
    ldf_off = sy-index - 1.
    ldf_char = cs_sccs01r-befr_cnvr_qty+ldf_off(1).
    IF ldf_char CA '0123456789'.
      IF ldf_idx < ldf_period_digit.
        ldf_int_dnum_x+ldf_idx_ia(1) = ldf_char.
        ldf_idx_ia = ldf_idx_ia + 1.
      ELSE.
        ldf_dec_dnum_x+ldf_idx_ib(1) = ldf_char.
        ldf_idx_ib = ldf_idx_ib + 1.
      ENDIF.
    ENDIF.
  ENDDO.

  " exactly 5 decimals, so the c-to-p conversion does not round
  ldf_num_c = |{ ldf_int_dnum_x }.{ ldf_dec_dnum_x }|.
  cs_sccs01r-aftr_cnvr_qty = ldf_num_c.
  IF ldf_flg_minus = abap_true.
    cs_sccs01r-aftr_cnvr_qty = cs_sccs01r-aftr_cnvr_qty * -1.
  ENDIF.

  cs_sccs01r-rtn_cd = 'OK'.

ENDFUNCTION.
