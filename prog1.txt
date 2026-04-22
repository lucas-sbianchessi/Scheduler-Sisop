.code
  load a
  add #1
  sub #2
  syscall 1 # print 9
  store a
  syscall 0
.endcode

.data
  a 10
.enddata
