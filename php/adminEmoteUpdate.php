<?php
    set_time_limit(0);
    ignore_user_abort(1);
    ob_start();
    $in = getRequestInfo();
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

    $db = 'cc_' . $in["channel"];
    $source = $in["source"];
    $emote_id = $in["emote_id"];
    $col = $in["type"];
    $new_value = $in["new_value"];

    $conn = new mysqli($host, $user, $password, $db); 
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        if($col == "count" || $col == "source" || $col == "active") {
            $sql = 'UPDATE emotes SET ' . $col . ' = ' . $new_value . ' WHERE emote_id = "' . $emote_id . '" AND source = ' . $source . ';';
        }
        else {
            $sql = 'UPDATE emotes SET ' . $col . ' = "' . $new_value . '" WHERE emote_id = "' . $emote_id . '" AND source = ' . $source . ';';            
        }
        $conn->query($sql);
        returnInfo();
    }

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
    
    
    function returnInfo()
    {
        $retVal = '{';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>