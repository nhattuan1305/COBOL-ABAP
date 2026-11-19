REPORT ztest_sccs010.
* Runs every test case of output/SCCS010/spec.md section 9 against Z_SCCS010
* and prints PASS / FAIL per case.

TYPES: BEGIN OF gts_case,
         id    TYPE c LENGTH 4,
         qty   TYPE c LENGTH 20,
         int   TYPE n LENGTH 2,
         dec   TYPE n LENGTH 2,
         exp_v TYPE p LENGTH 10 DECIMALS 5,
         exp_r TYPE c LENGTH 2,
       END OF gts_case,
       gtt_case TYPE STANDARD TABLE OF gts_case WITH EMPTY KEY.

DATA: gdt_case     TYPE gtt_case,
      gds_case     TYPE gts_case,
      gds_param    TYPE zsccs01r,
      gdf_cnt_fail TYPE i.

START-OF-SELECTION.
  gdt_case = VALUE #(
    ( id = 'T1'  qty = '1234'                int = '13' dec = '05' exp_v = '1234'                exp_r = 'OK' )
    ( id = 'T2'  qty = '-1,234.56'           int = '13' dec = '05' exp_v = '-1234.56'            exp_r = 'OK' )
    ( id = 'T3'  qty = '1,234,567.89'        int = '13' dec = '05' exp_v = '1234567.89'          exp_r = 'OK' )
    ( id = 'T4'  qty = '-.5'                 int = '13' dec = '05' exp_v = '-0.5'                exp_r = 'OK' )
    ( id = 'T5'  qty = '  12.5 '             int = '13' dec = '05' exp_v = '12.5'                exp_r = 'OK' )
    ( id = 'T6'  qty = '12.'                 int = '13' dec = '05' exp_v = '12'                  exp_r = 'OK' )
    ( id = 'T7'  qty = '9999999999999.99999' int = '13' dec = '05' exp_v = '9999999999999.99999' exp_r = 'OK' )
    ( id = 'T8'  qty = '12 34'               int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T9'  qty = '1,23.4'              int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T10' qty = ',123'                int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T11' qty = '1.2,3'               int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T12' qty = '12a'                 int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T13' qty = '5-'                  int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T14' qty = '--5'                 int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T15' qty = '1.2.3'               int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T16' qty = '123456'              int = '05' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T17' qty = '1.234567'            int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T18' qty = '1'                   int = '14' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T19' qty = '1'                   int = '13' dec = '06' exp_v = 0 exp_r = 'NG' )
    ( id = 'T20' qty = '1'                   int = '00' dec = '00' exp_v = 0 exp_r = 'NG' )
    ( id = 'T21' qty = '1,234,'              int = '13' dec = '05' exp_v = 0 exp_r = 'NG' )
    ( id = 'T22' qty = space                 int = '13' dec = '05' exp_v = 0 exp_r = 'OK' )
    ( id = 'T23' qty = '1,23'                int = '13' dec = '05' exp_v = '123'      exp_r = 'OK' )
    ( id = 'T24' qty = '12345,678'           int = '13' dec = '05' exp_v = '12345678' exp_r = 'OK' )
    ( id = 'T25' qty = '- 5'                 int = '13' dec = '05' exp_v = '-5'       exp_r = 'OK' )
    ( id = 'T26' qty = '.'                   int = '13' dec = '05' exp_v = 0 exp_r = 'OK' )
    ( id = 'T27' qty = '-'                   int = '13' dec = '05' exp_v = 0 exp_r = 'OK' )
    ( id = 'T28' qty = '              1,234,' int = '13' dec = '05' exp_v = '1234'     exp_r = 'OK' )
    ( id = 'T29' qty = '                 1 .' int = '13' dec = '05' exp_v = '1'        exp_r = 'OK' )
    ( id = 'T30' qty = '.5'                  int = '00' dec = '05' exp_v = '0.5'      exp_r = 'OK' )
    ( id = 'T31' qty = '0.5'                 int = '00' dec = '05' exp_v = 0 exp_r = 'NG' ) ).

  LOOP AT gdt_case INTO gds_case.
    CLEAR gds_param.
    gds_param-befr_cnvr_qty = gds_case-qty.
    gds_param-int_dnum_dat  = gds_case-int.
    gds_param-dec_dnum_dat  = gds_case-dec.

    CALL FUNCTION 'Z_SCCS010'
      CHANGING
        cs_sccs01r = gds_param.

    IF gds_param-aftr_cnvr_qty = gds_case-exp_v AND gds_param-rtn_cd = gds_case-exp_r.
      WRITE: / gds_case-id, 'PASS'.
    ELSE.
      gdf_cnt_fail = gdf_cnt_fail + 1.
      WRITE: / gds_case-id, 'FAIL',
               'exp=', gds_case-exp_v, gds_case-exp_r,
               'got=', gds_param-aftr_cnvr_qty, gds_param-rtn_cd.
    ENDIF.
  ENDLOOP.

  ULINE.
  WRITE: / |Total: { lines( gdt_case ) }  Failed: { gdf_cnt_fail }|.
