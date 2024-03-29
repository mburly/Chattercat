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
    if(isset($_COOKIE["cc_admin_token"])) {
        $token = $_COOKIE["cc_admin_token"];
        $sql = 'SELECT * FROM Adminsessions WHERE Token = "' . $token . '";';
        $result = $conn->query($sql);
        if($result->num_rows > 0) {
            $expires = strtotime($result->fetch_assoc()["Expires"]);
            if($expires - time() < 0) {
                returnWithError("token expired");
                return;
            }
        }
    }
    else {
        returnWithError("invalid token");
        return;
    }
    $db = 'cc_' . $_POST["channel"];
    $conn = new mysqli($host, $user, $password, $db); 
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        $sql = 'SELECT * FROM Emotes ORDER BY Count DESC;';
        $result = $conn->query($sql);
        if($result->num_rows > 0) {
            $codes = '';
            $counts = '';
            $emote_ids = '';
            $urls = '';
            $paths = '';
            $dates = '';
            $sources = '';
            $active = '';
            while($emote = $result->fetch_assoc()) {
                $codes .= '"' . addcslashes($emote["Code"], '"\\/') . '",';
                $counts .= $emote["Count"] . ',';
                $emote_ids .= '"' . addcslashes($emote["EmoteID"], '"\\/') . '",';
                $urls .= '"' . $emote["URL"] . '",';
                $paths .= '"' . $emote["Path"] . '",';
                $dates .= '"' . $emote["Added"] . '",';
                $sources .= $emote["Source"] . ',';
                $active .= $emote["Active"] . ',';
            }
            $codes = substr($codes, 0, -1);
            $counts = substr($counts, 0, -1);
            $emote_ids = substr($emote_ids, 0, -1);
            $urls = substr($urls, 0, -1);
            $paths = substr($paths, 0, -1);
            $dates = substr($dates, 0, -1);
            $sources = substr($sources, 0, -1);
            $active = substr($active, 0, -1);
            returnInfo($codes,$counts,$emote_ids,$urls,$paths,$dates,$sources,$active);
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
    
    
    function returnInfo($codes,$counts,$emote_ids,$urls,$paths,$dates,$sources,$active)
    {
        $retVal = '{';
        $retVal .= '"codes":[' . $codes . '],';
        $retVal .= '"counts":[' . $counts . '],';
        $retVal .= '"emote_ids":[' . $emote_ids . '],';
        $retVal .= '"urls":[' . $urls . '],';
        $retVal .= '"paths":[' . $paths . '],';
        $retVal .= '"dates":[' . $dates . '],';
        $retVal .= '"sources":[' . $sources . '],';
        $retVal .= '"active":[' . $active . '],';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>