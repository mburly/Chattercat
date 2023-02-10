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

    $db = "cc_" . $in["channel"];

    $conn = new mysqli($host, $user, $password, $db); 

    $emotes = array();
    $types = array();
    $paths = array();
    $dates= array();

    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = "SELECT e.code AS emote, e.path AS path, l.old AS old, l.new AS new, l.datetime AS datetime FROM logs l INNER JOIN emotes e ON l.emote_id=e.id ORDER BY l.id DESC LIMIT 5;";
        $result = $conn->query($sql);
        if($result->num_rows > 0) {
            while($log = $result -> fetch_assoc()) {
                array_push($emotes, $log["emote"]);
                array_push($dates, $log["datetime"]);
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