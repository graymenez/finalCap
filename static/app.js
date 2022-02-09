
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(geoSuccess, geoError);
    } else {
        alert("Geolocation is not supported by this browser")
    }
}




function geoSuccess(position) {
    let coords = []
    var lat = position.coords.latitude;
    var lng = position.coords.longitude;
    coords.push(lng)
    coords.push(lat)

    document.getElementById('coords').value = coords
    console.log(coords)
}

function geoError() {
    alert("Geocoder failed.");
}

