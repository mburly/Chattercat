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
    $db = "cc_" . $_POST["channel"];
    $conn = new mysqli($host, $user, $password, $db); 
    $emotes = array();
    $types = array();
    $paths = array();
    $dates= array();
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = "SELECT e.Code AS emote, e.Path AS path, l.Old AS old, l.New AS new, l.Timestamp AS timestamp FROM Logs l INNER JOIN Emotes e ON l.EmoteID=e.EmoteID AND l.Source=e.Source ORDER BY l.LogID DESC LIMIT 5;";
        $result = $conn->query($sql);
        if($result->num_rows > 0) {
            while($log = $result -> fetch_assoc()) {
                array_push($emotes, $log["emote"]);
                array_push($dates, $log["timestamp"]);
                array_push ($paths, 'e' . ltrim($log["path"], "chattercat-front/"));
                if($log["old"] == 1 && $log["new"] == 0) {
                    array_push($types, "disabled");
                }
                elseif($log["old"] == NULL && $log["new"] == 1) {
                    array_push($types, "enabled");
                }
                else {
                    array_push($types, "reactivated");
                }
            }
            returnInfo($dates, $types, $paths, $emotes);
        }
        else {
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
        $retVal = '{"results":' . $items . ',"error":""}';
        sendResultInfoAsJson($retVal);
    }
    
    function returnInfo($dates, $types, $paths, $emotes)
    {
        $retVal = '{';
        for($i = 0, $size = count($dates); $i < $size; ++$i) {
            $retVal .= '"log-' . $i . '": { "datetime":"' . $dates[$i] . '","type":"' . $types[$i] . '","path":"' . $paths[$i] . '","emote":"' . $emotes[$i] . '"},';   
        }
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>