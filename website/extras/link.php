<?php

// Great code by Little_G from http://www.webmasterworld.com/php/3681920.htm
function follow_redirect($url){
    $redirect_url = null;
    
    if(function_exists("curl_init")){
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_HEADER, true);
        curl_setopt($ch, CURLOPT_NOBODY, true);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $response = curl_exec($ch);
        curl_close($ch);
    } else {
        $url_parts = parse_url($url);
        $sock = fsockopen($url_parts['host'], (isset($url_parts['port']) ? (int)$url_parts['port'] : 80));
        $request = "HEAD " . $url_parts['path'] . (isset($url_parts['query']) ? '?'.$url_parts['query'] : '') . " HTTP/1.1\r\n";
        $request .= 'Host: ' . $url_parts['host'] . "\r\n";
        $request .= "Connection: Close\r\n\r\n";
        fwrite($sock, $request);
        $response = fread($sock, 2048);
        fclose($sock);
    }

    $header = "Location: ";
    $pos = strpos($response, $header);
    if($pos === false) {
        return false;
    } else {
        $pos += strlen($header);
        $redirect_url = substr($response, $pos, strpos($response, "\r\n", $pos)-$pos);
        return $redirect_url;
    }
}

// Where to go
$url = 'http://sourceforge.net/p/nestededitor/code/';

// Get redirect
while(($newurl = follow_redirect($url)) !== false) {
    $url = $newurl;
}

// Append argument if required
if($_GET['link']) {
    $url = $url . $_GET['link'];
}

// Redirect
header('Location: ' . $url);
exit;
?>
