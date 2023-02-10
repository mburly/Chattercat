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
    $conn = new mysqli($host, $user, $password, "cc_housekeeping");
    if($conn->connect_error) {
        returnWithError($conn->connect_error);
    }
    else {
        if(isset($_COOKIE["cc_admin_token"])) {
            $token = $_COOKIE["cc_admin_token"];
            $sql = 'SELECT * FROM adminsessions WHERE token = "' . $token . '";';
            $result = $conn->query($sql);
            if($result->num_rows > 0) {
                $expires = strtotime($result->fetch_assoc()["expires"]);
                if($expires - time() > 0) {
                    returnWithInfo("Success");
                }
                else {
                    returnWithError("token expired");
                }
            }
        }
        else {
            returnWithError("invalid token");
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
        $retVal = '{"results":"' . $items . '","error":""}';
        sendResultInfoAsJson($retVal);
    }
    
    function returnInfo($val)
    {
        $retVal = '{"id":' . $val . ',';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>