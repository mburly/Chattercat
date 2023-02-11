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
    $db = 'cc_' . $_POST["channel"];
    $source = $_POST["source"];
    $emote_id = $_POST["emote_id"];
    echo $db;
    echo $source;
    echo $emote_id;
    $conn = new mysqli($host, $user, $password, $db); 
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = 'DELETE FROM emotes WHERE source = ' . $source . ' AND emote_id ="' . $emote_id . '";';
        $conn->query($sql);
        returnInfo();
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