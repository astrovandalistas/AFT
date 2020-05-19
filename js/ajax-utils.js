function ajaxGet(url, callback) {
  if (!url) return;
  var xmlhttp = new XMLHttpRequest();

  xmlhttp.onreadystatechange = function() {
    if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
      if (xmlhttp.status == 200) {
        callback(xmlhttp.responseText);
      } else {
        console.log('something else other than 200 was returned');
      }
    }
  };

  xmlhttp.open("GET", url);
  xmlhttp.send();
}
