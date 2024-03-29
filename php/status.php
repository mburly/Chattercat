<?php
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
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = 'SELECT End FROM Executions ORDER BY ExecutionID DESC LIMIT 1';
        $result = $conn->query($sql);
        $end = $result->fetch_assoc()["End"];
        if($end == null) {
            returnInfo("online");
        }
        else {
            returnInfo("offline");
        }
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
        $retVal = '{"results":[' . $items . '],"error":""}';
        sendResultInfoAsJson($retVal);
    }
    
    function returnInfo($status)
    {
        $retVal = '{"status":"' . $status . '",';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>