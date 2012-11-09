\ simple expression parser and calculator
\
\ expression: ['+'|'-'] term ['+'|'-' term]*
\ term:       factor ['*'|'/' factor]*
\ factor:     '(' expression ')' | number
\ number:     digit [digit]*
\
\ originally from: http://blog.brush.co.nz/2007/11/recursive-decent/

variable _c

: c _c @ ;

: next  ( -- )
  key _c !  c emit ;

: digit?  ( c -- )
  [char] 0 - 10 u< ;

: number  ( -- n )
  c digit? 0= abort" digit expected"
  0  begin
    10 *  c [char] 0 -  +  next
    c digit? 0=
  until ;

: factor  ( -- n )
  c [char] ( = if
    next  expression  c [char] ) <> abort" ) expected"  next
  else
    number
  then ;

: term  ( -- n )
  factor
  begin
    c [char] * = dup  c [char] / =  or
  while
    next  factor  swap if  *  else  /  then
  repeat  drop ;

: expression  ( -- n )
  c [char] - = dup  c [char] + = or  if  next  then
  term  swap if  negate  then
  begin
    c [char] + = dup  c [char] - =  or
  while
    next  term  swap if  +  else  -  then
  repeat  drop ;

: calc  ( -- )
  next  expression  cr . ;

calc
