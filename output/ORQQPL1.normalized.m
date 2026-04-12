ORQQPL1 ; ALB/PDR,REV,ISL/JER,TC,LAB - PROBLEM LIST FOR CPRS GUI ;03 April 2018 10:25 AM
 ;;3.0;ORDER ENTRY/RESULTS REPORTING;**10,85,148,173,203,206,249,243,280,306,361,385,350,479**;Dec 17, 1997;Build 5
 ;
 ;------------------------- GET PROBLEM FROM LEXICON -------------------
 ;
LEXSRCH(LIST,FROM,N,VIEW,ORDATE) ; Get candidate Problems from LEX file
 NEW LEX,VAL,VAL1,COD,CIEN,SYS,MAX,NAME,ORIMPDT,ICDCSYS,ICDCODE
 SET ORIMPDT=$$IMPDATE^LEXU("10D")
 S:'+$GET(ORDATE) ORDATE=DT
 S:'$GET(N) N=100
 S:'$LENGTH($GET(VIEW)) VIEW="PL1"
 DO CONFIG^LEXSET("GMPL",VIEW,ORDATE)
 DO LOOK^LEXA(FROM,"GMPL",N,"",ORDATE)
 SET S=0
 FOR  S S=$ORDER(LEX("LIST",S)) Q:S<1  D
 . S VAL1=LEX("LIST",S)
 . S COD="",CIEN="",SYS="",NAME="",ICDCODE=""
 . S ICDCSYS=$S(ORDATE<ORIMPDT:"ICD",1:"10D")
 . I $LENGTH(VAL1,"CPT-4 ")>1 D
 .. S SYS=$S(ORDATE<ORIMPDT:"ICD-9-CM ",1:"ICD-10-CM ")
 .. S COD=$S(ORDATE<ORIMPDT:"799.9",1:"R69")
 .. S CIEN=""
 .. S NAME=$PIECE(VAL1," (CPT-4")
 . I $LENGTH(VAL1,"DSM-IV ")>1 D
 .. S SYS="DSM-IV "
 .. S COD=$PIECE($PIECE(VAL1,SYS,2),")")
 .. S:COD["/" COD=$PIECE(COD,"/",1)
 .. S ICDCODE=$$ONE^LEXU($PIECE(VAL1,U,1),ORDATE,ICDCSYS)
 .. S ICDCODE=$S(ICDCODE["":COD,1:ICDCODE)
 .. S CIEN=+$$ICDDATA^ICDXCODE(ICDCSYS,$GET(ICDCODE),ORDATE,"E")
 .. S NAME=$PIECE(VAL1," (DSM-IV")
 .. ;
 . I $LENGTH(VAL1,"(TITLE 38 ")>1 D
 .. S SYS="TITLE 38 "
 .. S COD=$PIECE($PIECE(VAL1,SYS,2),")")
 .. S:COD["/" COD=$PIECE(COD,"/",1)
 .. S ICDCODE=$$ONE^LEXU($PIECE(VAL1,U,1),ORDATE,ICDCSYS)
 .. S ICDCODE=$S(ICDCODE["":COD,1:ICDCODE)
 .. S CIEN=+$$ICDDATA^ICDXCODE(ICDCSYS,$GET(ICDCODE),ORDATE,"E")
 .. S NAME=$PIECE(VAL1,"(TITLE 38 ")
 .. ;
 . I $LENGTH(VAL1,"ICD-9-CM ")>1 D
 .. S SYS="ICD-9-CM "
 .. S COD=$PIECE($PIECE(VAL1,SYS,2),")")
 .. S:COD["/" COD=$PIECE(COD,"/",1)
 .. S CIEN=+$$ICDDATA^ICDXCODE("DIAG",$GET(COD),ORDATE,"E")
 .. S NAME=$PIECE(VAL1," (ICD-9-CM")
 .. ;
 . I $LENGTH(VAL1,"ICD-10-CM ")>1 D
 .. S SYS="ICD-10-CM "
 .. S COD=$PIECE($PIECE(VAL1,SYS,2),")")
 .. S:COD["/" COD=$PIECE(COD,"/",1)
 .. S CIEN=+$$ICDDATA^ICDXCODE("DIAG",$GET(COD),ORDATE,"E")
 .. S NAME=$PIECE(VAL1," (ICD-10-CM")
 . I $LENGTH(NAME)=0 S NAME=$PIECE($PIECE(VAL1," (")," *")
 . ;
 . ; jeh Clean left over codes
 . S NAME=$PIECE(NAME," (CPT-4")
 . S NAME=$PIECE(NAME," (DSM-IV")
 . S NAME=$PIECE(NAME,"(TITLE 38 ")
 . S NAME=$PIECE(NAME," (ICD-9-CM")
 . S NAME=$PIECE(NAME," (ICD-10-CM")
 . ;
 . S VAL=NAME_U_COD_U_CIEN_U_SYS ; ien^.01^icd^icdifn^system
 . S LIST(S)=VAL
 . S MAX=S
 IF $GET(MAX)'="" S LIST(MAX+1)=$GET(LEX("MAT"))
 KILL ^TMP("LEXSCH",$J)
 Q
 ;
SORT(LEX) ; Sort terms alphabetically
 NEW ORI S ORI=0
 FOR  S ORI=$ORDER(LEX("LIST",ORI)) Q:+ORI'>0  S LEX("ALPHA",$EXTRACT($PIECE(LEX("LIST",ORI),U,2),1,255),ORI)=""
 Q
 ;
ICDREC(COD) ;
 NEW CODIEN,ICDCSYS
 IF COD="" Q ""
 SET COD=$PIECE($PIECE(COD,U),"/")
 SET ICDCSYS=$$SAB^ICDEX(+$$CODECS^ICDEX($GET(COD),80,DT),DT) ;ICR #5747
 SET CODIEN=+$$ICDDATA^ICDXCODE(ICDCSYS,$GET(COD),DT,"E") ;ICR #5699
 QUIT CODIEN
 ;
CPTREC(COD) ;
 IF COD="" Q ""
 QUIT $$CODEN^ICPTCOD(COD) ;ICR #1995
 ;
EDLOAD(RETURN,DA) ; LOAD EDIT ARRAYS
 ; DA=problem IFN
 NEW I,GMPFLD,GMPORIG,GMPL
 DO GETFLDS^GMPLEDT3(DA)
 SET I=0
 DO LOADFLDS(.RETURN,"GMPFLD","NEW",.I)
 DO LOADFLDS(.RETURN,"GMPORIG","ORG",.I)
 KILL GMPFLD,GMPORIG,GMPL  ; should not have to do this
 Q
 ;
LOADFLDS(RETURN,NAM,TYP,I) ; LOAD FIELDS FOR TYPE OF ARRAY
 NEW S,V,CVP,PN,PID
 SET S="",V=$C(254)
 FOR  S S=$ORDER(@NAM@(S)) Q:S=10  D
 . S RETURN(I)=TYP_V_S_V_@NAM@(S)
 . S I=I+1
 SET S=""
 FOR  S S=$ORDER(@NAM@(10,S)) Q:S=""  D
 . S CVP=@NAM@(10,S)
 . S PN="" ; provider name
 . S PID=$PIECE(CVP,U,6) ; provider id
 . I PID'=""  S PN=$$GET1^DIQ(200,PID,.01) ; get provider name
 . S RETURN(I)=TYP_V_"10,"_S_V_CVP_U_PN
 . S I=I+1
 SET S=80000
 FOR  S S=$ORDER(@NAM@(S)) Q:S=""  D
 . S RETURN(I)=TYP_V_S_V_@NAM@(S)
 . S I=I+1
 Q
 ;
EDSAVE(RETURN,GMPIFN,GMPROV,GMPVAMC,UT,EDARRAY,GMPSRCH) ; SAVE EDITED RES
 ; RETURN - boolean, 1 success, 0 failure
 ; EDARRAY - array used for indirect sets of GMPORIG() and GMPFLDS()
 ;
 NEW GMPFLD,GMPORIG,S,GMPLUSER
 NEW VSRQFLG ; lab OR*3.0*479 added new variable
 SET VSRQFLG=0
 SET GMPSRCH=$GET(GMPSRCH)
 SET RETURN=1 ; initialize for success
 IF UT S GMPLUSER=1
 ;
 SET S=""
 FOR  S S=$ORDER(EDARRAY(S)) Q:S=""  D
 . ;S @EDARRAY(S) D lab OR*3.0*479 commented out EDDARRAY and added new logic below
 . ; lab OR*3.0*479 Adding data checks to prevent backdoor access into VistA
 . ; lab - start new logic OR*3.0*479
 . I ($EXTRACT(EDARRAY(S),1,6)="GMPFLD")!($EXTRACT(EDARRAY(S),1,7)="GMPORIG") D
 . . I $EXTRACT(EDARRAY(S),$FIND(EDARRAY(S),"="))="""" D
 . . . S @EDARRAY(S)
 . . ELSE  D
 . . . S RETURN=0
 . . . S VSRQFLG=1
 . ELSE  D
 . . S RETURN=0
 . . S VSRQFLG=1
 ;
 Q:(VSRQFLG)  ;quit if flag has been set meaning an unexpected value was sent in the parameter.
 ; lab - end new logic OR*3.0*479
 IF $DATA(GMPFLD(10,"NEW"))>9 D  I 'RETURN Q  ; Bail Out if no lock
 . L +^AUPNPROB(GMPIFN,11):10 ; given bogus nature of this lock, should be able to get
 . I '$T S RETURN=0
 ;
 DO EN^GMPLSAVE ; save the data
 KILL GMPFLD,GMPORIG
 ;
 LOCK -^AUPNPROB(GMPIFN,11) ; free this instance of lock (in case it was set)
 SET RETURN=1
 Q
 ;
UPDATE(ORRETURN,UPDARRAY) ; UPDATE A PROBLEM RECORD
 ; Does essentially same job as EDSAVE above, however does not handle edits to comments
 ; or addition of multiple comments.
 ; Use initially just for status updates.
 ;
 NEW S,GMPL,GMPORIG,ORARRAY ; last 2 vars created in nested call
 NEW VSRQFLG ; lab OR*3.0*479 added new variable
 SET VSRQFLG=0
 SET S=""
 FOR  S S=$ORDER(UPDARRAY(S)) Q:S=""  D
 . ;S @UPDARRAY(S) lab OR*3.0*479 commented out UPDARRAY and added new logic below
 . ; lab OR*3.0*479 Adding data checks to prevent backdoor access into VistA
 . ; lab - start new logic OR*3.0*479
 . I ($EXTRACT(UPDARRAY(S),1,7)="ORARRAY") D
 . . I $EXTRACT(UPDARRAY(S),$FIND(UPDARRAY(S),"="))="""" D
 . . . S @UPDARRAY(S)
 . . ELSE  D
 . . . S ORRETURN(0)=0
 . . . S ORRETURN(1)="Unexpected array value."
 . . . S VSRQFLG=1
 . ELSE  D
 . . S ORRETURN(0)=0
 . . S ORRETURN(1)="Unexpected array value."
 . . S VSRQFLG=1
 ;
 Q:(VSRQFLG)  ;quit if flag has been set meaning an unexpected value was sent in the parameter.
 ; lab - end new logic OR*3.0*479
 DO UPDATE^GMPLUTL(.ORARRAY,.ORRETURN)
 ; broker wont pick up root node RETURN
 SET ORRETURN(1)=ORRETURN(0) ; error text
 SET ORRETURN(0)=ORRETURN ; gmpdfn
 IF ORRETURN(0)=""  S ORRETURN=1 ; insurance ? need
 Q
 ;
ADDSAVE(RETURN,GMPDFN,GMPROV,GMPVAMC,ADDARRAY,GMPSRCH) ; SAVE NEW RECORD
 ; RETURN - Problem IFN if success, 0 otherwise
 ; ADDARRAY - array used for indirect sets of GMPFLDS()
 ;
 NEW DA,GMPFLD,GMPORIG,S
 NEW VSRQFLG ; lab OR*3.0*479 added new variable
 SET VSRQFLG=0
 SET GMPSRCH=$GET(GMPSRCH)
 SET RETURN=0 ;
 LOCK +^AUPNPROB(0):10
 Q:'$T  ; bail out if no lock
 ;
 SET S=""
 FOR  S S=$ORDER(ADDARRAY(S)) Q:S=""  D
 . ; lab - S @ADDARRAY(S) OR*3.0*479 commented out ADDARRAY and added new logic below
 . ; lab - for VSR project, adding data checks to prevent backdoor access into VistA
 . ; lab - start new logic
 . I $EXTRACT(ADDARRAY(S),1,6)="GMPFLD" D
 . . I $EXTRACT(ADDARRAY(S),$FIND(ADDARRAY(S),"="))="""" D
 . . . S @ADDARRAY(S)
 . . ELSE  D 
 . . . S RETURN=0
 . . . L -^AUPNPROB(0)
 . . . S VSRQFLG=1
 . ELSE  D 
 . . S RETURN=0
 . . L -^AUPNPROB(0)
 . . S VSRQFLG=1
 ;
 Q:(VSRQFLG)  ;quit if flag has been set meaning an unexpected value was sent in the parameter.
 ; lab - end new logic OR*3.0*479
 ;
 DO NEW^GMPLSAVE
 ;
 SET RETURN=DA
 ;
 LOCK -^AUPNPROB(0)
 SET RETURN=1
 Q
 ;
INITUSER(RETURN,ORDUZ) ; INITIALIZE FOR NEW USER
 ; taken from INIT^GMPLMGR
 ; leave GMPLUSER on symbol table - is evaluated in EDITSAVE
 ;
 NEW X,PV,CTXT,GMPLPROV,ORENT
 SET ORDUZ=$GET(ORDUZ,DUZ)
 SET GMPLUSER=$$CLINUSER(ORDUZ)
 SET CTXT=$$GET^XPAR("ALL","ORCH CONTEXT PROBLEMS",1)
 SET X=$GET(^GMPL(125.99,1,0)) ; IN1+6^GMPLMGR
 SET RETURN(0)=GMPLUSER ; problem list user, or other user
 SET RETURN(1)=$$VIEW^GMPLX1(ORDUZ) ; GMPLVIEW("VIEW") - users default view
 SET RETURN(2)=+$PIECE(X,U,2) ; verify transcribed problems
 SET RETURN(3)=+$PIECE(X,U,3) ; prompt for chart copy
 SET RETURN(4)=+$PIECE(X,U,4) ; use lexicon
 SET RETURN(5)=$S($PIECE(X,U,5)="R":1,1:0) ; chron or reverse chron listing
 SET RETURN(6)=$S($PIECE($GET(CTXT),";",3)'="":$PIECE($GET(CTXT),";",3),1:"A")
 SET GMPLPROV=$PIECE($GET(CTXT),";",5)
 IF +GMPLPROV>0,$DATA(^VA(200,GMPLPROV)) D
 . S RETURN(7)=GMPLPROV_U_$PIECE(^VA(200,GMPLPROV,0),U)
 ELSE  S RETURN(7)="0^All"
 SET RETURN(8)=$$SERVICE^GMPLX1(ORDUZ) ; user's service/section
 ; Guessing from what I see in the data that $$VIEW^GMPLX1 actually returns a composite
 ; of default view (in/out patient)/(c1/c2... if out patient i.e. GMPLVIEW("CLIN")) or
 ; /(s1/s2... if in patient i.e. GMPLVIEW("SERV"))
 ; Going with this assumption for now:
 IF $LENGTH(RETURN(1),"/")>1 D
 . S PV=RETURN(1)
 . S RETURN(1)=$PIECE(PV,"/")
 . I RETURN(1)="C" S GMPLVIEW("CLIN")=$PIECE(PV,"/",2,99)
 . I RETURN(1)="S" S GMPLVIEW("SERV")=$PIECE(PV,"/",2,99)
 SET RETURN(9)=$GET(GMPLVIEW("SERV")) ; ??? Where from - see tech doc
 SET RETURN(10)=$GET(GMPLVIEW("CLIN")) ; ??? Where from - see tech doc
 SET RETURN(11)=""
 SET RETURN(12)=+$PIECE($GET(CTXT),";",4) ; should comments display?
 SET ORENT="ALL^SRV.`"_+$$SERVICE^GMPLX1(ORDUZ,1)
 SET RETURN(13)=+$$GET^XPAR(ORENT,"ORQQPL SUPPRESS CODES",1) ; suppress codes?
 KILL GMPLVIEW
 Q
 ;
CLINUSER(ORDUZ) ;is this a clinical user?
 NEW ORUSER
 SET ORUSER=0
 IF $DATA(^XUSEC("ORES",ORDUZ)) S ORUSER=1
 IF $DATA(^XUSEC("ORELSE",ORDUZ)) S ORUSER=1
 IF $DATA(^XUSEC("PROVIDER",ORDUZ)) S ORUSER=1
 QUIT ORUSER
 ;
INITPT(RETURN,DFN) ; GET PATIENT PARAMETERS
 Q:+$GET(DFN)=0
 NEW GMPSC,GMPAGTOR,GMPION,GMPGULF,GMPHNC,GMPMST,GMPCV,GMPSHD
 ;
 SET RETURN(0)=DUZ(2) ; facility #
 DO DEM^VADPT ; get death indicator
 SET RETURN(1)=$GET(VADM(6)) ; death indicator
 DO VADPT^GMPLX1(DFN) ; get eligibilities
 SET RETURN(2)=$PIECE(GMPSC,U) ; service connected
 SET RETURN(3)=$GET(GMPAGTOR) ; agent orange exposure
 SET RETURN(4)=$GET(GMPION) ; ionizing radiation exposure
 SET RETURN(5)=$GET(GMPGULF) ; gulf war exposure
 SET RETURN(6)=VA("BID") ; need this to reconstitute GMPDFN on return
 SET RETURN(7)=$GET(GMPHNC) ; head/neck cancer
 SET RETURN(8)=$GET(GMPMST) ; MST
 SET RETURN(9)=$GET(GMPCV) ; CV
 SET RETURN(10)=$GET(GMPSHD) ; SHAD
 Q
 ;
PROVSRCH(LST,FLAG,N,FROM,PART) ; Get candidate Rroviders from person file
 NEW LV,NS,RV,IEN
 SET RV=$NAME(LV("DILIST","ID"))
 IF +$GET(N)=0 S N=50
 SET FLAG=$GET(FLAG),N=$GET(N),FROM=$GET(FROM),PART=$GET(PART)
 DO LIST^DIC(200,"",".01;1",FLAG,N,FROM,PART,"","","","LV")
 SET NS=""
 FOR  S NS=$ORDER(LV("DILIST",1,NS)) Q:NS=""  D
 . S IEN=""
 . S IEN=$ORDER(^VA(200,"B",@RV@(NS,.01),IEN)) ; compliments of PROV^ORQPTQ
 . S LST(NS)=IEN_U_@RV@(NS,.01) ; initials_U_@RV@(NS,1)
 Q
 ;
CLINSRCH(Y,X) ; Get LIST OF CLINICS
 ; Note: This comes from CLIN^ORQPTQ2, where it was commented out in place of
 ; a call to ^XPAR. I would have just used CLIN^ORQPTQ2, but it didn't work - at
 ; least on SLC OEX directory.
 ; X has no purpose other than to satisfy apparent rpc and tcallv requirement for args
 NEW I,NAME,IEN
 SET I=1,IEN=0,NAME=""
 ;access to SC global granted under DBIA #518:
 FOR  S NAME=$ORDER(^SC("B",NAME)) Q:NAME=""  S IEN=$ORDER(^(NAME,0)) D
 . I $PIECE(^SC(IEN,0),"^",3)="C" S Y(I)=IEN_"^"_NAME,I=I+1
 Q
 ;
SRVCSRCH(Y,FROM,DIR,ALL) ; GET LIST OF SERVICES
 NEW I,IEN,CNT S I=0,CNT=44
 FOR  Q:I=CNT  S FROM=$ORDER(^DIC(49,"B",FROM),DIR) Q:FROM=""  D
 . S IEN=$ORDER(^DIC(49,"B",FROM,0)) I '$GET(ALL),$PIECE(^DIC(49,IEN,0),U,9)'="C" Q
 . S I=I+1,Y(I)=IEN_"^"_FROM
 Q
 ;
DUP(Y,DFN,TERM,TEXT) ;Check for duplicate problem
 SET Y=$$DUPL^GMPLX(DFN,TERM,TEXT) Q:+Y=0
 IF $PIECE(^AUPNPROB(Y,1),U,2)="H" S Y=0 Q
 SET Y=Y_U_$PIECE(^AUPNPROB(Y,0),U,12)
 Q
GETDX(CODE,SYS,ORIDT) ; Get ICD associated with SNOMED CT or VHAT Code
 NEW LEX,ORI,ORY,ORUH,IMPLDT,ORCSYSPR
 SET ORIDT=$GET(ORIDT,DT)
 SET ORY=0,IMPLDT=$$IMPDATE^LEXU("10D")
 SET ORUH=$S(ORIDT<IMPLDT:"799.9",1:"R69.")
 SET ORCSYSPR=$S(ORIDT<IMPLDT:1,1:30)
 IF SYS["VHAT" D  I 1
 . I ORIDT<IMPLDT S ORY=$$GETASSN^LEXTRAN1(CODE,"VHAT2ICD") I 1
 . E  S ORY=0
 ELSE  D
 . I ORIDT<IMPLDT S ORY=$$GETASSN^LEXTRAN1(CODE,"SCT2ICD") I 1
 . E  S ORY=0
 IF $S(+ORY'>0:1,+$PIECE(ORY,U,2)'>0:1,+LEX'>0:1,1:0) S ORY=ORUH G GETDXX
 SET ORI=0,ORY=""
 FOR  S ORI=$ORDER(LEX(ORI)) Q:+ORI'>0  D
 . N ICD
 . S ICD=$ORDER(LEX(ORI,""))
 . S:'+$$STATCHK^ICDXCODE(ORCSYSPR,ICD,ORIDT) ICD=""
 . I ICD]"" S ORY=$S(ORY'="":ORY_"/",1:"")_ICD
 IF (ORY]""),(ORY'[".") S ORY=ORY_"."
GETDXX Q ORY
TEST ; test invocation
 NEW LIST,I S I=""
 DO LEXSRCH(.LIST,"diabetes with neuro",10,"GMPL",DT)
 FOR  S I=$ORDER(LIST(I)) Q:+I'>0  W !,LIST(I)
 Q
