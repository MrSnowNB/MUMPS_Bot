;;DEPRECATED — moved from repo root 2026-04-09
;; This file used globals (^MyData) and is not a valid pipeline fixture.
;; Use routines/hello_message.m as the official smoke-test routine.
;; See SMOKE-T01.yaml for the frozen fixture definition.
HelloWorld
    WRITE "Hello from the world of MUMPS!", 13, 10
    QUIT

GlobalTest
    SET ^MyData("Name")="Cline"
    SET ^MyData("Role")="Software Engineer"
    WRITE "Stored Name: ", ^MyData("Name"), 13, 10
    WRITE "Stored Role: ", ^MyData("Role"), 13, 10
    QUIT
