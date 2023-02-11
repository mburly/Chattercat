<?php
    ob_start();
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
    $pictures = array();
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = 'SHOW DATABASES;';
        $result = $conn->query($sql);
        while($row = $result->fetch_assoc()) {
            $dbname = $row["Database"];
            if(strpos($dbname, "cc_") !== false) {
                if($dbname == "cc_housekeeping") {
                    continue;
                }
                array_push($channels, explode("cc_", $dbname)[1]);
                $sql = 'SELECT url FROM pictures WHERE channel = "' . explode("cc_", $dbname)[1] . '" ORDER BY id DESC LIMIT 1;';
                $conn2 = new mysqli($host, $user, $password, "cc_housekeeping");
                $url = $conn2->query($sql)->fetch_assoc()["url"];
                if($url !== null) {
                    array_push($pictures, $url);
                }
                else {
                }
                $conn2->close();
            }
        }
        returnInfo($channels, $pictures);
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
    
    function returnInfo($channels, $pictures)
    {
        $retVal = '{"channels":[';
        foreach($channels as $channel) {
            $retVal .= '"' . $channel . '",';
        }
        $retVal = substr($retVal, 0, -1);
        $retVal .= '],"pictures":[';
        foreach($pictures as $picture) {
            $retVal .= '"' . $picture . '",';
        }
        $retVal = substr($retVal, 0, -1);
        $retVal .= '],';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>