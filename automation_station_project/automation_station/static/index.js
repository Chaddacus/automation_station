



console.log('index.js');

// Import Sortable module
function closeAlertTimer() {
    setTimeout(function() {
        document.getElementById('alert').classList.add('slide-out');
    }, 5000);
}

function closeAlert() {
    var alert = document.getElementById('alert');
    alert.style.display = 'none';
}



fetch('static/tooltip.json')
    .then(response => response.json())
    .then(data => {
        for (let key in data) {
            let el = document.querySelector(`#${key}`);
            if (el) {
                el.setAttribute('data-tooltip', data[key]);
            }
        }
    });