HelloWorld
    WRITE "Hello from the world of MUMPS!", 13, 10
    QUIT

GlobalTest
    SET ^MyData("Name")="Cline"
    SET ^MyData("Role")="Software Engineer"
    WRITE "Stored Name: ", ^MyData("Name"), 13, 10
    WRITE "Stored Role: ", ^MyData("Role"), 13, 10
    QUIT