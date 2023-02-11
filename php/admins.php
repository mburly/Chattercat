<?php
    set_time_limit(0);
    ignore_user_abort(1);
    ob_start();
    $configFile = fopen("../conf.ini", "r") or die("Unable to open file!");
    $host = '';
    $user = '';
    $password = '';
    while(!feof($configFile)) {
        $line = fgets($configFile);
        if(strpos($line, "host =") !== false)
        {
            $host .= rtrim(explode("= ", $line)[1], "\r\n");
        }
        else if(strpos($line, "user =") !== false)
        {
            $user .= rtrim(explode("= ", $line)[1], "\r\n");
        }
        else if(strpos($line, "password =") !== false)
        {
            $password .= rtrim(explode("= ", $line)[1], "\r\n");
        }
    }
    fclose($configFile);
    $conn = new mysqli($host, $user, $password, "cc_housekeeping");
    $usernames = '';
    $roles = '';
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = "SELECT username, role FROM admins;";
        $result = $conn->query($sql);
        while($admin = $result->fetch_assoc()) {
            $usernames .= '"' . $admin["username"] . '",';
            $roles .=  $admin["role"] . ',';
        }
        $usernames = substr($usernames, 0, -1);
        $roles = substr($roles, 0, -1);
        returnInfo($usernames, $roles);
    }

    function sendResultInfoAsJson( $obj )
    {
        header('Content-Type: text/html');
        echo $obj;
    }

    function returnWithError( $err )
    {
        $retValue = '{"id":0,"error":"' . $err . '"}';
        sendResultInfoAsJson( $retValue );
    }
    
    function returnWithInfo($items)
    {
        $retVal = '{"results":' . $items . ',"error":""}';
        sendResultInfoAsJson($retVal);
    }
    
    function returnInfo($usernames, $roles)
    {
        $retVal = '{"usernames":[' . $usernames . '],"roles":[' . $roles;
        $retVal .= '],"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>