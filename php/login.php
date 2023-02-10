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
        $username = preg_replace( "/\r|\n/", "", $in["username"] );
        $password = preg_replace( "/\r|\n/", "", md5($in["password"]));
        $sql = 'SELECT id FROM admins WHERE username = "' . $username . '" AND password = "' . $password . '";';
        $result = $conn->query($sql);
        if($result->num_rows > 0) {
            if(!isset($_COOKIE["cc_admin_token"])) {
                $id = $result->fetch_assoc()["id"];
                $token = md5(getRandomWord());
                $sql = 'INSERT INTO adminsessions (token, userId, datetime, expires) VALUES ("' . $token . '","' . $id . '",NOW(),DATE_ADD(NOW(), INTERVAL 1 DAY));';
                $conn->query($sql);
                setcookie("cc_admin_token", $token, time() + (86400 * 30), "/"); // 86400 = 1 day
                returnInfo("success");
            }
            else {
                returnInfo("success");  // cookie is validated in validate.php
            }
        }
        else
        {
            returnWithError("invalid login");
        }
    }

    function getRandomWord($len = 10) {
        $word = array_merge(range('a', 'z'), range('A', 'Z'));
        shuffle($word);
        return substr(implode($word), 0, $len);
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
    
    function returnInfo($status)
    {
        $retVal = '{"status":"' . $status . '",';
        $retVal .= '"error":""}';
        sendResultInfoAsJson($retVal);
    }

?>