<?php
    ob_start();
    $db_name = "cc_" . $_POST["channel"];
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
    $conn = new mysqli($host, $user, $password, $db_name);
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = "SELECT code, count, path, source FROM emotes GROUP BY code ORDER BY count DESC LIMIT 10;";
        $result = $conn->query($sql);
        $topEmoteCodes = '';
        $topEmoteCounts = '';
        $topEmotePaths = '';
        $topEmoteSources = '';
        while($emote = $result -> fetch_assoc()) {
            $topEmoteCodes .=  '"' . addcslashes($emote["code"], '"\\/'). '", ';
            $topEmoteCounts .=  '' . $emote["count"] . ', ';
            $topEmotePaths .= '"' . $emote["path"] . '", ';
            $topEmoteSources .= '' . $emote["source"] . ', ';
        }
        $topEmoteCodes = substr($topEmoteCodes, 0, -2);
        $topEmoteCounts = substr($topEmoteCounts, 0, -2);
        $topEmotePaths = substr($topEmotePaths, 0, -2);
        $topEmoteSources = substr($topEmoteSources, 0, -2);

        $sql = "SELECT COUNT(id) AS num_emotes FROM emotes;";
        $result = $conn->query($sql);
        $numEmotes = $result->fetch_assoc()["num_emotes"];

        $sql = "SELECT (SELECT username FROM chatters WHERE id = chatter_id) AS username, COUNT(id) AS message_count FROM messages GROUP BY chatter_id ORDER BY COUNT(id) DESC LIMIT 5;";
        $result = $conn->query($sql);
        $topChatterNames = '';
        $topChatterCounts = '';
        while($top_chatter = $result -> fetch_assoc()) {
            $topChatterNames .=  '"' . $top_chatter["username"] . '", ';
            $topChatterCounts .= '' . $top_chatter["message_count"] . ', ';
        }
        $topChatterNames = substr($topChatterNames, 0, -2);
        $topChatterCounts = substr($topChatterCounts, 0, -2);

        $sql = "SELECT COUNT(id) AS num_chatters FROM chatters;";
        $result = $conn->query($sql);
        $numChatters = $result->fetch_assoc()["num_chatters"];

        $sql = "SELECT DISTINCT (SELECT username FROM chatters WHERE id = chatter_id) AS username FROM messages GROUP BY id ORDER BY id DESC LIMIT 9;";
        $result = $conn->query($sql);
        $recentChatterNames = '';
        while($recent_chatter = $result -> fetch_assoc()) {
            $recentChatterNames .=  '"' . $recent_chatter["username"] . '", ';
        }
        $recentChatterNames = substr($recentChatterNames, 0, -2);

        $sql = "SELECT COUNT(id) AS recent_session_count FROM messages WHERE session_id = (SELECT MAX(id) FROM sessions);";
        $result = $conn->query($sql);
        $recentSessionMessageCount = $result->fetch_assoc()["recent_session_count"];

        $sql = "SELECT COUNT(id) AS num_messages FROM messages;";
        $result = $conn->query($sql);
        $numMessages = $result->fetch_assoc()["num_messages"];

        $sql = "SELECT (SELECT username FROM chatters WHERE id = chatter_id) AS username, message, datetime FROM messages ORDER BY id DESC LIMIT 20;";
        $result = $conn->query($sql);
        $recentMessageNames = '';
        $recentMessageMessages = '';
        $recentMessageDatetimes = '';
        while($recent_chat = $result -> fetch_assoc()) {
            $recentMessageNames .=  '"' . $recent_chat["username"] . '", ';
            $recentMessageMessages .=  '"' . addcslashes(removeUnicode($recent_chat["message"]), '"\\/') . '", ';
            $recentMessageDatetimes .=  '"' . $recent_chat["datetime"] . '", ';
        }
        $recentMessageNames = substr($recentMessageNames, 0, -2);
        $recentMessageMessages = substr($recentMessageMessages, 0, -2);
        $recentMessageDatetimes = substr($recentMessageDatetimes, 0, -2);

        $sql = "SELECT start_datetime, length FROM sessions ORDER BY id DESC LIMIT 5;";
        $result = $conn->query($sql);
        $recentSessionStartDatetimes = '';
        $recentSessionLengths = '';
        while($recentSession = $result -> fetch_assoc()) {
            if($recentSession["length"] == null)
            {
                $length = "null";
            }
            else
            {
                $length = $recentSession["length"];
            }
            $recentSessionStartDatetimes .=  '"' . $recentSession["start_datetime"] . '", ';
            $recentSessionLengths .=  '"' . $length . '", ';
        }
        $recentSessionStartDatetimes = substr($recentSessionStartDatetimes, 0, -2);
        $recentSessionLengths = substr($recentSessionLengths, 0, -2);

        $sql = "SELECT g.name, s.length, s.stream_title, s.session_id FROM games g INNER JOIN segments s ON g.id=s.game_id WHERE s.session_id IN (SELECT * FROM (SELECT id FROM sessions ORDER BY id DESC) AS t) ORDER BY s.id DESC;";
        $result = $conn->query($sql);
        $recentSegmentCategories = '';
        $recentSegmentLengths = '';
        $recentSegmentTitles = '';
        $recentSegmentSessions = '';
        while($recentSegment = $result -> fetch_assoc()) {
            $recentSegmentCategories .=  '"' . $recentSegment["name"] . '", ';
            $recentSegmentLengths .=  '"' . $recentSegment["length"] . '", ';
            $recentSegmentTitles .=  '"' . addcslashes($recentSegment["stream_title"], '"\\/') . '", ';
            $recentSegmentSessions .=  '' . $recentSegment["session_id"] . ', ';
        }
        $recentSegmentCategories = substr($recentSegmentCategories, 0, -2);
        $recentSegmentLengths = substr($recentSegmentLengths, 0, -2);
        $recentSegmentTitles = substr($recentSegmentTitles, 0, -2);
        $recentSegmentSessions = substr($recentSegmentSessions, 0, -2);

        returnInfo($topEmoteCodes, $topEmotePaths, $topEmoteCounts, $topEmoteSources, $numEmotes, $numChatters, $topChatterNames, $topChatterCounts, $recentChatterNames, $recentSessionMessageCount, $numMessages, $recentMessageNames, $recentMessageMessages, $recentMessageDatetimes, $recentSessionStartDatetimes, $recentSessionLengths, $recentSegmentCategories, $recentSegmentLengths, $recentSegmentTitles, $recentSegmentSessions);
    }

    function removeUnicode($string) {
        return preg_replace('/[\x00-\x1F\x7F]/u', '', $string);
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
    
    function returnInfo($topEmoteCodes, $topEmotePaths, $topEmoteCounts, $topEmoteSources, $numEmotes, $numChatters, $topChatterNames, $topChatterCounts, $recentChatterNames, $recentSessionMessageCount, $numMessages, $recentMessageNames, $recentMessageMessages, $recentMessageDatetimes, $recentSessionStartDatetimes, $recentSessionLengths, $recentSegmentCategories, $recentSegmentLengths, $recentSegmentTitles, $recentSegmentSessions)
    {
        $retVal = '{"topChatterNames":[' . $topChatterNames . '],"topChatterCounts":[' . $topChatterCounts . '],"recentChatterNames":[' . $recentChatterNames . '],"recentMessageNames":[' . $recentMessageNames . '],"recentMessageMessages":[' . $recentMessageMessages . '],"recentMessageDatetimes":[' . $recentMessageDatetimes . '],"recentSessionStartDatetimes":[' . $recentSessionStartDatetimes . '],"recentSessionLengths":[' . $recentSessionLengths . '],"recentSegmentCategories":[' . $recentSegmentCategories . '],"recentSegmentLengths":[' . $recentSegmentLengths . '],"recentSegmentTitles":[' . $recentSegmentTitles . '],"recentSegmentSessions":[' . $recentSegmentSessions . '],"topEmoteCodes":[' . $topEmoteCodes . '],"topEmoteCounts":[' . $topEmoteCounts . '],"topEmotePaths":[' . $topEmotePaths . '],"topEmoteSources":[' . $topEmoteSources . '],"totalChatters":' . $numChatters . ',"totalMessages":' . $numMessages . ',"recentSessionMessages":' . $recentSessionMessageCount . ',"totalEmotes":' . $numEmotes . ',"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>