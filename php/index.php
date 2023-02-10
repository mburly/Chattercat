<?php
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
    $conn = new mysqli($host, $user, $password);
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = "SHOW DATABASES;";
        $result = $conn->query($sql);
        $channels = array();
        $channelNames = '';
        while($db = $result -> fetch_assoc()) {
            if(strpos($db["Database"], "cc_") !== false && strpos($db["Database"], "housekeeping") == false)
            {
                array_push($channels, $db["Database"]);
                $channelNames .=  '"' . ltrim($db["Database"], "cc_") . '", ';
            }
        }
        $channelNames = substr($channelNames, 0, -2);

        $live = '';
        $liveChannels = array();
        $liveGames = array();
        $liveTimes = array();
        $liveTitles = array();
        $liveMessageCounts = array();
        $liveNumChatters = array();
        $liveNewChatters = array();

        foreach ($channels as &$channel)
        {
            $conn = new mysqli($host, $user, $password, $channel);
            if($conn->connect_error) {
                returnWithError($conn->connect_error);
            }
            else {
                $sql = "SELECT start_datetime, end_datetime FROM sessions ORDER BY ID DESC LIMIT 1;";
                $result = $conn->query($sql)->fetch_assoc();
                if($result == NULL)
                {
                    continue;
                }
                if($result["end_datetime"] == NULL)
                {
                    $live .=  'true, ';
                    array_push($liveTimes, $result["start_datetime"]);
                    $sql = "SELECT stream_title FROM segments ORDER BY ID DESC LIMIT 1;";
                    $result = $conn->query($sql)->fetch_assoc();
                    array_push($liveChannels, ltrim($channel, "cc_"));
                    array_push($liveTitles, addcslashes($result["stream_title"], '"\\/'));
                    $sql = "SELECT COUNT(id) AS num_messages, COUNT(DISTINCT chatter_id) as num_chatters FROM messages WHERE session_id = (SELECT MAX(id) FROM sessions);";
                    $result = $conn->query($sql)->fetch_assoc();
                    array_push($liveMessageCounts, $result["num_messages"]);
                    array_push($liveNumChatters, $result["num_chatters"]);
                    $sql = "SELECT name FROM games WHERE id = (SELECT game_id FROM segments ORDER BY id DESC LIMIT 1);";
                    $result = $conn->query($sql)->fetch_assoc();
                    array_push($liveGames, addcslashes($result["name"], '"\\/'));
                    $sql = "SELECT COUNT(id) AS new_chatters FROM chatters WHERE id IN (SELECT chatter_id FROM messages WHERE session_id = (SELECT MAX(id) FROM sessions)) AND first_date = UTC_DATE();";
                    $result = $conn->query($sql)->fetch_assoc();
                    array_push($liveNewChatters, $result["new_chatters"]);
                }
                else
                {
                    $live .= 'false, ';
                }
            }
        }
        $live = substr($live, 0, -2);

        returnInfo($channelNames, $live, $liveChannels, $liveGames, $liveTimes, $liveTitles, $liveMessageCounts, $liveNumChatters, $liveNewChatters);
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
        $retVal = '{"results":[' . $items . '],"error":""}';
        sendResultInfoAsJson($retVal);
    }
    
    function returnInfo($channels, $live, $liveChannels, $liveGames, $liveTimes, $liveTitles, $liveMessageCounts, $liveNumChatters, $liveNewChatters)
    {
        $retVal = '{"channels":[' . $channels . '],"live":[' . $live . '],';
        for($i = 0, $size = count($liveChannels); $i < $size; ++$i) {
            $retVal .= '"' . $liveChannels[$i] . '": { "title":"' . $liveTitles[$i] . '","category":"' . $liveGames[$i] . '","streamStartDate":"' . $liveTimes[$i] . '","newChatters":' . $liveNewChatters[$i] . ',"numMessages":' . $liveMessageCounts[$i] . ',"numChatters":' . $liveNumChatters[$i]. '},';   
        }
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>