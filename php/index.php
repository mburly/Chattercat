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
                $channelNames .=  '"' . substr($db["Database"], strpos($db["Database"], '_') + 1) . '", ';
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
                $sql = "SELECT Start, End FROM Sessions ORDER BY SessionID DESC LIMIT 1;";
                $result = $conn->query($sql)->fetch_assoc();
                if($result == NULL)
                {
                    continue;
                }
                if($result["End"] == NULL)
                {
                    $live .=  'true, ';
                    array_push($liveTimes, $result["Start"]);
                    $sql = "SELECT Title FROM Segments ORDER BY SegmentID DESC LIMIT 1;";
                    $result = $conn->query($sql)->fetch_assoc();
                    array_push($liveChannels, substr($channel, strpos($channel, '_') + 1));
                    array_push($liveTitles, addcslashes($result["Title"], '"\\/'));
                    $sql = "SELECT COUNT(MessageID) AS num_messages, COUNT(DISTINCT ChatterID) as num_chatters FROM Messages WHERE SessionID = (SELECT MAX(SessionID) FROM Sessions);";
                    $result = $conn->query($sql)->fetch_assoc();
                    array_push($liveMessageCounts, $result["num_messages"]);
                    array_push($liveNumChatters, $result["num_chatters"]);
                    $sql = "SELECT Name FROM Games WHERE GameID = (SELECT GameID FROM Segments ORDER BY SegmentID DESC LIMIT 1);";
                    $result = $conn->query($sql)->fetch_assoc();
                    array_push($liveGames, addcslashes($result["Name"], '"\\/'));
                    $sql = "SELECT COUNT(ChatterID) AS new_chatters FROM Chatters WHERE ChatterID IN (SELECT ChatterID FROM Messages WHERE SessionID = (SELECT MAX(SessionID) FROM Sessions)) AND FirstSeen = UTC_DATE();";
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