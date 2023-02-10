<?php
    ob_start();
    $in = getRequestInfo();
    $streamsFile = fopen("../streams.txt", "r") or die("Unable to open file!");
    $streams = array();
    while(!feof($streamsFile)) {
        $line = fgets($streamsFile);
        if($line != "") {
            array_push($streams, str_replace(array("\r", "\n"), '', $line));
        }
    }
    fclose($streamsFile);

    $host = '';
    $user = '';
    $password = '';

    $configFile = fopen("../conf.ini", "r") or die("Unable to open file!");
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
    $channels = array();
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = 'SHOW DATABASES;';
        $result = $conn->query($sql);
        while($row = $result->fetch_assoc()) {
            $dbname = $row["Database"];
            if(strpos($dbname, "cc_") !== false) {
                array_push($channels, explode("cc_", $dbname)[1]);
            }
        }
    }

    returnInfo($streams, $channels);

    function getRequestInfo()
    {
        return json_decode(file_get_contents('php://input'), true);
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
    
    function returnInfo($streams, $channels)
    {
        $retVal = '{"streams":[';
        foreach($streams as $stream) {
            $retVal .= '"' . $stream . '",';
        }
        $retVal = substr($retVal, 0, -1);
        $retVal .= '],"channels":[';
        foreach($channels as $channel) {
            $retVal .= '"' . $channel . '",';
        }
        $retVal = substr($retVal, 0, -1);
        $retVal .= '],';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>