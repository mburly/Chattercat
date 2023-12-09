<?php
    ini_set('display_errors', 1);
    set_time_limit(0);
    ignore_user_abort(1);
    ob_start();
    if(!isset($_COOKIE["cc_admin_token"])) {
        returnWithError("no token");
    }
    else {
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
        $conn = new mysqli($host, $user, $password, "cc_housekeeping");
        if($conn->connect_error) {
            returnWithError($conn->connect_error);
        }
        else {

            $sql = 'SELECT a.username as username FROM admins a INNER JOIN adminsessions ads ON a.id=ads.userId WHERE token = "' . $_COOKIE["cc_admin_token"] . '";';
	    $result = $conn->query($sql);
            $username = "";
            if($result->num_rows > 0) {
                $username = $result->fetch_assoc()["username"];
                $channels = getChannels($conn);
                $numChannels = count($channels);
                $executing = 0;
                $executeStart = null;
                $numChannelsOnline = 0;
                $numMessages = 0;
                $sql = 'SELECT * FROM executions ORDER BY id DESC LIMIT 1;';
                $result = $conn->query($sql);
                if($result->num_rows > 0) {
                    while($row = $result->fetch_assoc()) {
                        if($row["end"] == null) {
                            $executing = 1;
                            $executeStart = $row["start"];
                        }
                    }
                    foreach($channels as $channel) {
                        $conn2 = new mysqli($host, $user, $password, $channel);
                        if($conn2->connect_error) {
                            returnWithError($conn->connect_error);
                        }
                        else {
                            $sql = 'SELECT COUNT(id) as num_messages FROM messages;';
                            $result = $conn2->query($sql);
                            $count = $result->fetch_assoc()["num_messages"];
                            if($count != null) {
                                $numMessages = $numMessages + $count;
                            }
    
                            $sql = 'SELECT end_datetime FROM sessions ORDER BY id DESC LIMIT 1;';
                            $result = $conn2->query($sql);
                            $count = $result->fetch_assoc()["end_datetime"];
                            if($count == null) {
                                $numChannelsOnline = $numChannelsOnline + 1;
                            }
    
                        }
                    }    
                }
                $cwd = getcwd();
                $dir = explode("php", $cwd)[0] . "emotes";
                $dirs = array();
                array_push($dirs, $dir . "/twitch");
                array_push($dirs, $dir . "/bttv");
                array_push($dirs, $dir . "/ffz");
                $numEmotes = 0;
                $numTwitchEmotes = 0;
                $numBTTVEmotes = 0;
                $numFFZEmotes = 0;
                $counter = 0;
                foreach($dirs as $dir) {
                    $fi = new FilesystemIterator($dir);
                    $numEmotes = $numEmotes + iterator_count($fi);
                    if($counter == 0) {
                        $numTwitchEmotes = iterator_count($fi);
                    }
                    else if($counter == 1) {
                        $numBTTVEmotes = iterator_count($fi);
                    }
                    else if($counter == 2) {
                        $numFFZEmotes = iterator_count($fi);
                    }
                    $counter = $counter + 1;
                }
                returnInfo($username, $executing, $executeStart, $numChannels, $numMessages, $numEmotes, $numTwitchEmotes, $numBTTVEmotes, $numFFZEmotes, $numChannelsOnline);
            }
            else {
                returnWithError("no admin credentials");
            }
        }
    }

    function getChannels($conn)
    {
        $sql = "SHOW DATABASES;";
        $result = $conn->query($sql);
        $channels = array();
        $channelNames = '';
        while($db = $result -> fetch_assoc()) {
            if(strpos($db["Database"], "cc_") !== false && strpos($db["Database"], "housekeeping") == false)
            {
                array_push($channels, $db["Database"]);
            }
        }
        return $channels;
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
    
    function returnInfo($username, $executing, $executeStart, $numChannels, $numMessages, $numEmotes, $numTwitchEmotes, $numBTTVEmotes, $numFFZEmotes, $numChannelsOnline)
    {
        $retVal = '{"username":"' . $username . '","executing":' . $executing . 
        ',"executeStart":"' . $executeStart . '","numChannels":' . $numChannels . 
        ',"numMessages":' . $numMessages . ',"numEmotes":' . $numEmotes . ',"numTwitchEmotes":' . $numTwitchEmotes . ',"numBTTVEmotes":' . $numBTTVEmotes . ',"numFFZEmotes":' . $numFFZEmotes . ',"numChannelsOnline":' . $numChannelsOnline . ',';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>