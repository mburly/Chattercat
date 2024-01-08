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
        $sql = "SELECT Code, Count, Path, Source FROM TopEmotesView";
        $result = $conn->query($sql);
        $topEmoteCodes = '';
        $topEmoteCounts = '';
        $topEmotePaths = '';
        $topEmoteSources = '';
        while($emote = $result -> fetch_assoc()) {
            $topEmoteCodes .=  '"' . addcslashes($emote["Code"], '"\\/'). '", ';
            $topEmoteCounts .=  '' . $emote["Count"] . ', ';
            $topEmotePaths .= '"' . $emote["Path"] . '", ';
            $topEmoteSources .= '' . $emote["Source"] . ', ';
        }
        $topEmoteCodes = substr($topEmoteCodes, 0, -2);
        $topEmoteCounts = substr($topEmoteCounts, 0, -2);
        $topEmotePaths = substr($topEmotePaths, 0, -2);
        $topEmoteSources = substr($topEmoteSources, 0, -2);

        $sql = "SELECT COUNT(EmoteID) AS num_emotes FROM Emotes;";
        $result = $conn->query($sql);
        $numEmotes = $result->fetch_assoc()["num_emotes"];

        $sql = "SELECT Username, MessageCount FROM TopChattersView;";
        $result = $conn->query($sql);
        $topChatterNames = '';
        $topChatterCounts = '';
        while($top_chatter = $result -> fetch_assoc()) {
            $topChatterNames .=  '"' . $top_chatter["Username"] . '", ';
            $topChatterCounts .= '' . $top_chatter["MessageCount"] . ', ';
        }
        $topChatterNames = substr($topChatterNames, 0, -2);
        $topChatterCounts = substr($topChatterCounts, 0, -2);

        $sql = "SELECT COUNT(ChatterID) AS num_chatters FROM Chatters;";
        $result = $conn->query($sql);
        $numChatters = $result->fetch_assoc()["num_chatters"];

        $sql = "SELECT Username FROM RecentChattersView;";
        $result = $conn->query($sql);
        $recentChatterNames = '';
        while($recent_chatter = $result -> fetch_assoc()) {
            $recentChatterNames .=  '"' . $recent_chatter["Username"] . '", ';
        }
        $recentChatterNames = substr($recentChatterNames, 0, -2);

        $sql = "SELECT COUNT(MessageID) AS recent_session_count FROM Messages WHERE SessionID = (SELECT MAX(SessionID) FROM Sessions);";
        $result = $conn->query($sql);
        $recentSessionMessageCount = $result->fetch_assoc()["recent_session_count"];

        $sql = "SELECT COUNT(MessageID) AS num_messages FROM Messages;";
        $result = $conn->query($sql);
        $numMessages = $result->fetch_assoc()["num_messages"];

        $allEmotes = array();
        $allPaths = array();
        $sql = "SELECT Code, Path FROM Emotes WHERE Active = 1;";
        $result = $conn->query($sql);
        while($emote = $result->fetch_assoc()) {
            array_push($allEmotes, $emote["Code"]);
            array_push($allPaths, $emote["Path"]);
        }

        $sql = "SELECT Username, Message, Timestamp FROM RecentMessagesView;";
        $result = $conn->query($sql);
        $recentMessageNames = '';
        $recentMessageMessages = '';
        $recentMessageDatetimes = '';
        $seenWords = array();
        while($recent_chat = $result -> fetch_assoc()) {
            $message = $recent_chat["Message"];
            $words = explode(" ", $message);
            foreach($words as $word) {
                $i = array_search($word, $allEmotes);
                if(gettype($i) == 'integer' && !in_array($word, $seenWords)) {
                    $reg = '/\b' . preg_quote($word, '/') . '\b/';
                    $message = preg_replace($reg, '<div class="tooltip-top"><img class="emote" src="' . $allPaths[$i] . '" onerror="placeholder(this)" title="' . $allEmotes[$i] . '"><span class="tooltiptext"><img class="emote-tooltip" id="' . $allEmotes[$i] . '-tooltip" src="' . $allPaths[$i] . '"></span></div>', $message);
                    if($message == $recent_chat["Message"]) {
                        $message = str_replace($word, '<div class="tooltip-top"><img class="emote" src="' . $allPaths[$i] . '" onerror="placeholder(this)" title="' . $allEmotes[$i] . '"><span class="tooltiptext"><img class="emote-tooltip" id="' . $allEmotes[$i] . '-tooltip" src="' . $allPaths[$i] . '"></span></div>', $message);
                    }
                    array_push($seenWords, $word);
                }
            }
            $recentMessageNames .=  '"' . $recent_chat["Username"] . '", ';
            $recentMessageMessages .=  '"' . addcslashes(removeUnicode($message), '"\\/') . '", ';
            $recentMessageDatetimes .=  '"' . $recent_chat["Timestamp"] . '", ';
            $seenWords = array();
        }
        $recentMessageNames = substr($recentMessageNames, 0, -2);
        $recentMessageMessages = substr($recentMessageMessages, 0, -2);
        $recentMessageDatetimes = substr($recentMessageDatetimes, 0, -2);
        
        $sql = "SELECT Start, Length FROM Sessions ORDER BY SessionID DESC LIMIT 5;";
        $result = $conn->query($sql);
        $recentSessionStartDatetimes = '';
        $recentSessionLengths = '';
        while($recentSession = $result -> fetch_assoc()) {
            if($recentSession["Length"] == null)
            {
                $length = "null";
            }
            else
            {
                $length = $recentSession["Length"];
            }
            $recentSessionStartDatetimes .=  '"' . $recentSession["Start"] . '", ';
            $recentSessionLengths .=  '"' . $length . '", ';
        }
        $recentSessionStartDatetimes = substr($recentSessionStartDatetimes, 0, -2);
        $recentSessionLengths = substr($recentSessionLengths, 0, -2);

        $sql = "SELECT Name, Length, Title, SessionID FROM RecentSegmentsView;";
        $result = $conn->query($sql);
        $recentSegmentCategories = '';
        $recentSegmentLengths = '';
        $recentSegmentTitles = '';
        $recentSegmentSessions = '';
        while($recentSegment = $result -> fetch_assoc()) {
            $recentSegmentCategories .=  '"' . $recentSegment["Name"] . '", ';
            $recentSegmentLengths .=  '"' . $recentSegment["Length"] . '", ';
            $recentSegmentTitles .=  '"' . addcslashes($recentSegment["Title"], '"\\/') . '", ';
            $recentSegmentSessions .=  '' . $recentSegment["SessionID"] . ', ';
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