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
    $conn = new mysqli($host, $user, $password); 
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
        return;
    }
    else {
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
        $sql = 'SHOW DATABASES;';
        $result = $conn->query($sql);
        echo var_dump($result) . '<br>';
        while($db = $result->fetch_assoc()) {
            $dbname = $db["Database"];
            if(strpos($dbname, 'cc_') !== false) {
                if(strpos($dbname, 'housekeeping') == false) {
                    $sql = "DROP DATABASE $dbname;";
                    $dropResult = $conn->query($sql);
                }
            }
        }
        $sql = 'TRUNCATE TABLE cc_housekeeping.Pictures;';
        $result = $conn->query($sql);
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